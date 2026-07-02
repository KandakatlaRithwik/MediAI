"""Patient dashboard summary endpoint (Module 5)."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_medical_record_service
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.history import DashboardSummaryResponse
from app.services.medical_record_service import MedicalRecordService
from app.services.role_service import get_current_user, resolve_target_patient

logger = logging.getLogger("history")

router = APIRouter(prefix="/dashboard", tags=["Patient Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get a summary of the patient's reports and symptom checks",
)
async def get_dashboard_summary(
    patient_uuid: Optional[str] = Query(default=None, description="DOCTOR/ADMIN only: view another patient's dashboard."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: MedicalRecordService = Depends(get_medical_record_service),
) -> DashboardSummaryResponse:
    target_patient = resolve_target_patient(patient_uuid, current_user, db)
    logger.info("Dashboard summary requested for patient_id=%s by user_id=%s", target_patient.id, current_user.id)
    return service.get_dashboard_summary(db, target_patient.id)
