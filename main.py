from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import os

# ✅ Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()


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
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown tasks."""
    logger.info("🚀 BouleAI starting up…")
    yield
    logger.info("🛑 BouleAI shutting down…")


# ---------------------------------------------------------------------------
# Rate limiter (in-memory, per-IP)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address, default_limits=["20/minute"])

# App factory  (docs disabled in production)
# ---------------------------------------------------------------------------
_IS_DEV = os.getenv("ENVIRONMENT", "production").lower() == "development"
app = FastAPI(
    title="BouleAI — LLM Advisory Council",
    description=(
        "ChatGPT-style interface for the high-fidelity 3-stage LLM Council."
    ),
    version="0.2.0",
    lifespan=lifespan,
    docs_url="/docs" if _IS_DEV else None,
    redoc_url="/redoc" if _IS_DEV else None,
    openapi_url="/openapi.json" if _IS_DEV else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS — restrict to allowed origins in production
# ---------------------------------------------------------------------------
_allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
_allowed_origins = [o.strip() for o in _allowed_origins if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,  # No cookies/auth; credentials=True + "*" is invalid anyway
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# ---------------------------------------------------------------------------
# Security headers middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # ✅ Let CORSMiddleware handle OPTIONS preflight directly.
    # If we process OPTIONS here first, CORS never gets to respond with 200.
    if request.method == "OPTIONS":
        response: Response = await call_next(request)
        return response

    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # ✅ connect-src must include the Render backend so the Vercel frontend
    #    can fetch it without the browser blocking it via CSP.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "connect-src 'self' https://bouleai.onrender.com; "
        "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:"
    )
    # Remove server identification
    try:
        del response.headers["server"]
    except KeyError:
        pass
    return response

# ---------------------------------------------------------------------------
# API routers
# ---------------------------------------------------------------------------
from routers.api import router as api_router

app.include_router(api_router)


# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info("✅ Frontend static files mounted from: %s", FRONTEND_DIR)


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Meta"])
async def health_check():
    """Returns a simple liveness signal."""
    return {"status": "ok", "service": "BouleAI"}
