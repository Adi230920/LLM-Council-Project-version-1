import asyncio
import logging
from typing import List, Sequence
from models.schemas import Stage1Opinion, ModelConfig
from services.provider_manager import ProviderManager

logger = logging.getLogger("boule_ai.council_service")

STAGE1_SYSTEM_PROMPT = (
    "You are an expert advisor. Provide a concise, accurate, and deeply reasoned "
    "response to the user's query. Your answer must be independent and not reference other models."
)

async def generate_opinions(
    prompt: str,
    model_list: Sequence[ModelConfig],
    provider_manager: ProviderManager,
    temperature: float = 0.7,
    max_tokens: int = 1024
) -> List[Stage1Opinion]:
    """
    Stage 1: Independent First Opinions.
    Queries N models (across different providers) in parallel.
    """
    logger.info("Executing Stage 1: Generating %d opinions", len(model_list))
    
    messages = [
        {"role": "system", "content": STAGE1_SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
    ]
    
    coroutines = [
        provider_manager.chat(
            config=config,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        for config in model_list
    ]
    
    raw_results = await asyncio.gather(*coroutines, return_exceptions=True)
    
    opinions = []
    for i, (config, result) in enumerate(zip(model_list, raw_results), start=1):
        succeeded = True
        response_text = result
        
        if isinstance(result, Exception):
            logger.error("Model %s (%s) failed in Stage 1: %s", config.model, config.provider, result)
            succeeded = False
            response_text = f"[{config.model} failed to generate an opinion]"
        elif isinstance(result, str) and result.startswith("[") and "failed" in result.lower():
            succeeded = False

        opinions.append(Stage1Opinion(
            model_id=config.model,
            provider=config.provider,
            short_name=config.model.split("/")[-1].split(":")[0],
            response=response_text,
            succeeded=succeeded,
            response_id=i
        ))
        
    return opinions
