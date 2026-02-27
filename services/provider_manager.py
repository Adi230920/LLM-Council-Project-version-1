import logging
import asyncio
import os
from typing import List, Dict, Any, Optional
from models.schemas import ModelConfig
from services.openrouter_client import OpenRouterClient
from services.groq_client import GroqClient

logger = logging.getLogger("boule_ai.provider_manager")


class ProviderManager:
    """
    Manages multiple LLM providers and routes requests accordingly.

    Clients are lazily initialized on first use so that a missing API key
    for one provider does not crash the entire application at startup
    (important for Vercel cold-starts and partial-key deployments).
    """

    def __init__(self) -> None:
        self._openrouter_client: Optional[OpenRouterClient] = None
        self._groq_client: Optional[GroqClient] = None

    # ------------------------------------------------------------------ #
    # Lazy accessors                                                       #
    # ------------------------------------------------------------------ #

    @property
    def openrouter_client(self) -> Optional[OpenRouterClient]:
        if self._openrouter_client is None:
            if not os.environ.get("OPENROUTER_API_KEY"):
                logger.warning("OPENROUTER_API_KEY is not set — OpenRouter provider disabled.")
                return None
            try:
                self._openrouter_client = OpenRouterClient()
            except Exception as exc:
                logger.error("Failed to initialise OpenRouterClient: %s", exc)
                return None
        return self._openrouter_client

    @property
    def groq_client(self) -> Optional[GroqClient]:
        if self._groq_client is None:
            if not os.environ.get("GROQ_API_KEY"):
                logger.warning("GROQ_API_KEY is not set — Groq provider disabled.")
                return None
            try:
                self._groq_client = GroqClient()
            except Exception as exc:
                logger.error("Failed to initialise GroqClient: %s", exc)
                return None
        return self._groq_client

    # ------------------------------------------------------------------ #
    # Routing                                                              #
    # ------------------------------------------------------------------ #

    async def chat(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> str:
        """Routes the chat request to the correct provider."""
        provider = config.provider.lower()
        model = config.model

        if provider == "openrouter":
            client = self.openrouter_client
            if client is None:
                return "[Error: OPENROUTER_API_KEY is not configured on this deployment]"
            return await client.chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        if provider == "groq":
            client = self.groq_client
            if client is None:
                return "[Error: GROQ_API_KEY is not configured on this deployment]"
            return await client.chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        logger.error("Unknown provider: %s", provider)
        return f"[Error: Unknown provider '{provider}']"

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def close(self) -> None:
        """Gracefully closes all open client sessions."""
        closers = []
        if self._openrouter_client is not None:
            closers.append(self._openrouter_client.close())
        if self._groq_client is not None:
            closers.append(self._groq_client.close())
        if closers:
            await asyncio.gather(*closers, return_exceptions=True)

    async def __aenter__(self) -> "ProviderManager":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

