"""
MedicalRecordService - dashboard analytics orchestration (Module 5).

Aggregates counts/stats across a patient's medical_report_history and
patient_history rows for the GET /dashboard/summary endpoint.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.database.models.history import MedicalReportHistory, PatientHistory
from app.schemas.history import DashboardSummaryResponse

logger = logging.getLogger("history")

_HIGH_SEVERITY = "High"


def _has_high_risk(report: MedicalReportHistory) -> bool:
    risks: List[dict] = report.risk_assessment or []
    return any(risk.get("severity") == _HIGH_SEVERITY for risk in risks)


class MedicalRecordService:
    def get_dashboard_summary(self, db: Session, patient_id: int) -> DashboardSummaryResponse:
        total_symptom_checks = (
            db.query(PatientHistory).filter(PatientHistory.patient_id == patient_id).count()
        )

        report_entries = (
            db.query(MedicalReportHistory)
            .filter(MedicalReportHistory.patient_id == patient_id)
            .order_by(MedicalReportHistory.created_at.desc())
            .all()
        )
        total_reports = len(report_entries)
        high_risk_reports = sum(1 for report in report_entries if _has_high_risk(report))
        last_report_date = report_entries[0].created_at if report_entries else None

        logger.info(
            "Dashboard summary for patient_id=%s: reports=%d symptom_checks=%d high_risk=%d",
            patient_id, total_reports, total_symptom_checks, high_risk_reports,
        )

        return DashboardSummaryResponse(
            total_reports=total_reports,
            total_symptom_checks=total_symptom_checks,
            high_risk_reports=high_risk_reports,
            last_report_date=last_report_date,
        )
