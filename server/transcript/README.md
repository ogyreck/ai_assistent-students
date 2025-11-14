# Приложение для транскрипции и анализа аудио

Приложение обрабатывает MP3 файлы через Whisper API (транскрипция) и OpenRouter API (анализ текста).

## Структура проекта

```
transcript/
├── AlGore_2006.mp3          # Пример аудио файла
├── config.py                 # Конфигурация и переменные окружения
├── database.py               # Заглушка для работы с БД
├── openrouter_client.py      # Клиент для OpenRouter API
├── whisper_client.py         # Клиент для Whisper API
├── main.py                   # Главный файл приложения
├── .env.example              # Пример конфигурации
└── README.md                 # Этот файл
```

## Установка

1. Создайте файл `.env` на основе `.env.example`:

```bash
cp .env.example .env
```

2. Заполните `.env` вашими API ключами:

```env
OPENAI_API_KEY=sk-...
OPENROUTER_API_KEY=sk-or-...
```

3. Убедитесь, что установлены зависимости (уже есть в pyproject.toml):

```bash
# Если нужно установить зависимости
pip install openai
```

## Использование

### Из командной строки

Базовое использование:

```bash
cd transcript
python main.py AlGore_2006.mp3
```

С пользовательским промптом:

```bash
python main.py AlGore_2006.mp3 --prompt "Выдели ключевые идеи из этой речи"
```

С указанием языка:

```bash
python main.py audio.mp3 --language en
```

Без сохранения в БД:

```bash
python main.py audio.mp3 --no-db
```

Просмотр справки:

```bash
python main.py --help
```

### Из Python кода

```python
from server.transcript import process_audio_file

# Базовое использование
result = process_audio_file("AlGore_2006.mp3")
print(result["transcript"])
print(result["ai_response"])

# С пользовательским промптом
result = process_audio_file(
    "AlGore_2006.mp3",
    custom_prompt="Создай краткое резюме этой речи в 3-5 пунктах"
)

# Использование отдельных модулей
from server.transcript import WhisperClient, OpenRouterClient

# Только транскрипция
whisper = WhisperClient()
transcript = whisper.transcribe_audio("audio.mp3")

# Только обработка текста
openrouter = OpenRouterClient()
response = openrouter.process_text(
    text="Какой-то текст",
    prompt="Проанализируй этот текст"
)
```

## Настройка

### Переменные окружения

- `OPENAI_API_KEY` - API ключ OpenAI (обязательно)
- `OPENROUTER_API_KEY` - API ключ OpenRouter (обязательно)
- `OPENROUTER_MODEL` - Модель для использования (по умолчанию: `anthropic/claude-3-sonnet`)
- `OPENROUTER_PROMPT` - Промпт по умолчанию

### База данных

По умолчанию используется заглушка, которая сохраняет данные в `transcriptions.json`.

Для использования реальной БД замените `database.py` на реализацию с PostgreSQL/SQLite.

## Процесс обработки

1. **Загрузка файла** - Чтение MP3 файла
2. **Транскрипция** - Отправка в Whisper API для преобразования речи в текст
3. **Сохранение в БД** - Сохранение транскрипции (с метаданными)
4. **Анализ** - Отправка транскрипции в OpenRouter для анализа
5. **Возврат результата** - Получение и возврат ответа от AI

## API документация

### `process_audio_file()`

Главная функция для обработки аудио файлов.

**Параметры:**
- `audio_file_path` (str) - Путь к аудио файлу
- `custom_prompt` (str, optional) - Пользовательский промпт
- `language` (str, default="ru") - Язык аудио
- `save_to_db` (bool, default=True) - Сохранять ли в БД

**Возвращает:**
```python
{
    "transcript": "текст транскрипции...",
    "ai_response": "ответ от AI...",
    "db_id": "1"  # если save_to_db=True
}
```

### `WhisperClient.transcribe_audio()`

Транскрибирует аудио в текст.

**Параметры:**
- `audio_file_path` (str | Path) - Путь к аудио файлу
- `language` (str, default="ru") - Язык аудио
- `response_format` (str, default="text") - Формат ответа

### `OpenRouterClient.process_text()`

Обрабатывает текст через AI модель.

**Параметры:**
- `text` (str) - Текст для обработки
- `prompt` (str, optional) - Пользовательский промпт
- `system_prompt` (str, optional) - Системный промпт
- `temperature` (float, default=0.7) - Температура генерации
- `max_tokens` (int, default=2000) - Максимум токенов

## Примеры использования

### Пример 1: Анализ лекции

```python
result = process_audio_file(
    "lecture.mp3",
    custom_prompt="Создай конспект лекции с основными темами и примерами"
)
```

### Пример 2: Транскрипция интервью

```python
result = process_audio_file(
    "interview.mp3",
    custom_prompt="Выдели ключевые вопросы и ответы из интервью"
)
```

### Пример 3: Обработка на английском

```python
result = process_audio_file(
    "podcast.mp3",
    language="en",
    custom_prompt="Summarize this podcast episode"
)
```

## Устранение неполадок

### Ошибка: "OpenAI API key не найден"

Убедитесь, что создан файл `.env` и в нем указан `OPENAI_API_KEY`.

### Ошибка: "OpenRouter API key не найден"

Убедитесь, что в `.env` указан `OPENROUTER_API_KEY`.

### Ошибка: "Файл не найден"

Проверьте путь к аудио файлу. Используйте абсолютный путь или путь относительно текущей директории.

## Лицензия

MIT
