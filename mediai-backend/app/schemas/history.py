"""Request/response schemas for patient history & dashboard (Module 5)."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.auth import UserProfileResponse
from app.schemas.disease import PossibleDisease
from app.schemas.report_response import RiskAssessment


class SymptomHistoryEntry(BaseModel):
    id: int
    symptoms: List[str]
    predicted_diseases: List[PossibleDisease]
    severity: str
    emergency_status: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportHistoryEntry(BaseModel):
    id: int
    report_type: str
    report_summary: str
    risk_assessment: List[RiskAssessment]
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryEntry(BaseModel):
    id: int
    question: str
    response: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FullProfileResponse(BaseModel):
    patient_info: UserProfileResponse
    symptom_history: List[SymptomHistoryEntry] = Field(default_factory=list)
    report_history: List[ReportHistoryEntry] = Field(default_factory=list)
    chat_history: List[ChatHistoryEntry] = Field(default_factory=list)


class DashboardSummaryResponse(BaseModel):
    total_reports: int
    total_symptom_checks: int
    high_risk_reports: int
    last_report_date: Optional[datetime] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "total_reports": 10,
                "total_symptom_checks": 24,
                "high_risk_reports": 2,
                "last_report_date": "2026-06-20T10:00:00Z",
            }
        }
    }
