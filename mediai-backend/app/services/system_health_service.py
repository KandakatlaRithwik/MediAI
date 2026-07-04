"""
System health / status service (Module 7).

Drives GET /system/health and GET /system/status. Each check is isolated
in try/except so a single failing component never prevents the others from
being reported - callers always get a full picture rather than a 500 error.

All checks are synchronous (not async) because the DB, ChromaDB, and OCR
checks use blocking I/O, which would need run_in_executor if truly async;
given these are low-frequency monitoring calls, blocking is acceptable here.
"""

import logging
import time
from typing import Dict

logger = logging.getLogger("system")

STATUS_HEALTHY = "healthy"
STATUS_UNHEALTHY = "unhealthy"
STATUS_DISABLED = "disabled"


class SystemHealthService:
    def check_database(self) -> Dict[str, object]:
        """Ping the configured PostgreSQL database."""
        from app.database.connection import engine

        if engine is None:
            return {"status": STATUS_UNHEALTHY, "detail": "Database engine not initialized."}
        try:
            start = time.monotonic()
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            latency_ms = round((time.monotonic() - start) * 1000, 1)
            return {"status": STATUS_HEALTHY, "latency_ms": latency_ms}
        except Exception as exc:
            logger.error("Database health check failed: %s", exc)
            return {"status": STATUS_UNHEALTHY, "detail": str(exc)}

    def check_chromadb(self) -> Dict[str, object]:
        """Verify ChromaDB persistent client is readable."""
        try:
            from app.rag.vector_store import VectorStoreService
            vss = VectorStoreService()
            count = vss.count()
            return {"status": STATUS_HEALTHY, "documents_indexed": count}
        except Exception as exc:
            logger.error("ChromaDB health check failed: %s", exc)
            return {"status": STATUS_UNHEALTHY, "detail": str(exc)}

    def check_gemini(self) -> Dict[str, object]:
        """Verify Gemini API key is configured (doesn't burn an API call)."""
        from app.core.config import get_settings
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            return {"status": STATUS_UNHEALTHY, "detail": "GEMINI_API_KEY is not configured."}
        if settings.GEMINI_API_KEY == "your_gemini_api_key_here":
            return {"status": STATUS_UNHEALTHY, "detail": "GEMINI_API_KEY is still the placeholder value."}
        return {"status": STATUS_HEALTHY, "model": settings.GEMINI_MODEL_NAME}

    def check_ocr(self) -> Dict[str, object]:
    """
    Lightweight OCR health check.

    Do NOT initialize EasyOCR here.
    The OCR model is loaded lazily when an OCR request is made.
    """

    from app.core.config import get_settings
    import shutil

    settings = get_settings()

    if not settings.OCR_ENABLED:
        return {
            "status": STATUS_DISABLED,
            "detail": "OCR is disabled."
        }

    tesseract_available = shutil.which("tesseract") is not None

    return {
        "status": STATUS_HEALTHY,
        "engine": "EasyOCR (lazy loading)",
        "tesseract": tesseract_available,
        "detail": "OCR model will be loaded on first OCR request."
    }

    def get_full_status(self) -> Dict[str, Dict]:
        """Run all component checks and return a combined status dict."""
        start = time.monotonic()
        status = {
            "database": self.check_database(),
            "chromadb": self.check_chromadb(),
            "gemini": self.check_gemini(),
            "ocr": self.check_ocr(),
        }
        total_ms = round((time.monotonic() - start) * 1000, 1)
        status["_meta"] = {"total_check_ms": total_ms}
        return status

    def is_healthy(self) -> bool:
        """True only when every non-disabled component is healthy."""
        status = self.get_full_status()
        for key, result in status.items():
            if key.startswith("_"):
                continue
            component_status = result.get("status", STATUS_UNHEALTHY)
            if component_status == STATUS_UNHEALTHY:
                return False
        return True
