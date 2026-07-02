"""
PatientService - patient profile orchestration (Module 5).

Composes HistoryService's three read methods into the combined
full-profile view. Mirrors the orchestrator pattern used by RAGService /
SymptomCheckerService / ReportAnalysisService elsewhere in this codebase.
"""

import logging

from sqlalchemy.orm import Session

from app.database.models.user import User
from app.schemas.auth import UserProfileResponse
from app.schemas.history import ChatHistoryEntry, FullProfileResponse, ReportHistoryEntry, SymptomHistoryEntry
from app.services.history_service import HistoryService

logger = logging.getLogger("history")


class PatientService:
    def __init__(self) -> None:
        self._history_service = HistoryService()

    def get_full_profile(self, db: Session, patient: User) -> FullProfileResponse:
        symptom_entries = self._history_service.get_symptom_history(db, patient.id)
        report_entries = self._history_service.get_report_history(db, patient.id)
        chat_entries = self._history_service.get_chat_history(db, patient.id)

        logger.info(
            "Built full profile for patient_id=%s: %d symptom, %d report, %d chat entries",
            patient.id, len(symptom_entries), len(report_entries), len(chat_entries),
        )

        return FullProfileResponse(
            patient_info=UserProfileResponse.model_validate(patient),
            symptom_history=[SymptomHistoryEntry.model_validate(entry) for entry in symptom_entries],
            report_history=[ReportHistoryEntry.model_validate(entry) for entry in report_entries],
            chat_history=[ChatHistoryEntry.model_validate(entry) for entry in chat_entries],
        )
