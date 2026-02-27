"""
BouleAI — Resilient OpenRouter API Client
==========================================

Architecture rules enforced here:
  ✅ Rule 1 — 100 % async: uses aiohttp only, zero synchronous blocking calls.
  ✅ Rule 2 — Exponential backoff with jitter, max 3 retries per request.
  ✅ Rule 3 — Graceful degradation: after 3 failures the call returns a
              predefined fallback string instead of raising an exception.
  ✅ Rule 5 — API key loaded exclusively from the OPENROUTER_API_KEY env var.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
from typing import Any

import aiohttp
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("boule_ai.openrouter")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OPENROUTER_API_BASE: str = "https://openrouter.ai/api/v1/chat/completions"

# Timeout settings (seconds) — kept tight because free-tier drops connections.
CONNECT_TIMEOUT: float = 8.0
READ_TIMEOUT: float = 25.0

# Retry settings
MAX_RETRIES: int = 1
BACKOFF_BASE: float = 2.0   # seconds
BACKOFF_JITTER: float = 1.0  # ±1 s of random jitter

# Fallback string returned when all retries are exhausted (Rule 3).
FALLBACK_RESPONSE_TEMPLATE: str = "[{model} failed to respond after {retries} retries]"


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class OpenRouterClient:
    """
    Async client for OpenRouter's /chat/completions endpoint.

    Usage
    -----
    The recommended pattern is to share a single client instance for the
    lifetime of the application so the underlying aiohttp.ClientSession
    connection pool is reused across concurrent requests:

        client = OpenRouterClient()
        response = await client.chat(model="...", messages=[...])
        await client.close()

    Or use it as an async context manager:

        async with OpenRouterClient() as client:
            response = await client.chat(...)
    """

    def __init__(
        self,
        api_key: str | None = None,
        max_retries: int = MAX_RETRIES,
        backoff_base: float = BACKOFF_BASE,
    ) -> None:
        self._api_key: str = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self._api_key:
            raise EnvironmentError(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your .env file or set the environment variable."
            )

        self._max_retries: int = max_retries
        self._backoff_base: float = backoff_base

        # Build a single session; lazily created on first call.
        self._session: aiohttp.ClientSession | None = None

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def _get_session(self) -> aiohttp.ClientSession:
        """Return (or lazily create) the shared aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(
                connect=CONNECT_TIMEOUT,
                sock_read=READ_TIMEOUT,
            )
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                    # OpenRouter recommends these for free-tier routing.
                    "HTTP-Referer": "https://github.com/boule-ai",
                    "X-Title": "BouleAI Council",
                },
                timeout=timeout,
            )
        return self._session

    async def close(self) -> None:
        """Gracefully close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("aiohttp session closed.")

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "OpenRouterClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Core chat method — with retry + backoff
    # ------------------------------------------------------------------

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """
        Send a chat completion request to OpenRouter with exponential backoff.

        Parameters
        ----------
        model:        OpenRouter model ID (e.g. "mistralai/mistral-7b-instruct:free")
        messages:     List of {"role": "...", "content": "..."} dicts.
        temperature:  Sampling temperature.
        max_tokens:   Upper bound on response tokens.

        Returns
        -------
        str
            The assistant's reply text, or a fallback string if all retries
            are exhausted (Rule 3 — never raises an unhandled exception).
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        last_error: str = "unknown error"

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    "→ [%s] attempt %d/%d — requesting completion…",
                    model,
                    attempt,
                    self._max_retries,
                )
                result = await self._post(payload)
                logger.info("✓ [%s] success on attempt %d.", model, attempt)
                return result

            except (
                aiohttp.ClientConnectionError,
                aiohttp.ServerTimeoutError,
                asyncio.TimeoutError,
            ) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "⚠ [%s] attempt %d failed (network/timeout): %s",
                    model,
                    attempt,
                    last_error,
                )

            except aiohttp.ClientResponseError as exc:
                last_error = f"HTTP {exc.status}: {exc.message}"
                logger.warning(
                    "⚠ [%s] attempt %d failed (HTTP error): %s",
                    model,
                    attempt,
                    last_error,
                )
                # 4xx errors (except 429) won't be fixed by retrying.
                if exc.status != 429 and 400 <= exc.status < 500:
                    logger.error(
                        "✗ [%s] non-retryable HTTP %d — aborting retries.",
                        model,
                        exc.status,
                    )
                    break

            except Exception as exc:  # noqa: BLE001 — catch-all safety net
                last_error = f"{type(exc).__name__}: {exc}"
                logger.exception("✗ [%s] unexpected error: %s", model, last_error)
                break  # Unknown errors: don't retry blindly.

            # Exponential backoff with jitter (don't sleep after the last attempt)
            if attempt < self._max_retries:
                sleep_time = (self._backoff_base ** attempt) + random.uniform(
                    -BACKOFF_JITTER, BACKOFF_JITTER
                )
                sleep_time = max(sleep_time, 0.5)  # guard against negative jitter
                logger.info(
                    "⏳ [%s] backing off %.2f s before retry %d…",
                    model,
                    sleep_time,
                    attempt + 1,
                )
                await asyncio.sleep(sleep_time)

        # All retries exhausted — return graceful fallback (Rule 3).
        fallback = FALLBACK_RESPONSE_TEMPLATE.format(
            model=model, retries=self._max_retries
        )
        logger.error(
            "✗ [%s] all %d retries exhausted. Last error: %s. Returning fallback.",
            model,
            self._max_retries,
            last_error,
        )
        return fallback

    # ------------------------------------------------------------------
    # Internal HTTP post (no retry logic here — kept clean)
    # ------------------------------------------------------------------

    async def _post(self, payload: dict[str, Any]) -> str:
        """
        Fire a single POST to OpenRouter and extract the assistant text.

        Raises
        ------
        aiohttp.ClientResponseError  on non-2xx HTTP status.
        aiohttp.ServerTimeoutError   on read timeout.
        asyncio.TimeoutError         on connect timeout.
        ValueError                   if the JSON structure is unexpected.
        """
        session = self._get_session()

        async with session.post(OPENROUTER_API_BASE, json=payload) as response:
            response.raise_for_status()  # turns 4xx/5xx into ClientResponseError
            data: dict[str, Any] = await response.json()

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(
                f"Unexpected OpenRouter response structure: {data}"
            ) from exc
