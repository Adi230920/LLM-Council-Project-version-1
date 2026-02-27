import asyncio
import logging
import json
import re
from typing import List
from models.schemas import Stage1Opinion, Stage2Review, RankingItem, DetailedScore, ModelConfig
from services.provider_manager import ProviderManager
from utils.anonymizer import anonymize_opinions

logger = logging.getLogger("boule_ai.review_service")

STAGE2_SYSTEM_PROMPT = """
You are a critical reviewer in an advisory council. You will be shown several anonymized responses to the same user query.

**YOUR TASK:**
1. Critique each response for accuracy, insight, and logical rigor.
2. Assign scores (0-10) for each category.
3. Rank the responses from best to worst.

**STRICT OUTPUT FORMAT:**
You must respond with a raw JSON object only. No preamble. No markdown blocks.
{
  "rankings": [{"response_id": 1, "score_total": 28}, ...],
  "detailed_scores": [{"response_id": 1, "accuracy": 9, "insight": 9, "logic": 10, "critique": "..."}]
}
""".strip()

async def conduct_reviews(
    prompt: str,
    opinions: List[Stage1Opinion],
    reviewer_configs: List[ModelConfig],
    provider_manager: ProviderManager,
    temperature: float = 0.3
) -> List[Stage2Review]:
    """
    Stage 2: Anonymous Cross-Review.
    Each model (across providers) critiques the others' responses.
    """
    logger.info("Executing Stage 2: Conducting cross-reviews with %d models", len(reviewer_configs))
    
    anonymized_text, _ = anonymize_opinions(opinions)
    
    review_prompt = (
        f"Original User Query: {prompt}\n\n"
        f"Council Responses to Review:\n{anonymized_text}"
    )
    
    messages = [
        {"role": "system", "content": STAGE2_SYSTEM_PROMPT},
        {"role": "user", "content": review_prompt}
    ]
    
    coroutines = [
        provider_manager.chat(
            config=config,
            messages=messages,
            temperature=temperature,
            max_tokens=1024  # ✅ Reduced from 2048 — reviews are structured JSON, 1024 is sufficient
        )
        for config in reviewer_configs
    ]
    
    raw_results = await asyncio.gather(*coroutines, return_exceptions=True)
    
    reviews = []
    for config, result in zip(reviewer_configs, raw_results):
        if isinstance(result, Exception) or (isinstance(result, str) and result.startswith("[")):
            logger.error("Reviewer %s (%s) failed in Stage 2", config.model, config.provider)
            reviews.append(Stage2Review(
                reviewer_model_id=config.model,
                reviewer_provider=config.provider,
                rankings=[],
                detailed_scores=[],
                succeeded=False
            ))
            continue
            
        try:
            # Strip possible markdown code fence wrapping
            clean_json = re.sub(r'^```(?:json)?\s*|\s*```$', '', result.strip(), flags=re.MULTILINE)
            data = json.loads(clean_json)
            
            reviews.append(Stage2Review(
                reviewer_model_id=config.model,
                reviewer_provider=config.provider,
                rankings=[RankingItem(**r) for r in data.get("rankings", [])],
                detailed_scores=[DetailedScore(**s) for s in data.get("detailed_scores", [])],
                succeeded=True
            ))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.warning("Failed to parse JSON from reviewer %s: %s", config.model, e)
            reviews.append(Stage2Review(
                reviewer_model_id=config.model,
                reviewer_provider=config.provider,
                rankings=[],
                detailed_scores=[],
                succeeded=False
            ))
            
    return reviews
