"""
Клиент для работы с OpenAI Whisper API
"""
from pathlib import Path
from typing import Optional

from openai import OpenAI

from config import OPENAI_API_KEY, OPENROUTER_BASE_URL


class WhisperClient:
    """Клиент для транскрипции аудио через Whisper API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация клиента Whisper

        Args:
            api_key: API ключ OpenAI (если не указан, используется из config)
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key не найден. Установите OPENAI_API_KEY в .env")

        self.client = OpenAI(api_key=self.api_key, base_url=OPENROUTER_BASE_URL)

    def transcribe_audio(
        self,
        audio_file_path: str | Path,
        language: str = "ru",
        response_format: str = "text"
    ) -> str:
        """
        Транскрибирует аудио файл в текст

        Args:
            audio_file_path: Путь к аудио файлу (mp3, mp4, wav, и т.д.)
            language: Язык аудио (по умолчанию "ru" - русский)
            response_format: Формат ответа ("text", "json", "srt", "vtt")

        Returns:
            Текст транскрипции

        Raises:
            FileNotFoundError: Если файл не найден
            Exception: При ошибке API
        """
        audio_path = Path(audio_file_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Аудио файл не найден: {audio_path}")

        print(f"Отправка файла {audio_path.name} в Whisper API...")

        try:
            audio_file = open(audio_path, "rb")

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format=response_format
            )

            audio_file.close()

            # Если response_format="text", возвращается строка
            # Если "json", возвращается объект с полем text
            if isinstance(transcript, str):
                result = transcript
            else:
                result = transcript.text  # type: ignore

            print(f"Транскрипция успешно получена ({len(result)} символов)")
            return result

        except Exception as e:
            print(f"Ошибка при транскрипции: {e}")
            raise


def transcribe_file(file_path: str | Path, language: str = "ru") -> str:
    """
    Удобная функция для быстрой транскрипции файла

    Args:
        file_path: Путь к аудио файлу
        language: Язык аудио

    Returns:
        Текст транскрипции
    """
    client = WhisperClient()
    return client.transcribe_audio(file_path, language=language)
