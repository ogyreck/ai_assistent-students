"""
Project Service for managing projects and chats
Provides CRUD operations for project-related data with file persistence
"""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
import json
import os
import uuid


class Project(BaseModel):
    """Model for a project"""
    id: str
    name: str
    created_at: str
    updated_at: str = None


class Chat(BaseModel):
    """Model for a chat within a project"""
    id: str
    project_id: str
    name: str
    created_at: str
    updated_at: str = None


class Message(BaseModel):
    """Model for a message in a chat"""
    id: str
    chat_id: str
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: str


class ProjectService:
    """Service for managing projects and chats with file persistence"""

    def __init__(self, storage_dir: str = "project_storage"):
        """
        Initialize ProjectService

        Args:
            storage_dir: Directory for storing projects and chats
        """
        self.storage_dir = storage_dir
        self.projects: Dict[str, Project] = {}
        self.chats: Dict[str, Chat] = {}
        self.messages: Dict[str, List[Message]] = {}
        self._ensure_storage_dir()
        self._load_all_data()

    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "projects"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "chats"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "messages"), exist_ok=True)

    def _get_project_file_path(self, project_id: str) -> str:
        """Get file path for project"""
        return os.path.join(self.storage_dir, "projects", f"{project_id}.json")

    def _get_chat_file_path(self, chat_id: str) -> str:
        """Get file path for chat"""
        return os.path.join(self.storage_dir, "chats", f"{chat_id}.json")

    def _get_messages_file_path(self, chat_id: str) -> str:
        """Get file path for chat messages"""
        return os.path.join(self.storage_dir, "messages", f"{chat_id}.json")

    def _load_all_data(self) -> None:
        """Load all projects, chats, and messages from storage"""
        try:
            self._load_all_projects()
            self._load_all_chats()
            self._load_all_messages()
        except Exception as e:
            print(f"Error loading data: {e}")

    def _load_all_projects(self) -> None:
        """Load all projects from storage"""
        try:
            projects_dir = os.path.join(self.storage_dir, "projects")
            if not os.path.exists(projects_dir):
                return

            for filename in os.listdir(projects_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(projects_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            project = Project(**data)
                            self.projects[project.id] = project
                    except Exception as e:
                        print(f"Error loading project {filename}: {e}")
        except Exception as e:
            print(f"Error loading projects: {e}")

    def _load_all_chats(self) -> None:
        """Load all chats from storage"""
        try:
            chats_dir = os.path.join(self.storage_dir, "chats")
            if not os.path.exists(chats_dir):
                return

            for filename in os.listdir(chats_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(chats_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            chat = Chat(**data)
                            self.chats[chat.id] = chat
                    except Exception as e:
                        print(f"Error loading chat {filename}: {e}")
        except Exception as e:
            print(f"Error loading chats: {e}")

    def _load_all_messages(self) -> None:
        """Load all messages from storage"""
        try:
            messages_dir = os.path.join(self.storage_dir, "messages")
            if not os.path.exists(messages_dir):
                return

            for filename in os.listdir(messages_dir):
                if filename.endswith(".json"):
                    filepath = os.path.join(messages_dir, filename)
                    chat_id = filename[:-5]  # Remove .json
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            messages = [Message(**msg) for msg in data]
                            self.messages[chat_id] = messages
                    except Exception as e:
                        print(f"Error loading messages for {filename}: {e}")
        except Exception as e:
            print(f"Error loading messages: {e}")

    def _save_project(self, project: Project) -> None:
        """Save project to file"""
        try:
            filepath = self._get_project_file_path(project.id)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving project: {e}")
            raise

    def _save_chat(self, chat: Chat) -> None:
        """Save chat to file"""
        try:
            filepath = self._get_chat_file_path(chat.id)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chat.dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving chat: {e}")
            raise

    def _save_messages(self, chat_id: str, messages: List[Message]) -> None:
        """Save messages to file"""
        try:
            filepath = self._get_messages_file_path(chat_id)
            messages_data = [msg.dict() for msg in messages]
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving messages: {e}")
            raise

    # ==================== PROJECT OPERATIONS ====================

    def create_project(self, name: str) -> Project:
        """
        Create a new project

        Args:
            name: Project name

        Returns:
            Created Project
        """
        project = Project(
            id=f"proj-{uuid.uuid4().hex[:8]}",
            name=name,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.projects[project.id] = project
        self._save_project(project)
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """
        Get a project by ID

        Args:
            project_id: Project ID

        Returns:
            Project or None
        """
        return self.projects.get(project_id)

    def get_all_projects(self) -> List[Project]:
        """
        Get all projects

        Returns:
            List of all projects
        """
        return list(self.projects.values())

    def update_project(self, project_id: str, name: str) -> Optional[Project]:
        """
        Update a project

        Args:
            project_id: Project ID
            name: New project name

        Returns:
            Updated Project or None
        """
        project = self.projects.get(project_id)
        if not project:
            return None

        project.name = name
        project.updated_at = datetime.now().isoformat()
        self._save_project(project)
        return project

    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project and all its chats

        Args:
            project_id: Project ID

        Returns:
            True if deleted successfully
        """
        if project_id not in self.projects:
            return False

        # Delete all chats for this project
        chats_to_delete = [chat_id for chat_id, chat in self.chats.items()
                          if chat.project_id == project_id]
        for chat_id in chats_to_delete:
            self.delete_chat(project_id, chat_id)

        # Delete project
        del self.projects[project_id]

        try:
            filepath = self._get_project_file_path(project_id)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error deleting project file: {e}")

        return True

    # ==================== CHAT OPERATIONS ====================

    def create_chat(self, project_id: str, name: str) -> Optional[Chat]:
        """
        Create a new chat in a project

        Args:
            project_id: Project ID
            name: Chat name

        Returns:
            Created Chat or None if project doesn't exist
        """
        if project_id not in self.projects:
            return None

        chat = Chat(
            id=f"chat-{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            name=name,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.chats[chat.id] = chat
        self.messages[chat.id] = []
        self._save_chat(chat)
        self._save_messages(chat.id, [])
        return chat

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """
        Get a chat by ID

        Args:
            chat_id: Chat ID

        Returns:
            Chat or None
        """
        return self.chats.get(chat_id)

    def get_project_chats(self, project_id: str) -> List[Chat]:
        """
        Get all chats for a project

        Args:
            project_id: Project ID

        Returns:
            List of chats
        """
        return [chat for chat in self.chats.values() if chat.project_id == project_id]

    def update_chat(self, chat_id: str, name: str) -> Optional[Chat]:
        """
        Update a chat

        Args:
            chat_id: Chat ID
            name: New chat name

        Returns:
            Updated Chat or None
        """
        chat = self.chats.get(chat_id)
        if not chat:
            return None

        chat.name = name
        chat.updated_at = datetime.now().isoformat()
        self._save_chat(chat)
        return chat

    def delete_chat(self, project_id: str, chat_id: str) -> bool:
        """
        Delete a chat

        Args:
            project_id: Project ID
            chat_id: Chat ID

        Returns:
            True if deleted successfully
        """
        if chat_id not in self.chats:
            return False

        chat = self.chats[chat_id]
        if chat.project_id != project_id:
            return False

        del self.chats[chat_id]
        if chat_id in self.messages:
            del self.messages[chat_id]

        try:
            chat_filepath = self._get_chat_file_path(chat_id)
            if os.path.exists(chat_filepath):
                os.remove(chat_filepath)

            messages_filepath = self._get_messages_file_path(chat_id)
            if os.path.exists(messages_filepath):
                os.remove(messages_filepath)
        except Exception as e:
            print(f"Error deleting chat files: {e}")

        return True

    # ==================== MESSAGE OPERATIONS ====================

    def add_message(self, chat_id: str, content: str, role: str) -> Optional[Message]:
        """
        Add a message to a chat

        Args:
            chat_id: Chat ID
            content: Message content
            role: Message role ('user' or 'assistant')

        Returns:
            Created Message or None if chat doesn't exist
        """
        if chat_id not in self.chats:
            return None

        if chat_id not in self.messages:
            self.messages[chat_id] = []

        message = Message(
            id=f"msg-{uuid.uuid4().hex[:8]}",
            chat_id=chat_id,
            content=content,
            role=role,
            timestamp=datetime.now().isoformat()
        )
        self.messages[chat_id].append(message)
        self._save_messages(chat_id, self.messages[chat_id])
        return message

    def get_chat_messages(self, chat_id: str) -> List[Message]:
        """
        Get all messages for a chat

        Args:
            chat_id: Chat ID

        Returns:
            List of messages
        """
        return self.messages.get(chat_id, [])

    def get_message(self, chat_id: str, message_id: str) -> Optional[Message]:
        """
        Get a specific message

        Args:
            chat_id: Chat ID
            message_id: Message ID

        Returns:
            Message or None
        """
        messages = self.messages.get(chat_id, [])
        return next((msg for msg in messages if msg.id == message_id), None)

    def delete_message(self, chat_id: str, message_id: str) -> bool:
        """
        Delete a message from a chat

        Args:
            chat_id: Chat ID
            message_id: Message ID

        Returns:
            True if deleted successfully
        """
        if chat_id not in self.messages:
            return False

        initial_length = len(self.messages[chat_id])
        self.messages[chat_id] = [msg for msg in self.messages[chat_id]
                                   if msg.id != message_id]

        if len(self.messages[chat_id]) == initial_length:
            return False  # Message not found

        self._save_messages(chat_id, self.messages[chat_id])
        return True
