"""
Приложение для обработки аудио файлов через Whisper API и OpenRouter
"""
from .main import process_audio_file
from .whisper_client import WhisperClient, transcribe_file
from .openrouter_client import OpenRouterClient, process_transcript
from .database import DatabaseStub, save_to_database

__all__ = [
    "process_audio_file",
    "WhisperClient",
    "transcribe_file",
    "OpenRouterClient",
    "process_transcript",
    "DatabaseStub",
    "save_to_database",
]
