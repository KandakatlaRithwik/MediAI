"""
HistoryService - persistence layer for patient history (Module 5).

Pure CRUD against the three history tables (PatientHistory,
MedicalReportHistory, ChatHistory). Like AuthService, methods accept a
per-request SQLAlchemy `Session` rather than holding one in `__init__`.

Save calls are designed to be wrapped in try/except by callers (see the
modified /ask, /symptom-checker, /analyze-report routes) so that a history
write failure never breaks the underlying feature it's recording - history
is an audit trail, not a dependency those features should fail without.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.database.models.history import ChatHistory, MedicalReportHistory, PatientHistory
from app.schemas.disease import PossibleDisease
from app.schemas.report_response import RiskAssessment

logger = logging.getLogger("history")

_DEFAULT_HISTORY_LIMIT = 50


class HistoryService:
    # --- Writes ---

    def save_symptom_history(
        self,
        db: Session,
        patient_id: int,
        symptoms: List[str],
        predicted_diseases: List[PossibleDisease],
        severity: str,
        emergency_status: bool,
    ) -> PatientHistory:
        entry = PatientHistory(
            patient_id=patient_id,
            symptoms=symptoms,
            predicted_diseases=[disease.model_dump() for disease in predicted_diseases],
            severity=severity,
            emergency_status=emergency_status,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info("Saved symptom history for patient_id=%s severity=%s", patient_id, severity)
        return entry

    def save_report_history(
        self,
        db: Session,
        patient_id: int,
        report_type: str,
        report_summary: str,
        risk_assessment: List[RiskAssessment],
    ) -> MedicalReportHistory:
        entry = MedicalReportHistory(
            patient_id=patient_id,
            report_type=report_type,
            report_summary=report_summary,
            risk_assessment=[risk.model_dump() for risk in risk_assessment],
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info("Saved report history for patient_id=%s report_type=%s", patient_id, report_type)
        return entry

    def save_chat_history(self, db: Session, patient_id: int, question: str, response: str) -> ChatHistory:
        entry = ChatHistory(patient_id=patient_id, question=question, response=response)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        logger.info("Saved chat history for patient_id=%s", patient_id)
        return entry

    # --- Reads (most recent first) ---

    def get_symptom_history(self, db: Session, patient_id: int, limit: int = _DEFAULT_HISTORY_LIMIT) -> List[PatientHistory]:
        return (
            db.query(PatientHistory)
            .filter(PatientHistory.patient_id == patient_id)
            .order_by(PatientHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_report_history(self, db: Session, patient_id: int, limit: int = _DEFAULT_HISTORY_LIMIT) -> List[MedicalReportHistory]:
        return (
            db.query(MedicalReportHistory)
            .filter(MedicalReportHistory.patient_id == patient_id)
            .order_by(MedicalReportHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_chat_history(self, db: Session, patient_id: int, limit: int = _DEFAULT_HISTORY_LIMIT) -> List[ChatHistory]:
        return (
            db.query(ChatHistory)
            .filter(ChatHistory.patient_id == patient_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
            .all()
        )
