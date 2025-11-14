"""
Клиент для работы с OpenRouter API
"""
from typing import Optional

from openai import OpenAI

from config import (
    DEFAULT_PROMPT,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)


class OpenRouterClient:
    """Клиент для обработки текста через OpenRouter API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Инициализация клиента OpenRouter

        Args:
            api_key: API ключ OpenRouter (если не указан, используется из config)
            model: Модель для использования (если не указана, используется из config)
            base_url: Базовый URL API (если не указан, используется из config)
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OpenRouter API key не найден. Установите OPENROUTER_API_KEY в .env")

        self.model = model or OPENROUTER_MODEL
        self.base_url = base_url or OPENROUTER_BASE_URL

        # Создаем клиент OpenAI, но с базовым URL OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def process_text(
        self,
        text: str,
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        """
        Отправляет текст в OpenRouter для обработки

        Args:
            text: Текст для обработки (например, транскрипция)
            prompt: Пользовательский промпт (если не указан, используется DEFAULT_PROMPT)
            system_prompt: Системный промпт (опционально)
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            Ответ от модели

        Raises:
            Exception: При ошибке API
        """
        if not prompt:
            prompt = DEFAULT_PROMPT

        messages = []

        # Добавляем системный промпт, если он указан
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # Добавляем пользовательский промпт с текстом
        user_message = f"{prompt}\n\n{text}"
        messages.append({
            "role": "user",
            "content": user_message
        })

        print(f"Отправка запроса в OpenRouter (модель: {self.model})...")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=temperature,
                max_tokens=max_tokens
            )

            result = response.choices[0].message.content or ""
            print(f"Получен ответ от OpenRouter ({len(result)} символов)")
            return result

        except Exception as e:
            print(f"Ошибка при обработке через OpenRouter: {e}")
            raise


def process_transcript(
    transcript: str,
    prompt: Optional[str] = None,
    system_prompt: Optional[str] = None
) -> str:
    """
    Удобная функция для быстрой обработки транскрипции

    Args:
        transcript: Текст транскрипции
        prompt: Пользовательский промпт
        system_prompt: Системный промпт

    Returns:
        Обработанный текст от модели
    """
    client = OpenRouterClient()
    return client.process_text(
        text=transcript,
        prompt=prompt,
        system_prompt=system_prompt
    )
