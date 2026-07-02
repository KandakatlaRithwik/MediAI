"""Response schemas shared across API routes."""

from typing import List

from pydantic import BaseModel, Field

from app.schemas.disease import PossibleDisease


class HealthResponse(BaseModel):
    status: str
    service: str


class UploadResponse(BaseModel):
    status: str
    document: str
    chunks_stored: int


class AskResponse(BaseModel):
    answer: str
    sources: List[str]
    detected_symptoms: List[str] = Field(
        default_factory=list,
        description="Symptoms detected in the question, if any (Module 2 symptom-aware RAG).",
    )
    possible_diseases: List[PossibleDisease] = Field(
        default_factory=list,
        description="Disease predictions injected into the answer's context, if symptoms were detected.",
    )


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
