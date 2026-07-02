"""Response schemas for GET /system/health and GET /system/status (Module 7)."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    status: str = Field(..., description="'healthy', 'unhealthy', or 'disabled'.")
    detail: Optional[str] = Field(default=None, description="Error detail when unhealthy.")
    latency_ms: Optional[float] = Field(default=None, description="Latency for DB ping, if applicable.")
    documents_indexed: Optional[int] = Field(default=None, description="ChromaDB document count, if healthy.")
    model: Optional[str] = Field(default=None, description="Gemini model name, if configured.")


class SystemStatusResponse(BaseModel):
    database: str = Field(..., description="'healthy' or 'unhealthy'.")
    chromadb: str = Field(..., description="'healthy' or 'unhealthy'.")
    gemini: str = Field(..., description="'healthy' or 'unhealthy'.")
    ocr: str = Field(..., description="'healthy', 'unhealthy', or 'disabled'.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "database": "healthy",
                "chromadb": "healthy",
                "gemini": "healthy",
                "ocr": "healthy",
            }
        }
    }


class SystemHealthResponse(BaseModel):
    overall: str = Field(..., description="'healthy' if all non-disabled components are healthy, else 'degraded'.")
    database: Dict[str, Any] = Field(default_factory=dict)
    chromadb: Dict[str, Any] = Field(default_factory=dict)
    gemini: Dict[str, Any] = Field(default_factory=dict)
    ocr: Dict[str, Any] = Field(default_factory=dict)
    version: str = Field(..., description="Application version.")
