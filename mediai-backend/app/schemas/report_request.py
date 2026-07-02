"""Request schema for the Medical Report Analyzer endpoint.

The actual upload is multipart/form-data (a file), so this schema documents
the one optional accompanying form field rather than the request body
itself - FastAPI's Swagger UI still renders it correctly via Form().
"""

from typing import Optional

from pydantic import BaseModel, Field


class ReportAnalysisRequest(BaseModel):
    report_type_hint: Optional[str] = Field(
        default=None,
        description=(
            "Optional hint for the report type (e.g. 'Blood Sugar', 'CBC'). "
            "If omitted, the report type is inferred automatically from whichever "
            "parameters are detected in the document."
        ),
    )

    model_config = {
        "json_schema_extra": {"example": {"report_type_hint": "Blood Sugar"}}
    }
