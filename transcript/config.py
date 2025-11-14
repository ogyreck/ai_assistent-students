"""
Конфигурация для приложения транскрипции
"""
import os
from pathlib import Path
from typing import Optional

# Базовая директория проекта
BASE_DIR = Path(__file__).parent

# API ключи
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")

# Настройки OpenRouter
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3-sonnet")

# Промпт для обработки транскрипции
DEFAULT_PROMPT = os.getenv(
    "OPENROUTER_PROMPT",
    "Проанализируй следующую транскрипцию и предоставь краткое резюме:"
)

# Настройки Whisper
WHISPER_MODEL = "whisper-1"

# Директория для временных файлов
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)


def validate_config() -> bool:
    """Проверяет наличие всех необходимых переменных окружения"""
    missing = []

    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")

    if missing:
        print(f"Ошибка: отсутствуют переменные окружения: {', '.join(missing)}")
        print("Создайте файл .env на основе .env.example")
        return False

    return True
