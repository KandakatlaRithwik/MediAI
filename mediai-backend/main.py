"""
Application entry point.

Run with:  uvicorn main:app --reload
or:        python main.py
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.routes import (
    auth, dashboard, health, history, ocr_report, rag,
    report_analysis, symptom_checker, system, upload,
)
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.database.connection import init_db

# Disable third-party telemetry / noisy logs as early as possible (before
# the libraries are imported elsewhere).
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "False")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

setup_logging()
logger = logging.getLogger(__name__)
system_logger = logging.getLogger("system")

# Quiet known noisy third-party loggers.
for _noisy in ("chromadb.telemetry", "sentence_transformers", "httpx", "urllib3", "PIL"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

settings = get_settings()

# Rate limiter (Module 7) — 60 requests per minute per IP by default.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    system_logger.info(
        "%s v%s starting up (env=%s)", settings.APP_NAME, settings.APP_VERSION, settings.APP_ENV
    )
    try:
        init_db()
        system_logger.info("Database tables initialized.")
    except Exception as exc:  # noqa: BLE001
        system_logger.warning("Database table initialization skipped/failed: %s", exc)

    # --- Preload heavy singletons so the first request isn't slow ---
    try:
        from app.services.embedding_service import EmbeddingService
        from app.rag.vector_store import VectorStoreService
        EmbeddingService()
        VectorStoreService()
        system_logger.info("Embedding model + ChromaDB preloaded.")
    except Exception as exc:  # noqa: BLE001
        system_logger.warning("Preload of embedding/vector store failed: %s", exc)

    if settings.OCR_ENABLED:
        try:
            from app.services.ocr_service import OCRService
            OCRService()._get_reader()  # warm up EasyOCR weights
            system_logger.info("EasyOCR reader preloaded.")
        except Exception as exc:  # noqa: BLE001
            system_logger.warning("OCR preload failed (will lazy-load on first use): %s", exc)

    system_logger.info("OCR enabled: %s", settings.OCR_ENABLED)
    yield
    system_logger.info("Medical RAG Engine shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-Powered Medical Assistant — complete backend platform. "
        "Module 1: Medical RAG Engine. Module 2.5: Advanced Medical Intelligence. "
        "Module 3: Medical Report Analyzer. Module 4: JWT Auth & RBAC. "
        "Module 5: Patient Medical History & Dashboard. "
        "Module 6: OCR Medical Report Processing (EasyOCR + Tesseract). "
        "Module 7: Production Deployment (Docker, rate limiting, health checks, connection pooling)."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> Response:
    """Add security headers to every response (Module 7)."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter

# CORS — browsers reject wildcard origin with credentials, so we toggle accordingly.
_cors_origins = settings.cors_origins_list
_allow_credentials = _cors_origins != ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

register_exception_handlers(app)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"status": "error", "message": "Rate limit exceeded. Please slow down."},
    )


app.include_router(health.router)
app.include_router(upload.router)
app.include_router(rag.router)
app.include_router(symptom_checker.router)
app.include_router(report_analysis.router)
app.include_router(ocr_report.router)
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(system.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
