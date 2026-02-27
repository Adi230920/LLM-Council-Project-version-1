from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import os

# ✅ Load environment variables from .env first — must happen before any import that reads env vars
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

# ---------------------------------------------------------------------------
# App factory (docs disabled in production)
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
# Defaults to localhost for local dev if ALLOWED_ORIGINS is not set.
# In production (Render), set ALLOWED_ORIGINS to your actual frontend URL(s).
# ---------------------------------------------------------------------------
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
if _raw_origins.strip():
    _allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
else:
    # Development fallback — allow local origins
    _allowed_origins = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ]

logger.info("🔒 CORS allowed origins: %s", _allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,  # No cookies/auth; credentials=True + "*" is invalid anyway
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# ---------------------------------------------------------------------------
# Security headers middleware
# NOTE: In Starlette, middleware is applied in reverse registration order
# (last registered = outermost wrapper). CORSMiddleware (registered above)
# will therefore run INSIDE this middleware, which is correct — security
# headers are applied AFTER CORS has done its work.
# For OPTIONS preflight, we pass through immediately so CORSMiddleware
# can respond with the correct 200 + CORS headers.
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # ✅ Pass OPTIONS straight through — CORSMiddleware handles preflight.
    if request.method == "OPTIONS":
        response: Response = await call_next(request)
        return response

    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Build connect-src dynamically from allowed origins so it stays in sync
    # with CORS config and doesn't need to be hardcoded per deployment.
    _connect_src_origins = " ".join(_allowed_origins)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"connect-src 'self' {_connect_src_origins}; "
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
# API routers — must be registered BEFORE the static files catch-all mount
# ---------------------------------------------------------------------------
from routers.api import router as api_router

app.include_router(api_router)


# ---------------------------------------------------------------------------
# Health-check — MUST be defined BEFORE the static files mount.
# The StaticFiles mount at "/" acts as a catch-all and will intercept ANY
# route registered after it, including /health.
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Meta"])
async def health_check():
    """Returns a simple liveness signal."""
    return {"status": "ok", "service": "BouleAI"}


# ---------------------------------------------------------------------------
# Static files — mounted LAST so it doesn't shadow API routes or /health
# ---------------------------------------------------------------------------
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    logger.info("✅ Frontend static files mounted from: %s", FRONTEND_DIR)
else:
    logger.warning("⚠️  Frontend directory not found at: %s — static files not served.", FRONTEND_DIR)
