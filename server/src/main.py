from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import json
import asyncio
import base64
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.getcwd())

try:
    from config.Config import CONFIG
    from service.llm_client import create_llm_client
    from service.whisper_service import create_whisper_transcriber

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

except Exception as e:
    print(f"✗ Error loading config or initializing services:")
    print(f"  {e}")
    import traceback
    traceback.print_exc()
    # Fallback to dummy clients for testing
    llm_client = None
    whisper_transcriber = None

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

class Chat(BaseModel):
    id: str
    project_id: str
    name: str
    created_at: str

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

# ==================== MOCK DATA ====================

mock_user = User(
    id="user-1",
    name="20= 20=>2",
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
    # Mock: just return a fake URL
    # In production, save file and return actual URL
    contents = await file.read()
    # Simulate saving avatar
    mock_user.avatar_url = f"data:image/png;base64,{base64.b64encode(contents[:100]).decode()}"
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
            temperature=temperature
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

# ==================== PROJECTS ENDPOINTS ====================

@app.get("/api/projects", response_model=List[Project])
async def get_projects():
    """Get all projects"""
    return mock_projects

@app.post("/api/projects", response_model=Project)
async def create_project(project: Project):
    """Create new project"""
    if not project.id:
        project.id = f"proj-{len(mock_projects) + 1}"
    if not project.created_at:
        project.created_at = datetime.now().isoformat()
    mock_projects.append(project)
    return project

# ==================== CHATS ENDPOINTS ====================

@app.get("/api/chats", response_model=List[Chat])
async def get_chats(project_id: Optional[str] = None):
    """Get all chats, optionally filtered by project"""
    if project_id:
        return [c for c in mock_chats if c.project_id == project_id]
    return mock_chats

@app.post("/api/chats", response_model=Chat)
async def create_chat(chat: Chat):
    """Create new chat"""
    if not chat.id:
        chat.id = f"chat-{len(mock_chats) + 1}"
    if not chat.created_at:
        chat.created_at = datetime.now().isoformat()
    mock_chats.append(chat)
    mock_messages[chat.id] = []
    return chat

@app.get("/api/chats/graph", response_model=ChatGraph)
async def get_chat_graph():
    """Get chat graph data"""
    return mock_graph

# ==================== MESSAGES ENDPOINTS ====================

@app.get("/api/chats/{chat_id}/messages", response_model=List[Message])
async def get_messages(chat_id: str):
    """Get all messages in a chat"""
    return mock_messages.get(chat_id, [])

@app.post("/api/chats/{chat_id}/messages", response_model=Message)
async def create_message(chat_id: str, content: str, role: str = "user"):
    """Create a new message"""
    if chat_id not in mock_messages:
        mock_messages[chat_id] = []

    message = Message(
        id=f"msg-{len(mock_messages[chat_id]) + 1}",
        chat_id=chat_id,
        content=content,
        role=role,
        timestamp=datetime.now().isoformat()
    )
    mock_messages[chat_id].append(message)
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

            # Send user message confirmation
            await websocket.send_text(json.dumps({
                "type": "user_message",
                "message": user_message.dict()
            }))

            # Build conversation history (last 10 messages)
            messages = [
                {
                    "role": "system",
                    "content": "Ты полезный ассистент для студентов. Помогаешь с учебой, отвечаешь на вопросы и даешь советы."
                }
            ]
            for msg in mock_messages[chat_id][-10:]:
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

            # Stream response from LLM
            full_response = ""
            try:
                if llm_client is None:
                    raise Exception("LLM Client not initialized. Check config.yml")

                async for chunk in llm_client.chat_completion_stream(
                    messages=messages,
                    temperature=0.7
                ):
                    full_response += chunk
                    # Send chunk to client
                    await websocket.send_text(json.dumps({
                        "type": "assistant_chunk",
                        "content": chunk
                    }))
            except Exception as e:
                print(f"Error during LLM streaming: {e}")
                import traceback
                traceback.print_exc()
                error_message = f"Ошибка при генерации ответа: {str(e)}"
                full_response = error_message
                await websocket.send_text(json.dumps({
                    "type": "assistant_chunk",
                    "content": error_message
                }))

            # Save assistant message
            assistant_message = Message(
                id=assistant_msg_id,
                chat_id=chat_id,
                content=full_response,
                role="assistant",
                timestamp=datetime.now().isoformat()
            )
            mock_messages[chat_id].append(assistant_message)

            # Send end of assistant message
            await websocket.send_text(json.dumps({
                "type": "assistant_end",
                "message": assistant_message.dict()
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

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
