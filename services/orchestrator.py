import logging
import time
from typing import List, Optional
from models.schemas import DeliberationTrace, ConsultRequest, ModelConfig
from services.provider_manager import ProviderManager
from services.council_service import generate_opinions
from services.review_service import conduct_reviews
from services.chairman_service import synthesize_deliberation

logger = logging.getLogger("boule_ai.orchestrator")

# ---------------------------------------------------------------------------
# Default council configuration — all are valid free-tier OpenRouter models.
# Previously "openrouter/free" was an invalid model ID and caused 1 of 4
# members to always fail. Replaced with a real free model.
# ---------------------------------------------------------------------------
DEFAULT_COUNCIL_MODELS = [
    ModelConfig(provider="openrouter", model="arcee-ai/trinity-large-preview:free"),
    ModelConfig(provider="openrouter", model="z-ai/glm-4.5-air:free"),
    ModelConfig(provider="openrouter", model="arcee-ai/trinity-mini:free"),
    ModelConfig(provider="openrouter", model="arcee-ai/trinity-mini:free"),
]

DEFAULT_CHAIRMAN_MODEL = ModelConfig(provider="openrouter", model="arcee-ai/trinity-large-preview:free")

async def run_deliberation(
    request: ConsultRequest,
    provider_manager: ProviderManager
) -> DeliberationTrace:
    """
    Coordinates the full 3-stage LLM Council deliberation loop.
    """
    t_start = time.monotonic()
    
    council_models = request.council_models or DEFAULT_COUNCIL_MODELS
    chairman_model = request.chairman_model or DEFAULT_CHAIRMAN_MODEL
    
    # --- STAGE 1: Independent Opinions ---
    opinions = await generate_opinions(
        prompt=request.prompt,
        model_list=council_models,
        provider_manager=provider_manager,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    t_stage1 = time.monotonic()
    
    # --- STAGE 2: Anonymous Cross-Review ---
    reviews = []
    if any(op.succeeded for op in opinions):
        reviews = await conduct_reviews(
            prompt=request.prompt,
            opinions=opinions,
            reviewer_configs=council_models,
            provider_manager=provider_manager,
            temperature=0.3
        )
    else:
        logger.warning("All council opinions failed — skipping Stage 2 review.")
    t_stage2 = time.monotonic()
    
    # --- STAGE 3: Chairman Synthesis ---
    verdict = await synthesize_deliberation(
        prompt=request.prompt,
        opinions=opinions,
        reviews=reviews,
        chairman_config=chairman_model,
        provider_manager=provider_manager
    )
    t_end = time.monotonic()
    
    trace = DeliberationTrace(
        original_prompt=request.prompt,
        stage1_opinions=opinions,
        stage2_reviews=reviews,
        verdict=verdict,
        meta={
            "timing": {
                "stage1_seconds": round(t_stage1 - t_start, 2),
                "stage2_seconds": round(t_stage2 - t_stage1, 2),
                "stage3_seconds": round(t_end - t_stage2, 2),
                "total_seconds": round(t_end - t_start, 2)
            },
            "council_size": len(council_models),
            "chairman_model": chairman_model.model
        }
    )
    
    logger.info("✅ Deliberation complete in %.2fs", t_end - t_start)
    return trace
