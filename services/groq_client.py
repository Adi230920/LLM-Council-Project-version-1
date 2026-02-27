import asyncio
import logging
import os
import random
from typing import Any

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("boule_ai.groq")

GROQ_API_BASE: str = "https://api.groq.com/openai/v1/chat/completions"

# Timeout settings
CONNECT_TIMEOUT: float = 8.0
READ_TIMEOUT: float = 25.0

# Retry settings
MAX_RETRIES: int = 1
BACKOFF_BASE: float = 2.0
BACKOFF_JITTER: float = 1.0

FALLBACK_RESPONSE_TEMPLATE: str = "[Groq model {model} failed after {retries} retries]"


class GroqClient:
    """
    Async client for Groq's /chat/completions endpoint.
    """

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = MAX_RETRIES,
        backoff_base: float = BACKOFF_BASE,
    ) -> None:
        self._api_key: str = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self._api_key:
            raise EnvironmentError("GROQ_API_KEY is not set.")

        self._max_retries: int = max_retries
        self._backoff_base: float = backoff_base
        self._session: aiohttp.ClientSession | None = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                connect=CONNECT_TIMEOUT,
                sock_read=READ_TIMEOUT,
            )
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "GroqClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error: str = "unknown error"

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info("→ Groq [%s] attempt %d/%d", model, attempt, self._max_retries)
                result = await self._post(payload)
                return result

            except (aiohttp.ClientConnectionError, aiohttp.ServerTimeoutError, asyncio.TimeoutError) as exc:
                last_error = str(exc)
            except aiohttp.ClientResponseError as exc:
                last_error = f"HTTP {exc.status}"
                if exc.status != 429 and 400 <= exc.status < 500:
                    break
            except Exception as exc:
                last_error = str(exc)
                break

            if attempt < self._max_retries:
                sleep_time = (self._backoff_base ** attempt) + random.uniform(-BACKOFF_JITTER, BACKOFF_JITTER)
                await asyncio.sleep(max(sleep_time, 0.5))

        return FALLBACK_RESPONSE_TEMPLATE.format(model=model, retries=self._max_retries)

    async def _post(self, payload: dict[str, Any]) -> str:
        session = self._get_session()
        async with session.post(GROQ_API_BASE, json=payload) as response:
            response.raise_for_status()
            data = await response.json()
            return data["choices"][0]["message"]["content"]
