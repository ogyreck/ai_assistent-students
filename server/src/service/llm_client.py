"""
LLM Client Service using OpenAI SDK
Supports streaming responses for chat completions
"""
from openai import AsyncOpenAI
from typing import AsyncIterator, List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM Client for chat completions using OpenAI SDK.
    Compatible with OpenAI API and OpenRouter.

    Configuration is loaded from environment or config files:
    - base_url: API endpoint URL
    - api_key: Authentication token
    - model: Model name/identifier
    """

    def __init__(self, base_url: str, api_key: str, model: str):
        """
        Initialize LLM client

        Args:
            base_url: API base URL (e.g., https://api.openai.com/v1 or https://openrouter.ai/api/v1)
            api_key: API key for authentication
            model: Model name to use (e.g., gpt-4, qwen/qwen3-32b)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        logger.info(f"LLM Client initialized")
        logger.info(f"  Base URL: {base_url}")
        logger.info(f"  Model: {model}")

    def update_config(self, base_url: str = None, api_key: str = None, model: str = None):
        """
        Update LLM client configuration at runtime

        Args:
            base_url: New API base URL (optional)
            api_key: New API key (optional)
            model: New model name (optional)
        """
        if base_url:
            self.base_url = base_url
        if api_key:
            self.api_key = api_key
        if model:
            self.model = model

        # Reinitialize client with new config
        self.client = AsyncOpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
        )
        logger.info(f"LLM Client configuration updated")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  Model: {self.model}")

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """
        Stream chat completion response

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks from the model
        """
        try:
            logger.debug(f"Starting streaming completion with {len(messages)} messages")

            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content

        except Exception as e:
            logger.error(f"Error in streaming completion: {e}")
            raise

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get complete chat completion response (non-streaming)

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate

        Returns:
            Complete response text
        """
        try:
            logger.debug(f"Getting completion with {len(messages)} messages")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False,
            )

            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content
            else:
                logger.warning("No content in response")
                return ""

        except Exception as e:
            logger.error(f"Error in completion: {e}")
            raise


def create_llm_client(base_url: str, api_key: str, model: str) -> LLMClient:
    """
    Factory function to create LLM client

    Args:
        base_url: API base URL
        api_key: API key
        model: Model name

    Returns:
        Configured LLMClient instance
    """
    return LLMClient(base_url=base_url, api_key=api_key, model=model)
