"""
BouleAI — API Router  (v1)
===========================

Exposes the full BouleAI scatter-gather-synthesize pipeline as a
single REST endpoint:

    POST /api/v1/consult
        Body : { "prompt": "...", "council_models": [...], "chairman_model": "..." }
        Returns: { "verdict": "...", "council_summary": {...}, "meta": {...} }

The entire flow is async end-to-end — no blocking code here.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from services.council_orchestrator import query_council, synthesize_consensus
from services.openrouter_client import OpenRouterClient

logger = logging.getLogger("boule_ai.api")

router = APIRouter(prefix="/api/v1", tags=["Council"])


# ---------------------------------------------------------------------------
# Default model configuration (all free-tier OpenRouter IDs)
# ---------------------------------------------------------------------------
DEFAULT_COUNCIL_MODELS: list[str] = [
    "arcee-ai/trinity-large-preview:free",
    "arcee-ai/trinity-large-preview:free",
    "arcee-ai/trinity-mini:free",
    "arcee-ai/trinity-large-preview:free",
]

DEFAULT_CHAIRMAN_MODEL: str = "arcee-ai/trinity-large-preview:free"


# ---------------------------------------------------------------------------
# Dependency — shared OpenRouterClient per request
# ---------------------------------------------------------------------------
# We create one client per request (not application-lifetime) to keep
# dependency injection simple.  For high-throughput scenarios, move this to
# app.state in main.py and inject via Request.app.state.client instead.
async def get_client() -> OpenRouterClient:   # type: ignore[misc]
    client = OpenRouterClient()
    try:
        yield client
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------
class ConsultRequest(BaseModel):
    """Payload for POST /api/v1/consult."""

    prompt: str = Field(
        ...,
        min_length=3,
        max_length=4096,
        description="The question or task to put to the Advisory Council.",
        examples=["What is the best strategy for reducing technical debt in a large codebase?"],
    )
    council_models: list[str] | None = Field(
        default=None,
        min_length=1,
        max_length=8,
        description="List of OpenRouter model IDs for the council members. Defaults to backend preset if Null.",
    )
    chairman_model: str | None = Field(
        default=None,
        description="OpenRouter model ID for the Chairman synthesizer. Defaults to backend preset if Null.",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for council models.",
    )
    max_tokens: int = Field(
        default=1024,
        ge=64,
        le=4096,
        description="Maximum tokens per council model response.",
    )

    @field_validator("council_models")
    @classmethod
    def models_must_be_non_empty_strings(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for m in v:
            if not m.strip():
                raise ValueError("council_models must not contain empty strings.")
        return v


class CouncilMemberSummary(BaseModel):
    """Per-model result included in the response for transparency."""

    model: str
    short_name: str
    succeeded: bool
    response_preview: str   # first 200 chars only — full text is in aggregated


class ConsultResponse(BaseModel):
    """Full response returned by POST /api/v1/consult."""

    verdict: str = Field(description="Chairman's synthesized, definitive answer.")
    aggregated_council_responses: str = Field(
        description="Raw formatted block of all council responses (for debugging / display)."
    )
    council_members: list[CouncilMemberSummary] = Field(
        description="Per-model summary with success status."
    )
    meta: dict = Field(description="Timing and participation statistics.")


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/consult",
    response_model=ConsultResponse,
    summary="Consult the BouleAI Advisory Council",
    description=(
        "Broadcasts the prompt to all council models concurrently "
        "(Scatter), aggregates their responses (Gather), then sends "
        "the aggregated output to the Chairman model for final synthesis."
    ),
)
async def consult(
    body: ConsultRequest,
    client: Annotated[OpenRouterClient, Depends(get_client)],
) -> ConsultResponse:
    """
    Full BouleAI pipeline:
      1. Scatter prompt → council models (concurrent via asyncio.gather)
      2. Gather + format all council responses
      3. Send aggregated block → Chairman for synthesis
      4. Return clean JSON response
    """
    t_start = time.monotonic()

    # ------------------------------------------------------------------
    # Step 1 & 2 — Scatter → Gather
    # ------------------------------------------------------------------
    council_models = body.council_models or DEFAULT_COUNCIL_MODELS
    chairman_model = body.chairman_model or DEFAULT_CHAIRMAN_MODEL

    logger.info(
        "📨 /consult received — prompt length=%d, council=%d models",
        len(body.prompt),
        len(council_models),
    )

    try:
        session = await query_council(
            prompt=body.prompt,
            model_list=council_models,
            client=client,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except Exception as exc:
        logger.exception("Council scatter-gather failed unexpectedly: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Council scatter-gather failed: {exc}",
        ) from exc

    aggregated = session.to_aggregated_string()
    t_after_council = time.monotonic()

    # ------------------------------------------------------------------
    # Step 3 — Chairman synthesis
    # ------------------------------------------------------------------
    try:
        verdict = await synthesize_consensus(
            original_prompt=body.prompt,
            aggregated_council_responses=aggregated,
            chairman_model=chairman_model,
            client=client,
            temperature=0.3,            # lower temp for deterministic synthesis
            max_tokens=body.max_tokens * 2,  # Chairman may need more room
        )
    except Exception as exc:
        logger.exception("Chairman synthesis failed unexpectedly: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Chairman synthesis failed: {exc}",
        ) from exc

    t_end = time.monotonic()

    # ------------------------------------------------------------------
    # Step 4 — Build response
    # ------------------------------------------------------------------
    member_summaries = [
        CouncilMemberSummary(
            model=m.model,
            short_name=m.short_name,
            succeeded=m.succeeded,
            response_preview=m.response[:200].rstrip() + ("…" if len(m.response) > 200 else ""),
        )
        for m in session.members
    ]

    meta = {
        "council_models_queried": len(session.members),
        "council_models_succeeded": session.success_count,
        "council_models_failed": session.failure_count,
        "chairman_model": chairman_model,
        "timing": {
            "council_scatter_gather_seconds": round(t_after_council - t_start, 2),
            "chairman_synthesis_seconds": round(t_end - t_after_council, 2),
            "total_seconds": round(t_end - t_start, 2),
        },
    }

    logger.info(
        "✅ /consult complete — %d/%d council succeeded, total=%.2fs",
        session.success_count,
        len(session.members),
        t_end - t_start,
    )

    return ConsultResponse(
        verdict=verdict,
        aggregated_council_responses=aggregated,
        council_members=member_summaries,
        meta=meta,
    )


# ---------------------------------------------------------------------------
# Config Endpoints
# ---------------------------------------------------------------------------
@router.get("/config", summary="Get default model configuration")
async def get_config():
    """Returns the default council and chairman models used by the backend."""
    return {
        "default_council_models": DEFAULT_COUNCIL_MODELS,
        "default_chairman_model": DEFAULT_CHAIRMAN_MODEL,
    }
