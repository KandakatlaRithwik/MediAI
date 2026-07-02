"""Health check endpoint."""

from fastapi import APIRouter

from app.schemas.response import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
def health_check() -> HealthResponse:
    """Lightweight liveness check used by orchestrators/load balancers."""
    return HealthResponse(status="running", service="medical-rag")
