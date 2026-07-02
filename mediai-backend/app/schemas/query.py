"""Request schemas for the RAG query (/ask) endpoint."""

from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="The medical question to ask the assistant.",
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=20,
        description="Optional override for the number of context chunks to retrieve.",
    )
    source_filter: Optional[str] = Field(
        default=None,
        description="Optional document filename to restrict retrieval to a single source.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"question": "What are the symptoms of diabetes?"}
        }
    }
