import logging
import asyncio
from typing import List, Dict, Any, Optional
from models.schemas import ModelConfig
from services.openrouter_client import OpenRouterClient
from services.groq_client import GroqClient

logger = logging.getLogger("boule_ai.provider_manager")

class ProviderManager:
    """
    Manages multiple LLM providers and routes requests accordingly.
    """
    def __init__(self):
        self.openrouter_client = OpenRouterClient()
        self.groq_client = GroqClient()

    async def chat(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Routes the chat request to the correct provider.
        """
        provider = config.provider.lower()
        model = config.model

        if provider == "openrouter":
            return await self.openrouter_client.chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        elif provider == "groq":
            return await self.groq_client.chat(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        else:
            logger.error("Unknown provider: %s", provider)
            return f"[Error: Unknown provider {provider}]"

    async def close(self):
        """Closes all underlying sessions."""
        await asyncio.gather(
            self.openrouter_client.close(),
            self.groq_client.close(),
            return_exceptions=True
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
