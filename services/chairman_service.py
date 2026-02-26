import logging
from typing import List
from models.schemas import Stage1Opinion, Stage2Review, ModelConfig
from services.provider_manager import ProviderManager

logger = logging.getLogger("boule_ai.chairman_service")

CHAIRMAN_SYSTEM_PROMPT = """
You are the Chairman of the Advisory Council.
You are provided with:
1. The original user query.
2. Multiple council member responses (anonymized as Response #1, #2, etc.).
3. Anonymized cross-reviews and rankings for those responses.

**YOUR TASK:**
- Synthesize a final, definitive answer.
- Weigh responses with higher scores and better rankings more heavily.
- Resolve contradictions by looking at the logical critiques provided by other members.
- Explicitly mention areas of consensus or significant disagreement.
- Do not just concatenate; perform true meta-reasoning.

**STRUCTURE YOUR VERDICT:**
## Consensus Verdict
<Your main synthesized answer>

## Reasoning Trace
<Explain how you reconciled the different viewpoints and reviews>
""".strip()

async def synthesize_deliberation(
    prompt: str,
    opinions: List[Stage1Opinion],
    reviews: List[Stage2Review],
    chairman_config: ModelConfig,
    provider_manager: ProviderManager,
    temperature: float = 0.3
) -> str:
    """
    Stage 3: Chairman Meta-Synthesis.
    Reconciles opinions and reviews into a final verdict.
    """
    logger.info("Executing Stage 3: Synthesizing deliberation with model %s (%s)", chairman_config.model, chairman_config.provider)
    
    formatted_opinions = "\n".join([
        f"--- RESPONSE #{op.response_id} ---\n{op.response}\n"
        for op in opinions if op.succeeded
    ])
    
    formatted_reviews = []
    for rev in reviews:
        if not rev.succeeded: continue
        rev_text = f"Reviewer Model (Anonymized):\n"
        for score in rev.detailed_scores:
            rev_text += (
                f"- Assessment of Response #{score.response_id}:\n"
                f"  Scores: Accuracy={score.accuracy}/10, Insight={score.insight}/10, Logic={score.logic}/10\n"
                f"  Critique: {score.critique}\n"
            )
        formatted_reviews.append(rev_text)
    
    chairman_payload = (
        f"ORIGINAL QUERY: {prompt}\n\n"
        f"COUNCIL OPINIONS:\n{formatted_opinions}\n\n"
        f"PEER REVIEWS:\n" + "\n---\n".join(formatted_reviews)
    )
    
    messages = [
        {"role": "system", "content": CHAIRMAN_SYSTEM_PROMPT},
        {"role": "user", "content": chairman_payload}
    ]
    
    try:
        verdict = await provider_manager.chat(
            config=chairman_config,
            messages=messages,
            temperature=temperature,
            max_tokens=2048
        )
        return verdict
    except Exception as e:
        logger.exception("Chairman synthesis failed: %s", e)
        return f"[Chairman {chairman_config.model} failed to synthesize the council's deliberation.]"
