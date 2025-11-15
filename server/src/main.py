from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import asyncio
import base64
import sys
import os
import httpx

# Add current directory to path for imports
sys.path.insert(0, os.getcwd())

try:
    from config.Config import CONFIG
    from service.llm_client import create_llm_client
    from service.whisper_service import create_whisper_transcriber
    from service.calendar_service import CalendarService
    from service.project_service import ProjectService
    from service.document_parser import DocumentTextExtractor
    from tools.agent_tools import CalendarTool, WebSearchTool, ReActAgent

    # Initialize LLM client from config
    llm_client = create_llm_client(
        base_url=CONFIG.llm.url,
        api_key=CONFIG.llm.token,
        model=CONFIG.llm.model
    )
    print(f"✓ LLM Client initialized successfully")
    print(f"  Model: {CONFIG.llm.model}")
    print(f"  Base URL: {CONFIG.llm.url}")

    # Initialize Whisper transcriber from config
    whisper_transcriber = create_whisper_transcriber(
        api_key=CONFIG.transcribe.token,
        base_url=CONFIG.transcribe.url
    )
    print(f"✓ Whisper Transcriber initialized successfully")
    print(f"  Model: {CONFIG.transcribe.model}")
    print(f"  URL: {CONFIG.transcribe.url}")

    # Initialize Calendar Service
    calendar_service = CalendarService(storage_dir="calendar_storage")
    print(f"✓ Calendar Service initialized successfully")

    # Initialize Project Service
    project_service = ProjectService(storage_dir="project_storage")
    print(f"✓ Project Service initialized successfully")

    # Initialize Document Text Extractor
    document_extractor = DocumentTextExtractor()
    print(f"✓ Document Text Extractor initialized successfully")

except Exception as e:
    print(f"✗ Error loading config or initializing services:")
    print(f"  {e}")
    import traceback
    traceback.print_exc()
    # Fallback to dummy clients for testing
    llm_client = None
    whisper_transcriber = None
    calendar_service = None
    project_service = None
    document_extractor = None

app = FastAPI(title="Student Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class User(BaseModel):
    id: str
    name: str
    email: str
    avatar_url: Optional[str] = None

class Task(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    date: str
    time: str

class Project(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: Optional[str] = None

class Chat(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: str
    updated_at: Optional[str] = None

class Message(BaseModel):
    id: str
    chat_id: str
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: str

class ChatNode(BaseModel):
    id: str
    label: str
    type: str

class ChatEdge(BaseModel):
    source: str
    target: str
    label: str

class ChatGraph(BaseModel):
    nodes: List[ChatNode]
    edges: List[ChatEdge]

class Document(BaseModel):
    id: str
    project_id: str
    filename: str
    file_size: int
    uploaded_at: str
    uploaded_by_user: str

class CreateProjectRequest(BaseModel):
    name: str

class CreateChatRequest(BaseModel):
    project_id: str
    name: str

class CreateMessageRequest(BaseModel):
    content: str
    role: str = "user"

# ==================== MOCK DATA ====================

mock_user = User(
    id="user-1",
    name="Иван Иванов",
    email="ivan@example.com",
    avatar_url=None
)

mock_tasks = [
    Task(
        id="task-1",
        title="AB@5G0 A :><0=4>9",
        description="1AC645=85 ?@>5:B0",
        date=datetime.now().strftime("%Y-%m-%d"),
        time="10:00"
    ),
    Task(
        id="task-2",
        title="!40G0 ;01>@0B>@=>9",
        description="> <0B5<0B8G5A:><C 0=0;87C",
        date="2025-11-15",
        time="14:00"
    ),
    Task(
        id="task-3",
        title=">=AC;LB0F8O",
        description="> :C@A>2>9 @01>B5",
        date="2025-11-16",
        time="16:30"
    )
]

mock_projects = [
    Project(id="proj-1", name="(03><5@ =0 ", created_at="2025-11-01T10:00:00Z"),
    Project(id="proj-2", name="Web ?@8;>65=85", created_at="2025-11-05T14:30:00Z"),
]

mock_chats = [
    Chat(id="chat-1", project_id="proj-1", name="1I55 >1AC645=85", created_at="2025-11-01T10:30:00Z"),
    Chat(id="chat-2", project_id="proj-1", name="0B5<0B8G5A:89 0=0;87", created_at="2025-11-02T09:00:00Z"),
    Chat(id="chat-3", project_id="proj-2", name="Frontend @07@01>B:0", created_at="2025-11-05T15:00:00Z"),
]

mock_messages = {
    "chat-1": [
        Message(id="msg-1", chat_id="chat-1", content="@825B! ><>38 A ?@>5:B><", role="user", timestamp="2025-11-01T10:31:00Z"),
        Message(id="msg-2", chat_id="chat-1", content="4@02AB2C9B5! >=5G=>, G5< <>3C ?><>GL?", role="assistant", timestamp="2025-11-01T10:31:05Z"),
    ],
    "chat-2": [
        Message(id="msg-3", chat_id="chat-2", content="1JOA=8 ?@>872>4=K5", role="user", timestamp="2025-11-02T09:01:00Z"),
    ],
}

mock_graph = ChatGraph(
    nodes=[
        ChatNode(id="chat-1", label="1I55 >1AC645=85", type="chat"),
        ChatNode(id="chat-2", label="0B5<0B8G5A:89 0=0;87", type="chat"),
        ChatNode(id="chat-3", label="Frontend", type="chat"),
        ChatNode(id="topic-1", label="@>872>4=K5", type="topic"),
        ChatNode(id="topic-2", label="Vue.js", type="topic"),
    ],
    edges=[
        ChatEdge(source="chat-1", target="chat-2", label="A2O70="),
        ChatEdge(source="chat-2", target="topic-1", label=">1AC6405B"),
        ChatEdge(source="chat-3", target="topic-2", label=">1AC6405B"),
    ]
)

# Mock documents storage
mock_documents = {}

# ==================== USER ENDPOINTS ====================

@app.get("/api/user/me", response_model=User)
async def get_current_user():
    """Get current user information"""
    return mock_user

@app.patch("/api/user/me", response_model=User)
async def update_user(name: Optional[str] = None, email: Optional[str] = None):
    """Update user profile"""
    if name:
        mock_user.name = name
    if email:
        mock_user.email = email
    return mock_user

@app.post("/api/user/avatar")
async def upload_avatar(file: UploadFile = File(...)):
    """Upload user avatar"""
    contents = await file.read()

    mime_type = file.content_type or "image/png"
    base64_data = base64.b64encode(contents).decode()
    mock_user.avatar_url = f"data:{mime_type};base64,{base64_data}"

    return {"url": mock_user.avatar_url}

# ==================== TRANSCRIPTION ====================

class TranscriptionRequest(BaseModel):
    language: str = "ru"
    temperature: float = 0.0

@app.post("/api/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "ru",
    temperature: float = 0.0
):
    """
    Transcribe audio to text using Whisper API

    Args:
        audio: Audio file (MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM)
        language: Language code (ru, en, etc.)
        temperature: Sampling temperature (0-1)

    Returns:
        JSON with transcribed text and metadata
    """
    try:
        # Validate audio file
        if not audio:
            raise HTTPException(status_code=400, detail="No audio file provided")

        if not audio.filename:
            raise HTTPException(status_code=400, detail="Audio file must have a filename")

        # Read audio file
        audio_content = await audio.read()

        if not audio_content:
            raise HTTPException(status_code=400, detail="Audio file is empty")

        # Check file size (max 25MB for Whisper API)
        if len(audio_content) > 25 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Audio file is too large (max 25MB)")

        print(f"Transcribing audio: {audio.filename}, size: {len(audio_content)} bytes, language: {language}")

        # Check if whisper transcriber is initialized
        if whisper_transcriber is None:
            raise HTTPException(status_code=503, detail="Whisper service not initialized")

        # Transcribe using Whisper service
        result = await whisper_transcriber.transcribe(
            audio_data=audio_content,
            filename=audio.filename,
            language=language,
            temperature=0.0
        )

        if result["success"]:
            print(f"✓ Transcription successful: {result['text']}")
            return {
                "success": True,
                "text": result["text"],
                "language": result["language"],
                "model": result["model"],
            }
        else:
            print(f"✗ Transcription failed: {result.get('error')}")
            return {
                "success": False,
                "text": "",
                "error": result.get("error", "Unknown error"),
                "model": result["model"],
            }

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        print(f"✗ Transcription error: {error_message}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Transcription failed: {error_message}")

# ==================== TASKS ENDPOINTS ====================

@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    """Get all tasks"""
    return mock_tasks

@app.get("/api/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    """Get task by ID"""
    task = next((t for t in mock_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.post("/api/tasks", response_model=Task)
async def create_task(task: Task):
    """Create new task"""
    # Generate ID if not provided
    if not task.id:
        task.id = f"task-{len(mock_tasks) + 1}"
    mock_tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_update: Task):
    """Update existing task"""
    task = next((t for t in mock_tasks if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update task fields
    task.title = task_update.title
    task.description = task_update.description
    task.date = task_update.date
    task.time = task_update.time
    return task

@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete task"""
    global mock_tasks
    mock_tasks = [t for t in mock_tasks if t.id != task_id]
    return {"success": True}

# ==================== CALENDAR STATE ENDPOINTS ====================

from service.calendar_service import CalendarState, CalendarTask as CalendarTaskModel

@app.get("/api/calendar/state/{user_id}/{year}/{month}", response_model=CalendarState)
async def get_calendar_state(user_id: str, year: int, month: int):
    """
    Get calendar state for a specific month

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        CalendarState object with all tasks for that month
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    state = calendar_service.get_or_create_state(user_id, year, month)
    return state


@app.get("/api/calendar/tasks/{user_id}/{year}/{month}", response_model=List[CalendarTaskModel])
async def get_calendar_tasks(user_id: str, year: int, month: int):
    """
    Get all tasks for a specific month

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        List of CalendarTask objects
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    tasks = calendar_service.get_all_tasks_in_month(user_id, year, month)
    return tasks


@app.get("/api/calendar/all-tasks/{user_id}", response_model=List[CalendarTaskModel])
async def get_all_calendar_tasks(user_id: str):
    """
    Get all tasks for a user across all months

    Args:
        user_id: User ID

    Returns:
        List of all CalendarTask objects for the user
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    tasks = calendar_service.get_all_tasks_for_user(user_id)
    return tasks


@app.post("/api/calendar/task/{user_id}/{year}/{month}", response_model=CalendarTaskModel)
async def create_calendar_task(
    user_id: str,
    year: int,
    month: int,
    task: CalendarTaskModel
):
    """
    Create a new task in calendar state

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)
        task: CalendarTask object with title, description, date, time, and id

    Returns:
        Created CalendarTask object
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    if not task.id:
        raise HTTPException(status_code=400, detail="Task must have an id")

    created_task = calendar_service.create_task(user_id, year, month, task)
    return created_task


@app.get("/api/calendar/task/{user_id}/{year}/{month}/{task_id}", response_model=CalendarTaskModel)
async def get_calendar_task(user_id: str, year: int, month: int, task_id: str):
    """
    Get a specific task from calendar state

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)
        task_id: Task ID

    Returns:
        CalendarTask object or 404 if not found
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    task = calendar_service.get_task(user_id, year, month, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@app.patch("/api/calendar/task/{user_id}/{year}/{month}/{task_id}", response_model=CalendarTaskModel)
async def update_calendar_task(
    user_id: str,
    year: int,
    month: int,
    task_id: str,
    task_update: CalendarTaskModel
):
    """
    Update an existing task in calendar state

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)
        task_id: Task ID
        task_update: Updated CalendarTask object

    Returns:
        Updated CalendarTask object or 404 if not found
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    updated_task = calendar_service.update_task(user_id, year, month, task_id, task_update)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated_task


@app.delete("/api/calendar/task/{user_id}/{year}/{month}/{task_id}")
async def delete_calendar_task(user_id: str, year: int, month: int, task_id: str):
    """
    Delete a task from calendar state

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)
        task_id: Task ID

    Returns:
        Success message or 404 if not found
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    deleted = calendar_service.delete_task(user_id, year, month, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"success": True, "message": "Task deleted successfully"}


@app.delete("/api/calendar/state/{user_id}/{year}/{month}")
async def delete_calendar_state(user_id: str, year: int, month: int):
    """
    Delete entire calendar state for a month

    Args:
        user_id: User ID
        year: Year (e.g., 2025)
        month: Month (1-12)

    Returns:
        Success message or 404 if not found
    """
    if calendar_service is None:
        raise HTTPException(status_code=503, detail="Calendar service not initialized")

    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12")

    deleted = calendar_service.delete_state(user_id, year, month)
    if not deleted:
        raise HTTPException(status_code=404, detail="Calendar state not found")

    return {"success": True, "message": "Calendar state deleted successfully"}

# ==================== PROJECTS ENDPOINTS ====================

@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    """Get all projects"""
    if project_service is None:
        print(f"DEBUG: get_projects - returning mock_projects ({len(mock_projects)} projects)")
        return mock_projects
    projects = project_service.get_all_projects()
    print(f"DEBUG: get_projects - returning {len(projects)} projects from project_service")
    return projects

@app.post("/api/projects", response_model=Project)
async def create_project(request: CreateProjectRequest):
    """Create new project"""
    print(f"DEBUG: Creating project with name={request.name}")

    if project_service is None:
        print(f"WARNING: project_service is None, using mock data")
        project = Project(
            id=f"proj-{len(mock_projects) + 1}",
            name=request.name,
            created_at=datetime.now().isoformat()
        )
        mock_projects.append(project)
        print(f"DEBUG: Created mock project: {project.id}")
        return project

    print(f"DEBUG: Using project_service.create_project()")
    project = project_service.create_project(request.name)
    print(f"DEBUG: Created project: {project.id}")
    return project

# ==================== CHATS ENDPOINTS ====================

@app.get("/api/chats", response_model=List[Chat])
async def get_chats(project_id: Optional[str] = None):
    """Get all chats, optionally filtered by project"""
    print(f"DEBUG: get_chats called with project_id={project_id}")

    if project_service is None:
        print(f"DEBUG: get_chats - using mock_chats")
        if project_id:
            result = [c for c in mock_chats if c.project_id == project_id]
            print(f"DEBUG: get_chats - found {len(result)} chats for project {project_id}")
            return result
        print(f"DEBUG: get_chats - returning all {len(mock_chats)} mock chats")
        return mock_chats

    if project_id:
        print(f"DEBUG: get_chats - using project_service.get_project_chats({project_id})")
        chats = project_service.get_project_chats(project_id)
    else:
        # Get all chats from all projects
        print(f"DEBUG: get_chats - getting all chats from project_service")
        chats = list(project_service.chats.values())

    print(f"DEBUG: get_chats - returning {len(chats)} chats")
    return chats

@app.post("/api/chats", response_model=Chat)
async def create_chat(request: CreateChatRequest):
    """Create new chat"""
    print(f"DEBUG: Creating chat with project_id={request.project_id}, name={request.name}")

    if project_service is None:
        print(f"WARNING: project_service is None, using mock data")
        chat = Chat(
            id=f"chat-{len(mock_chats) + 1}",
            project_id=request.project_id,
            name=request.name,
            created_at=datetime.now().isoformat()
        )
        mock_chats.append(chat)
        mock_messages[chat.id] = []
        print(f"DEBUG: Created mock chat: {chat.id}")
        return chat

    print(f"DEBUG: Using project_service.create_chat()")
    chat = project_service.create_chat(request.project_id, request.name)
    if chat is None:
        print(f"ERROR: Project not found: {request.project_id}")
        raise HTTPException(status_code=404, detail="Project not found")
    print(f"DEBUG: Created chat: {chat.id}")
    return chat

@app.get("/api/chats/graph", response_model=ChatGraph)
async def get_chat_graph():
    """Get chat graph data"""
    return mock_graph

# ==================== MESSAGES ENDPOINTS ====================

@app.get("/api/chats/{chat_id}/messages", response_model=List[Message])
async def get_messages(chat_id: str):
    """Get all messages in a chat"""
    if project_service is None:
        return mock_messages.get(chat_id, [])
    return project_service.get_chat_messages(chat_id)

@app.post("/api/chats/{chat_id}/messages", response_model=Message)
async def create_message(chat_id: str, request: CreateMessageRequest):
    """Create a new message"""
    print(f"DEBUG: Creating message in chat {chat_id}")

    if project_service is None:
        print(f"DEBUG: Using mock_messages")
        if chat_id not in mock_messages:
            mock_messages[chat_id] = []

        message = Message(
            id=f"msg-{len(mock_messages[chat_id]) + 1}",
            chat_id=chat_id,
            content=request.content,
            role=request.role,
            timestamp=datetime.now().isoformat()
        )
        mock_messages[chat_id].append(message)
        return message

    print(f"DEBUG: Using project_service.add_message()")
    message = project_service.add_message(chat_id, request.content, request.role)
    if message is None:
        print(f"ERROR: Chat not found: {chat_id}")
        raise HTTPException(status_code=404, detail="Chat not found")
    return message

# ==================== WEBSOCKET FOR CHAT STREAMING ====================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws/chat/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: str):
    """WebSocket endpoint for streaming chat responses with LLM"""
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_content = message_data.get("content", "")

            # Save user message
            if project_service is None:
                user_message = Message(
                    id=f"msg-{datetime.now().timestamp()}",
                    chat_id=chat_id,
                    content=user_content,
                    role="user",
                    timestamp=datetime.now().isoformat()
                )
                if chat_id not in mock_messages:
                    mock_messages[chat_id] = []
                mock_messages[chat_id].append(user_message)
                chat_messages = mock_messages[chat_id]
            else:
                user_message = project_service.add_message(chat_id, user_content, "user")
                if user_message is None:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Chat not found"
                    }))
                    return
                chat_messages = project_service.get_chat_messages(chat_id)

            # Send user message confirmation
            await websocket.send_text(json.dumps({
                "type": "user_message",
                "message": user_message.model_dump()
            }))

            rag_context = ""
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    rag_response = await client.get(
                        "http://147.45.224.7:6500/api/get_answer",
                        params={"user_question": user_content}
                    )
                    if rag_response.status_code == 200:
                        rag_data = rag_response.json()
                        rag_answer = rag_data.get("answer", "")
                        if rag_answer:
                            rag_context = f"\n\nИнформация из базы знаний: {rag_answer}"
                            print(f"✓ RAG context added: {rag_answer[:100]}...")
            except Exception as e:
                print(f"⚠ RAG request failed: {e}")

            # Build conversation history (last 10 messages)
            system_prompt = f"""Ты полезный ассистент для студентов. Помогаешь с учебой, отвечаешь на вопросы и даешь советы.

current_time: {datetime.now().strftime("%d,%m,%y %H:%M:%S")}

Ты имеешь доступ к инструментам для поиска информации:
- КАЛЕНДАРЬ: для работы с датами, планированием, графиками
- WEB SEARCH: для поиска актуальной информации в интернете

Инструкции по использованию инструментов:
1. Если пользователь спрашивает о датах/планировании → используй КАЛЕНДАРЬ
2. Если нужна актуальная информация → используй WEB SEARCH
3. После использования инструмента включи результат в ответ
4. Будь помощным и кратким в ответе

Когда у тебя достаточно информации для ответа, отправь полный ответ пользователю.

В конце обязательно вызови финальный ответ, если надо сделать какой то поиск просто сразу делай, просто после ответа вызови финальный ответ
"""

            if rag_context:
                system_prompt += rag_context

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                }
            ]
            for msg in chat_messages[-10:]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

            # Generate message ID for assistant response
            assistant_msg_id = f"msg-{datetime.now().timestamp()}"

            # Send start of assistant message
            await websocket.send_text(json.dumps({
                "type": "assistant_start",
                "message_id": assistant_msg_id
            }))

            # Use ReAct agent if available, otherwise fall back to direct LLM
            full_response = ""
            tool_calls_made = []

            try:
                if llm_client is None:
                    raise Exception("LLM Client not initialized. Check config.yml")

                # Try to use agent for tool-aware responses
                print(f"🤖 Using ReAct Agent for user message: {user_content[:50]}...")

                # Create agent instance
                agent = ReActAgent(llm_client)

                # Process message with agent
                full_response, tool_calls_made = await agent.process_message(
                    user_message=user_content,
                    chat_context=messages[1:]  # Exclude system prompt for agent context
                )

                print(f"✓ Agent completed with {len(tool_calls_made)} tool calls")

                # Stream the agent's response to client in chunks
                print(f"📤 Streaming response ({len(full_response)} chars) to client")

                # Always stream the full_response from agent (whether tools were used or not)
                if full_response:
                    chunk_size = 50
                    for i in range(0, len(full_response), chunk_size):
                        chunk = full_response[i:i+chunk_size]
                        await websocket.send_text(json.dumps({
                            "type": "assistant_chunk",
                            "content": chunk
                        }))
                        # Small delay for better streaming effect
                        await asyncio.sleep(0.01)

                    if tool_calls_made:
                        print(f"📊 Tools used: {[tc['tool'] for tc in tool_calls_made]}")
                else:
                    # If no response, something went wrong
                    print("⚠️ Agent returned empty response")
                    full_response = "Извините, не удалось обработать ваш запрос."
                    await websocket.send_text(json.dumps({
                        "type": "assistant_chunk",
                        "content": full_response
                    }))

            except Exception as e:
                print(f"Error during agent/LLM processing: {e}")
                import traceback
                traceback.print_exc()
                error_message = f"Ошибка при генерации ответа: {str(e)}"
                full_response = error_message
                await websocket.send_text(json.dumps({
                    "type": "assistant_chunk",
                    "content": error_message
                }))

            # Save assistant message
            if project_service is None:
                assistant_message = Message(
                    id=assistant_msg_id,
                    chat_id=chat_id,
                    content=full_response,
                    role="assistant",
                    timestamp=datetime.now().isoformat()
                )
                mock_messages[chat_id].append(assistant_message)
            else:
                assistant_message = project_service.add_message(chat_id, full_response, "assistant")
                if assistant_message is None:
                    # Chat doesn't exist anymore, just send the message
                    assistant_message = Message(
                        id=assistant_msg_id,
                        chat_id=chat_id,
                        content=full_response,
                        role="assistant",
                        timestamp=datetime.now().isoformat()
                    )

            # Send end of assistant message
            await websocket.send_text(json.dumps({
                "type": "assistant_end",
                "message": assistant_message.model_dump()
            }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ==================== MODEL CONFIGURATION ====================

class LLMConfigUpdate(BaseModel):
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None

@app.get("/api/config/llm")
async def get_llm_config():
    """Get current LLM configuration"""
    return {
        "base_url": llm_client.base_url,
        "model": llm_client.model,
        "api_key": llm_client.api_key[:20] + "..." if llm_client.api_key else None
    }

@app.patch("/api/config/llm")
async def update_llm_config(config: LLMConfigUpdate):
    """Update LLM configuration"""
    try:
        llm_client.update_config(
            base_url=config.base_url,
            api_key=config.api_key,
            model=config.model_name
        )
        return {
            "success": True,
            "message": "LLM configuration updated",
            "config": {
                "base_url": llm_client.base_url,
                "model": llm_client.model,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update config: {str(e)}")

# ==================== DOCUMENTS ENDPOINTS ====================

@app.post("/api/projects/{project_id}/documents", response_model=Document)
async def upload_document(
    project_id: str,
    file: UploadFile = File(...),
    user_id: str = "user-1"  # In production, get from auth token
):
    """Upload document to project"""
    try:
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Create uploads directory if it doesn't exist
        upload_dir = f"uploads/{user_id}/{project_id}"
        os.makedirs(upload_dir, exist_ok=True)

        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="File is empty")

        # Save file to disk
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create document record
        document = Document(
            id=f"doc-{datetime.now().timestamp()}",
            project_id=project_id,
            filename=file.filename,
            file_size=len(file_content),
            uploaded_at=datetime.now().isoformat(),
            uploaded_by_user=user_id
        )

        # Store in mock storage
        if project_id not in mock_documents:
            mock_documents[project_id] = []
        mock_documents[project_id].append(document)

        print(f"✓ Document uploaded: {file.filename} ({len(file_content)} bytes)")

        if document_extractor is not None:
            try:
                extracted_text = document_extractor(file_content, file.filename)
                if extracted_text and len(extracted_text.strip()) > 0:
                    print(f"📄 Extracted text from {file.filename}: {len(extracted_text)} characters")

                    async with httpx.AsyncClient(timeout=30.0) as client:
                        rag_upload_response = await client.post(
                            "http://147.45.224.7:6500/api/upload_text",
                            json={
                                "text": extracted_text,
                                "title": f"{file.filename} (Project: {project_id})"
                            }
                        )
                        if rag_upload_response.status_code == 200:
                            print(f"✓ Document text uploaded to RAG: {file.filename}")
                        else:
                            print(f"⚠ RAG upload failed with status {rag_upload_response.status_code}")
                else:
                    print(f"⚠ No text extracted from {file.filename}")
            except Exception as e:
                print(f"⚠ Failed to extract text or upload to RAG: {e}")

        return document

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        print(f"✗ Document upload error: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {error_message}")


@app.get("/api/projects/{project_id}/documents", response_model=List[Document])
async def get_project_documents(project_id: str):
    """Get all documents for a project"""
    documents = mock_documents.get(project_id, [])
    return sorted(documents, key=lambda x: x.uploaded_at, reverse=True)


@app.delete("/api/projects/{project_id}/documents/{document_id}")
async def delete_document(project_id: str, document_id: str, user_id: str = "user-1"):
    """Delete document from project"""
    try:
        if project_id not in mock_documents:
            raise HTTPException(status_code=404, detail="Project not found")

        # Find and remove document
        documents = mock_documents[project_id]
        document = next((d for d in documents if d.id == document_id), None)

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file from disk
        file_path = f"uploads/{user_id}/{project_id}/{document.filename}"
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove from mock storage
        mock_documents[project_id] = [d for d in documents if d.id != document_id]

        print(f"✓ Document deleted: {document.filename}")
        return {"success": True, "message": "Document deleted"}

    except HTTPException:
        raise
    except Exception as e:
        error_message = str(e)
        print(f"✗ Document deletion error: {error_message}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {error_message}")

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
