from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import ConsultRequest, DeliberationTrace
from services.orchestrator import run_deliberation
from services.provider_manager import ProviderManager

logger = logging.getLogger("boule_ai.api")

router = APIRouter(prefix="/api/v1", tags=["Council"])

# ---------------------------------------------------------------------------
# Dependency — shared ProviderManager per request
# ---------------------------------------------------------------------------
async def get_manager() -> ProviderManager:
    manager = ProviderManager()
    try:
        yield manager
    finally:
        await manager.close()

# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post(
    "/consult",
    response_model=DeliberationTrace,
    summary="Consult the BouleAI Advisory Council (3-Stage Deliberation)",
    description=(
        "Executes a full 3-stage deliberation: "
        "1. Independent Opinions, 2. Anonymous Peer Review, 3. Chairman Synthesis."
    ),
)
async def consult(
    body: ConsultRequest,
    manager: Annotated[ProviderManager, Depends(get_manager)],
) -> DeliberationTrace:
    """
    Full BouleAI 3-Stage Pipeline with Multi-Provider support.
    """
    logger.info("📨 /consult received — prompt length=%d", len(body.prompt))

    try:
        trace = await run_deliberation(request=body, provider_manager=manager)
        return trace
    except Exception as exc:
        logger.exception("Council deliberation failed unexpectedly: %s", exc)
        raise HTTPException(
            status_code=502,
            detail=f"Council deliberation failed: {exc}",
        ) from exc

@router.get("/config", summary="Get default model configuration")
async def get_config():
    """Returns the default council and chairman models used by the backend."""
    from services.orchestrator import DEFAULT_COUNCIL_MODELS, DEFAULT_CHAIRMAN_MODEL
    return {
        "default_council_models": [m.dict() for m in DEFAULT_COUNCIL_MODELS],
        "default_chairman_model": DEFAULT_CHAIRMAN_MODEL.dict(),
    }
