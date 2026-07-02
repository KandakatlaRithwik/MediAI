"""
System health and status endpoints (Module 7).

GET /system/health  — detailed per-component health with latencies.
GET /system/status  — concise status map matching the spec's exact shape.

Both endpoints are intentionally unauthenticated (monitoring tools need to
reach them without a token) but production deployments should add IP
allowlisting at the reverse proxy level.
"""

import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_system_health_service
from app.core.config import get_settings
from app.schemas.system import SystemHealthResponse, SystemStatusResponse
from app.services.system_health_service import SystemHealthService

logger = logging.getLogger("system")

router = APIRouter(prefix="/system", tags=["System Health"])


@router.get(
    "/health",
    response_model=SystemHealthResponse,
    summary="Detailed per-component health check",
    description="Checks Database, ChromaDB, Gemini API key, and OCR availability. Returns latencies and error details.",
)
async def system_health(service: SystemHealthService = Depends(get_system_health_service)) -> SystemHealthResponse:
    logger.info("System health check requested.")
    full_status = service.get_full_status()
    overall = "healthy" if service.is_healthy() else "degraded"

    return SystemHealthResponse(
        overall=overall,
        database=full_status.get("database", {}),
        chromadb=full_status.get("chromadb", {}),
        gemini=full_status.get("gemini", {}),
        ocr=full_status.get("ocr", {}),
        version=get_settings().APP_VERSION,
    )


@router.get(
    "/status",
    response_model=SystemStatusResponse,
    summary="Concise status map for each component",
    description="Returns a simple healthy/unhealthy/disabled label per component.",
)
async def system_status(service: SystemHealthService = Depends(get_system_health_service)) -> SystemStatusResponse:
    logger.info("System status check requested.")
    full_status = service.get_full_status()

    return SystemStatusResponse(
        database=full_status.get("database", {}).get("status", "unhealthy"),
        chromadb=full_status.get("chromadb", {}).get("status", "unhealthy"),
        gemini=full_status.get("gemini", {}).get("status", "unhealthy"),
        ocr=full_status.get("ocr", {}).get("status", "unhealthy"),
    )
