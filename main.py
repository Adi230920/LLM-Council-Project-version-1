"""
BouleAI — FastAPI Application Entry Point

Initializes the FastAPI app, mounts static files for the vanilla frontend,
and registers API routers. All heavy lifting (model calls) is delegated
to the services layer which is fully asynchronous.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("boule_ai")


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown tasks."""
    logger.info("🚀 BouleAI starting up…")
    yield
    logger.info("🛑 BouleAI shutting down…")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="BouleAI — LLM Advisory Council",
    description=(
        "Queries 4 Council LLMs concurrently via OpenRouter (free tier), "
        "aggregates their answers, and passes the result to a Chairman model "
        "for a final synthesized verdict."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the vanilla-JS frontend served on the same origin (or locally)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# API routers — registered BEFORE the static catch-all mount so /api/v1/*
# routes are matched first and not shadowed by the frontend's '/' mount.
# ---------------------------------------------------------------------------
from routers.api import router as api_router   # noqa: E402
app.include_router(api_router)


# ---------------------------------------------------------------------------
# Static files — vanilla HTML/CSS/JS frontend
# IMPORTANT: must be mounted LAST — StaticFiles with html=True acts as a
# catch-all and would swallow API routes if registered first.
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info("✅ Frontend static files mounted from: %s", FRONTEND_DIR)
else:
    logger.warning(
        "⚠️  'frontend/' directory not found — skipping static file mount. "
        "Create it and add index.html to enable the UI."
    )


# ---------------------------------------------------------------------------
# Health-check — always useful
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Meta"])
async def health_check():
    """Returns a simple liveness signal."""
    return {"status": "ok", "service": "BouleAI"}
