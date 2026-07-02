"""
Patient history endpoints (Module 5).

All endpoints require authentication. By default they return the current
user's own history; DOCTOR/ADMIN may pass `patient_uuid` to view another
patient's records (see role_service.resolve_target_patient for the exact
access rules).
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_history_service, get_patient_service
from app.database.connection import get_db
from app.database.models.user import User
from app.schemas.history import ChatHistoryEntry, FullProfileResponse, ReportHistoryEntry, SymptomHistoryEntry
from app.services.history_service import HistoryService
from app.services.patient_service import PatientService
from app.services.role_service import get_current_user, resolve_target_patient

logger = logging.getLogger("history")

router = APIRouter(prefix="/history", tags=["Patient History"])


@router.get("/symptoms", response_model=List[SymptomHistoryEntry], summary="Get symptom-checker history")
async def get_symptom_history(
    patient_uuid: Optional[str] = Query(default=None, description="DOCTOR/ADMIN only: view another patient's history."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: HistoryService = Depends(get_history_service),
) -> List[SymptomHistoryEntry]:
    target_patient = resolve_target_patient(patient_uuid, current_user, db)
    entries = service.get_symptom_history(db, target_patient.id)
    return [SymptomHistoryEntry.model_validate(entry) for entry in entries]


@router.get("/reports", response_model=List[ReportHistoryEntry], summary="Get report-analysis history")
async def get_report_history(
    patient_uuid: Optional[str] = Query(default=None, description="DOCTOR/ADMIN only: view another patient's history."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: HistoryService = Depends(get_history_service),
) -> List[ReportHistoryEntry]:
    target_patient = resolve_target_patient(patient_uuid, current_user, db)
    entries = service.get_report_history(db, target_patient.id)
    return [ReportHistoryEntry.model_validate(entry) for entry in entries]


@router.get("/chat", response_model=List[ChatHistoryEntry], summary="Get /ask question-and-answer history")
async def get_chat_history(
    patient_uuid: Optional[str] = Query(default=None, description="DOCTOR/ADMIN only: view another patient's history."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: HistoryService = Depends(get_history_service),
) -> List[ChatHistoryEntry]:
    target_patient = resolve_target_patient(patient_uuid, current_user, db)
    entries = service.get_chat_history(db, target_patient.id)
    return [ChatHistoryEntry.model_validate(entry) for entry in entries]


@router.get(
    "/full-profile",
    response_model=FullProfileResponse,
    summary="Get the combined patient profile: info + all history types",
)
async def get_full_profile(
    patient_uuid: Optional[str] = Query(default=None, description="DOCTOR/ADMIN only: view another patient's profile."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: PatientService = Depends(get_patient_service),
) -> FullProfileResponse:
    target_patient = resolve_target_patient(patient_uuid, current_user, db)
    return service.get_full_profile(db, target_patient)
