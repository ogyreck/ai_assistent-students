"""
Заглушка для работы с базой данных
В будущем можно заменить на реальную БД (PostgreSQL, SQLite и т.д.)
"""
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import json


class DatabaseStub:
    """Заглушка для БД - сохраняет данные в JSON файл"""

    def __init__(self, db_file: str = "transcriptions.json"):
        """
        Инициализация заглушки БД

        Args:
            db_file: Имя файла для хранения данных
        """
        self.db_file = Path(__file__).parent / db_file
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Создает файл БД если его нет"""
        if not self.db_file.exists():
            self._save_data([])

    def _load_data(self) -> list[dict[str, Any]]:
        """Загружает данные из файла"""
        with open(self.db_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_data(self, data: list[dict[str, Any]]) -> None:
        """Сохраняет данные в файл"""
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_transcription(
        self,
        audio_file: str,
        transcript: str,
        ai_response: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> int:
        """
        Сохраняет результаты транскрипции в БД

        Args:
            audio_file: Имя аудио файла
            transcript: Текст транскрипции
            ai_response: Ответ от AI модели (опционально)
            metadata: Дополнительные метаданные (опционально)

        Returns:
            ID записи
        """
        data = self._load_data()

        # Создаем новую запись
        record = {
            "id": len(data) + 1,
            "audio_file": audio_file,
            "transcript": transcript,
            "ai_response": ai_response,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat()
        }

        data.append(record)
        self._save_data(data)

        print(f"Запись сохранена в БД (ID: {record['id']})")
        return record["id"]

    def get_transcription(self, record_id: int) -> Optional[dict[str, Any]]:
        """
        Получает запись по ID

        Args:
            record_id: ID записи

        Returns:
            Запись или None если не найдена
        """
        data = self._load_data()
        for record in data:
            if record["id"] == record_id:
                return record
        return None

    def get_all_transcriptions(self) -> list[dict[str, Any]]:
        """
        Получает все записи

        Returns:
            Список всех записей
        """
        return self._load_data()

    def delete_transcription(self, record_id: int) -> bool:
        """
        Удаляет запись по ID

        Args:
            record_id: ID записи

        Returns:
            True если запись удалена, False если не найдена
        """
        data = self._load_data()
        original_length = len(data)
        data = [r for r in data if r["id"] != record_id]

        if len(data) < original_length:
            self._save_data(data)
            print(f"Запись {record_id} удалена из БД")
            return True

        return False


# Глобальный экземпляр БД
db = DatabaseStub()


def save_to_database(
    audio_file: str,
    transcript: str,
    ai_response: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None
) -> int:
    """
    Удобная функция для быстрого сохранения в БД

    Args:
        audio_file: Имя аудио файла
        transcript: Текст транскрипции
        ai_response: Ответ от AI модели
        metadata: Дополнительные метаданные

    Returns:
        ID записи
    """
    return db.save_transcription(audio_file, transcript, ai_response, metadata)
