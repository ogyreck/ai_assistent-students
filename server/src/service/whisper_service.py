"""
Whisper Transcription Service
Converts audio files to text using OpenAI Whisper API compatible endpoints

Supports:
- OpenAI API (https://api.openai.com/v1)
- OpenRouter (https://openrouter.ai/api/v1)
- CAILA (https://caila.io/api/mlpgate) - Uses base64 encoded audio
- Any OpenAI-compatible API
"""

from openai import AsyncOpenAI
from typing import Optional
import logging
from io import BytesIO
import re
import base64
import aiohttp
import json
import asyncio

from server.src.config.Config import CONFIG

logger = logging.getLogger(__name__)


class WhisperTranscriber:
    """
    Service for transcribing audio using OpenAI Whisper API compatible endpoints.

    Supports multiple audio formats: MP3, MP4, MPEG, MPGA, M4A, WAV, WEBM
    Can be configured with different API endpoints (OpenAI, OpenRouter, CAILA, etc.)
    """

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        """
        Initialize Whisper transcriber

        Args:
            api_key: API key for the service
            base_url: API endpoint URL (will be normalized automatically)
        """
        self.api_key = api_key
        self.original_base_url = base_url
        # Normalize base_url to remove trailing /v1 if it exists
        self.base_url = self._normalize_base_url(base_url)

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.base_url,
        )
        logger.info(f"Whisper Transcriber initialized")
        logger.info(f"  Base URL: {self.base_url}")
        logger.info(f"  Original URL: {base_url}")

    def _normalize_base_url(self, url: str) -> str:
        """
        Normalize API base URL to ensure it ends with /v1

        Examples:
            https://api.openai.com/v1 -> https://api.openai.com/v1
            https://api.openai.com -> https://api.openai.com/v1
            https://caila.io/api/adapters/openai -> https://caila.io/api/adapters/openai
        """
        if not url:
            return "https://api.openai.com/v1"

        # Remove trailing slash
        url = url.rstrip('/')

        # If it already ends with /v1, return as is
        if url.endswith('/v1'):
            return url

        # Check if it's a known provider that needs special handling
        if 'caila.io' in url:
            # CAILA already has the full path, don't add /v1
            return url
        elif 'openrouter.ai' in url:
            # OpenRouter format
            if not url.endswith('/v1'):
                return url + '/v1'
            return url
        else:
            # Default: add /v1 if not present
            if not url.endswith('/v1'):
                return url + '/v1'
            return url

    async def transcribe(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        language: str = "ru",
        temperature: float = 0.0,
    ) -> dict:
        """
        Transcribe audio data to text

        Args:
            audio_data: Raw audio bytes
            filename: Original filename (for format detection)
            language: Language code (e.g., 'ru' for Russian, 'en' for English)
            temperature: Sampling temperature (0-1). Lower = more consistent

        Returns:
            Dictionary with transcribed text and metadata
        """
        try:
            logger.info(f"Starting transcription: {filename} ({len(audio_data)} bytes), language: {language}")

            # Check if this is Caila API (mlpgate endpoint)
            if 'mlpgate' in self.original_base_url:
                logger.info(f"Detected Caila API (mlpgate), using base64 encoding")
                return await self._transcribe_via_caila(audio_data, filename, language)

            # Create file-like object from bytes
            audio_file = BytesIO(audio_data)
            audio_file.name = filename

            # Try using OpenAI SDK first
            try:
                logger.info(f"Attempting transcription via OpenAI client: {self.base_url}")
                transcript = await self.client.audio.transcriptions.create(
                    model=CONFIG.transcribe.model,
                    file=audio_file,
                    language=language,
                    temperature=temperature,
                )

                transcribed_text = transcript.text
                logger.info(f"✓ Transcription successful via SDK: {len(transcribed_text)} characters")

                return {
                    "success": True,
                    "text": transcribed_text,
                    "language": language,
                    "model": CONFIG.transcribe.model,
                }
            except Exception as sdk_error:
                logger.warning(f"SDK transcription failed: {sdk_error}")
                # Try HTTP API method as fallback
                logger.info("Attempting transcription via HTTP API...")
                return await self._transcribe_via_http(audio_data, filename, language, temperature)

        except Exception as e:
            error_message = str(e)
            logger.error(f"Transcription error: {error_message}")
            return {
                "success": False,
                "text": "",
                "error": error_message,
                "model": "whisper-1",
            }

    async def _transcribe_via_caila(
        self,
        audio_data: bytes,
        filename: str,
        language: str,
    ) -> dict:
        """
        Transcribe using Caila's Faster Whisper API with base64 encoded audio

        Caila API format:
        POST https://caila.io/api/mlpgate/account/{author}/model/{service}/predict
        Header: MLP-API-KEY: {token}
        Body: {"audio_base64": "...base64 encoded audio..."}

        Args:
            audio_data: Raw audio bytes
            filename: Original filename
            language: Language code (note: Caila's Whisper supports language detection)

        Returns:
            Dictionary with transcribed text and metadata
        """
        try:
            logger.info(f"Transcribing via Caila API: {filename} ({len(audio_data)} bytes)")

            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            logger.info(f"Audio encoded to base64: {len(audio_base64)} characters")

            # Prepare request payload
            payload = {
                "audio_base64": audio_base64
            }

            # Make HTTP request to Caila API
            headers = {
                "MLP-API-KEY": self.api_key,
                "Content-Type": "application/json"
            }

            logger.info(f"Making Caila API request to: {self.original_base_url}")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.original_base_url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120)  # 2 minutes timeout for audio processing
                ) as resp:
                    response_text = await resp.text()

                    if resp.status == 200:
                        try:
                            data = json.loads(response_text)
                            # Caila returns: {"result": "transcribed text"} or similar structure
                            transcribed_text = data.get('result', data.get('text', ''))

                            if not transcribed_text and 'data' in data:
                                # Try alternative response structures
                                transcribed_text = data['data'].get('result', data['data'].get('text', ''))

                            logger.info(f"✓ Caila transcription successful: {len(transcribed_text)} characters")

                            return {
                                "success": True,
                                "text": transcribed_text,
                                "language": language,
                                "model": CONFIG.transcribe.model,
                            }
                        except json.JSONDecodeError:
                            logger.error(f"Failed to parse Caila response as JSON: {response_text[:200]}")
                            return {
                                "success": False,
                                "text": "",
                                "error": f"Invalid JSON response from Caila API",
                                "model": CONFIG.transcribe.model,
                            }
                    else:
                        logger.error(f"Caila API error ({resp.status}): {response_text}")
                        return {
                            "success": False,
                            "text": "",
                            "error": f"Caila API returned {resp.status}: {response_text}",
                            "model": CONFIG.transcribe.model,
                        }

        except asyncio.TimeoutError:
            logger.error("Caila API request timed out")
            return {
                "success": False,
                "text": "",
                "error": "Caila API request timed out (exceeded 120 seconds)",
                "model": CONFIG.transcribe.model,
            }
        except Exception as e:
            error_message = str(e)
            logger.error(f"Caila transcription error: {error_message}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "text": "",
                "error": error_message,
                "model": CONFIG.transcribe.model,
            }

    async def _transcribe_via_http(
        self,
        audio_data: bytes,
        filename: str,
        language: str,
        temperature: float,
    ) -> dict:
        """
        Fallback method: Transcribe using direct HTTP API call with aiohttp

        Args:
            audio_data: Raw audio bytes
            filename: Original filename
            language: Language code
            temperature: Sampling temperature

        Returns:
            Dictionary with transcribed text and metadata
        """
        try:
            import aiohttp

            # Construct API endpoint
            api_url = f"{self.base_url}/audio/transcriptions".rstrip('/')
            logger.info(f"Making HTTP request to: {api_url}")

            # Prepare form data
            form_data = aiohttp.FormData()
            form_data.add_field('file', BytesIO(audio_data), filename=filename)
            form_data.add_field('model', 'whisper-1')
            form_data.add_field('language', language)
            form_data.add_field('temperature', str(temperature))

            # Make async HTTP request
            async with aiohttp.ClientSession() as session:
                headers = {
                    'Authorization': f'Bearer {self.api_key}'
                }

                async with session.post(api_url, data=form_data, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        text = data.get('text', '')
                        logger.info(f"✓ Transcription successful via HTTP: {len(text)} characters")
                        return {
                            "success": True,
                            "text": text,
                            "language": language,
                            "model": "whisper-1",
                        }
                    else:
                        error_text = await resp.text()
                        logger.error(f"HTTP API error ({resp.status}): {error_text}")
                        return {
                            "success": False,
                            "text": "",
                            "error": f"HTTP {resp.status}: {error_text}",
                            "model": "whisper-1",
                        }

        except ImportError:
            logger.warning("aiohttp not installed, cannot use HTTP fallback")
            return {
                "success": False,
                "text": "",
                "error": "aiohttp is required for HTTP transcription fallback",
                "model": "whisper-1",
            }
        except Exception as e:
            error_message = str(e)
            logger.error(f"HTTP transcription error: {error_message}")
            return {
                "success": False,
                "text": "",
                "error": error_message,
                "model": "whisper-1",
            }

    async def transcribe_with_translation(
        self,
        audio_data: bytes,
        filename: str = "audio.wav",
        target_language: str = "en",
        temperature: float = 0.0,
    ) -> dict:
        """
        Transcribe audio and translate to target language

        Note: Whisper API translates to English by default.
        For other languages, use transcribe() and then a translation API.

        Args:
            audio_data: Raw audio bytes
            filename: Original filename
            target_language: Target language code
            temperature: Sampling temperature

        Returns:
            Dictionary with transcribed text and translation
        """
        try:
            logger.info(f"Starting transcription with translation: {filename}")

            # Create file-like object
            audio_file = BytesIO(audio_data)
            audio_file.name = filename

            # Transcribe
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                temperature=temperature,
            )

            original_text = transcript.text

            logger.info(f"Transcription completed: {original_text[:50]}...")

            return {
                "success": True,
                "original_text": original_text,
                "translated_text": original_text,  # Would need separate translation API
                "target_language": target_language,
                "model": "whisper-1",
            }

        except Exception as e:
            error_message = str(e)
            logger.error(f"Transcription with translation error: {error_message}")
            return {
                "success": False,
                "original_text": "",
                "error": error_message,
                "model": "whisper-1",
            }


def create_whisper_transcriber(api_key: str, base_url: str = "https://api.openai.com/v1") -> WhisperTranscriber:
    """
    Factory function to create Whisper transcriber

    Args:
        api_key: OpenAI API key
        base_url: API endpoint URL

    Returns:
        Configured WhisperTranscriber instance
    """
    return WhisperTranscriber(api_key=CONFIG.transcribe.token, base_url=CONFIG.transcribe.url)
