"""
Calendar Service for managing calendar states and tasks
Provides CRUD operations for calendar-related data
"""

from typing import List, Optional, Dict
from datetime import datetime
from pydantic import BaseModel
import json
import os


class CalendarState(BaseModel):
    """Model for calendar state storage"""
    id: str
    user_id: str
    year: int
    month: int
    tasks: List[Dict] = []
    created_at: str
    updated_at: str


class CalendarTask(BaseModel):
    """Model for a single task in calendar"""
    id: str
    title: str
    description: Optional[str] = None
    date: str  # YYYY-MM-DD
    time: str  # HH:MM


class CalendarService:
    """Service for managing calendar states and tasks"""

    def __init__(self, storage_dir: str = "calendar_storage"):
        """
        Initialize CalendarService

        Args:
            storage_dir: Directory for storing calendar states
        """
        self.storage_dir = storage_dir
        self.states: Dict[str, CalendarState] = {}
        self._ensure_storage_dir()
        self._load_all_states()

    def _ensure_storage_dir(self) -> None:
        """Ensure storage directory exists"""
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_state_file_path(self, user_id: str, year: int, month: int) -> str:
        """Get file path for calendar state"""
        filename = f"calendar_{user_id}_{year}_{month:02d}.json"
        return os.path.join(self.storage_dir, filename)

    def _get_state_key(self, user_id: str, year: int, month: int) -> str:
        """Get cache key for calendar state"""
        return f"{user_id}_{year}_{month:02d}"

    def _load_all_states(self) -> None:
        """Load all calendar states from storage"""
        try:
            if not os.path.exists(self.storage_dir):
                return

            for filename in os.listdir(self.storage_dir):
                if filename.startswith("calendar_") and filename.endswith(".json"):
                    filepath = os.path.join(self.storage_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            state = CalendarState(**data)
                            key = self._get_state_key(
                                state.user_id,
                                state.year,
                                state.month
                            )
                            self.states[key] = state
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
        except Exception as e:
            print(f"Error loading calendar states: {e}")

    def _save_state(self, state: CalendarState) -> None:
        """Save calendar state to file"""
        try:
            filepath = self._get_state_file_path(
                state.user_id,
                state.year,
                state.month
            )
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(state.model_dump(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving calendar state: {e}")
            raise

    def get_or_create_state(
        self,
        user_id: str,
        year: int,
        month: int
    ) -> CalendarState:
        """
        Get or create calendar state for specific month

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)

        Returns:
            CalendarState object
        """
        key = self._get_state_key(user_id, year, month)

        if key in self.states:
            return self.states[key]

        # Create new state
        state = CalendarState(
            id=f"state_{user_id}_{year}_{month:02d}",
            user_id=user_id,
            year=year,
            month=month,
            tasks=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self.states[key] = state
        self._save_state(state)

        return state

    def get_state(
        self,
        user_id: str,
        year: int,
        month: int
    ) -> Optional[CalendarState]:
        """
        Get calendar state for specific month

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)

        Returns:
            CalendarState or None
        """
        key = self._get_state_key(user_id, year, month)
        return self.states.get(key)

    def create_task(
        self,
        user_id: str,
        year: int,
        month: int,
        task: CalendarTask
    ) -> CalendarTask:
        """
        Create a new task in calendar state

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)
            task: CalendarTask object

        Returns:
            Created CalendarTask
        """
        state = self.get_or_create_state(user_id, year, month)

        task_dict = task.model_dump()
        state.tasks.append(task_dict)
        state.updated_at = datetime.now().isoformat()

        self._save_state(state)

        return task

    def get_task(
        self,
        user_id: str,
        year: int,
        month: int,
        task_id: str
    ) -> Optional[CalendarTask]:
        """
        Get a specific task from calendar state

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)
            task_id: Task ID

        Returns:
            CalendarTask or None
        """
        state = self.get_state(user_id, year, month)
        if not state:
            return None

        task_dict = next((t for t in state.tasks if t['id'] == task_id), None)
        if task_dict:
            return CalendarTask(**task_dict)

        return None

    def update_task(
        self,
        user_id: str,
        year: int,
        month: int,
        task_id: str,
        task_update: CalendarTask
    ) -> Optional[CalendarTask]:
        """
        Update an existing task in calendar state

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)
            task_id: Task ID
            task_update: Updated CalendarTask object

        Returns:
            Updated CalendarTask or None
        """
        state = self.get_state(user_id, year, month)
        if not state:
            return None

        task_index = next(
            (i for i, t in enumerate(state.tasks) if t['id'] == task_id),
            None
        )

        if task_index is None:
            return None

        state.tasks[task_index] = task_update.model_dump()
        state.updated_at = datetime.now().isoformat()

        self._save_state(state)

        return task_update

    def delete_task(
        self,
        user_id: str,
        year: int,
        month: int,
        task_id: str
    ) -> bool:
        """
        Delete a task from calendar state

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)
            task_id: Task ID

        Returns:
            True if deleted successfully
        """
        state = self.get_state(user_id, year, month)
        if not state:
            return False

        initial_length = len(state.tasks)
        state.tasks = [t for t in state.tasks if t['id'] != task_id]

        if len(state.tasks) == initial_length:
            return False  # Task not found

        state.updated_at = datetime.now().isoformat()
        self._save_state(state)

        return True

    def get_all_tasks_in_month(
        self,
        user_id: str,
        year: int,
        month: int
    ) -> List[CalendarTask]:
        """
        Get all tasks for a specific month

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)

        Returns:
            List of CalendarTask objects
        """
        state = self.get_state(user_id, year, month)
        if not state:
            return []

        return [CalendarTask(**task) for task in state.tasks]

    def get_all_tasks_for_user(self, user_id: str) -> List[CalendarTask]:
        """
        Get all tasks for a user across all months

        Args:
            user_id: User ID

        Returns:
            List of CalendarTask objects
        """
        all_tasks = []
        for key, state in self.states.items():
            if state.user_id == user_id:
                all_tasks.extend([CalendarTask(**task) for task in state.tasks])

        return all_tasks

    def delete_state(self, user_id: str, year: int, month: int) -> bool:
        """
        Delete entire calendar state for a month

        Args:
            user_id: User ID
            year: Year
            month: Month (1-12)

        Returns:
            True if deleted successfully
        """
        key = self._get_state_key(user_id, year, month)

        if key not in self.states:
            return False

        # Remove from memory
        del self.states[key]

        # Remove from storage
        try:
            filepath = self._get_state_file_path(user_id, year, month)
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Error deleting state file: {e}")

        return True
