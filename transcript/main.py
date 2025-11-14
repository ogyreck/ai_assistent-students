"""
Главное приложение для обработки аудио файлов
Процесс:
1. Загрузка MP3 файла
2. Транскрипция через Whisper API
3. Сохранение в БД
4. Обработка через OpenRouter API
5. Возврат результата
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from config import validate_config
from database import save_to_database
from openrouter_client import OpenRouterClient
from whisper_client import WhisperClient


def process_audio_file(
    audio_file_path: str,
    custom_prompt: Optional[str] = None,
    language: str = "ru",
    save_to_db: bool = True
) -> dict[str, str]:
    """
    Обрабатывает аудио файл: транскрипция + анализ через AI

    Args:
        audio_file_path: Путь к аудио файлу (mp3, wav, и т.д.)
        custom_prompt: Пользовательский промпт для обработки (опционально)
        language: Язык аудио (по умолчанию "ru")
        save_to_db: Сохранять ли результаты в БД (по умолчанию True)

    Returns:
        Словарь с результатами:
        - transcript: текст транскрипции
        - ai_response: ответ от AI модели
        - db_id: ID записи в БД (если save_to_db=True)

    Raises:
        FileNotFoundError: Если файл не найден
        ValueError: Если не настроены API ключи
        Exception: При других ошибках
    """
    print("\n" + "=" * 60)
    print("Начало обработки аудио файла")
    print("=" * 60 + "\n")

    audio_path = Path(audio_file_path)
    print(f"Файл: {audio_path.name}")
    print(f"Размер: {audio_path.stat().st_size / 1024 / 1024:.2f} MB\n")

    # Шаг 1: Транскрипция через Whisper
    print("Шаг 1/4: Транскрипция аудио через Whisper API")
    print("-" * 60)
    whisper_client = WhisperClient()
    transcript = whisper_client.transcribe_audio(audio_path, language=language)
    print(f"Транскрипция готова!\n")

    # Показываем превью транскрипции
    preview_length = 200
    if len(transcript) > preview_length:
        print(f"Превью транскрипции: {transcript[:preview_length]}...\n")
    else:
        print(f"Транскрипция: {transcript}\n")

    # Шаг 2: Обработка через OpenRouter
    print("Шаг 2/4: Обработка транскрипции через OpenRouter API")
    print("-" * 60)
    openrouter_client = OpenRouterClient()
    ai_response = openrouter_client.process_text(
        text=transcript,
        prompt=custom_prompt
    )
    print(f"Обработка завершена!\n")

    # Показываем превью ответа AI
    if len(ai_response) > preview_length:
        print(f"Превью ответа: {ai_response[:preview_length]}...\n")
    else:
        print(f"Ответ AI: {ai_response}\n")

    # Шаг 3: Сохранение в БД
    db_id = None
    if save_to_db:
        print("Шаг 3/4: Сохранение в базу данных")
        print("-" * 60)
        db_id = save_to_database(
            audio_file=audio_path.name,
            transcript=transcript,
            ai_response=ai_response,
            metadata={
                "file_size": audio_path.stat().st_size,
                "language": language,
            }
        )
        print()

    print("Шаг 4/4: Готово!")
    print("=" * 60 + "\n")

    result = {
        "transcript": transcript,
        "ai_response": ai_response,
    }

    if db_id:
        result["db_id"] = str(db_id)

    return result


def main() -> None:
    """Главная функция для запуска из командной строки"""
    parser = argparse.ArgumentParser(
        description="Обработка аудио файлов: транскрипция + анализ через AI"
    )
    parser.add_argument(
        "audio_file",
        type=str,
        help="Путь к аудио файлу (mp3, wav, и т.д.)"
    )
    parser.add_argument(
        "--prompt",
        "-p",
        type=str,
        default=None,
        help="Пользовательский промпт для обработки транскрипции"
    )
    parser.add_argument(
        "--language",
        "-l",
        type=str,
        default="ru",
        help="Язык аудио (по умолчанию: ru)"
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Не сохранять результаты в БД"
    )

    args = parser.parse_args()

    # Проверяем конфигурацию
    if not validate_config():
        sys.exit(1)

    try:
        result = process_audio_file(
            audio_file_path=args.audio_file,
            custom_prompt=args.prompt,
            language=args.language,
            save_to_db=not args.no_db
        )

        # Выводим полные результаты
        print("\n" + "=" * 60)
        print("ПОЛНЫЕ РЕЗУЛЬТАТЫ")
        print("=" * 60 + "\n")

        print("ТРАНСКРИПЦИЯ:")
        print("-" * 60)
        print(result["transcript"])
        print("\n")

        print("ОТВЕТ AI:")
        print("-" * 60)
        print(result["ai_response"])
        print("\n")

        if "db_id" in result:
            print(f"ID записи в БД: {result['db_id']}\n")

    except FileNotFoundError as e:
        print(f"\nОшибка: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\nОшибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\nНеожиданная ошибка: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
