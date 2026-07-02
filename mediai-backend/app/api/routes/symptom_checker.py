"""
Symptom Checker endpoint.

Extracts symptoms from free-text input, matches them against the disease
knowledge base, scores confidence per match, and recommends a specialist.
This is a screening aid, not a diagnostic tool - see SymptomCheckerResponse
for the mandatory safety disclaimer included on every response.

Module 5: if the caller is authenticated, the result is automatically saved
to their symptom history. This is fully optional and best-effort - an
anonymous call, or a history-save failure, never affects the response
returned to the caller (see role_service.get_optional_current_user and
database.connection.get_db_session_or_none).
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends

from app.api.deps import get_history_service, get_symptom_checker_service
from app.database.connection import get_db_session_or_none
from app.database.models.user import User
from app.schemas.symptom import SymptomCheckerResponse, SymptomCheckRequest
from app.services.history_service import HistoryService
from app.services.role_service import get_optional_current_user
from app.services.symptom_checker_service import SymptomCheckerService

logger = logging.getLogger("history")

router = APIRouter(tags=["Symptom Checker"])


def _save_symptom_history_best_effort(
    history_service: HistoryService, current_user: Optional[User], response: SymptomCheckerResponse
) -> None:
    if current_user is None:
        return
    db = get_db_session_or_none()
    if db is None:
        return
    try:
        history_service.save_symptom_history(
            db,
            patient_id=current_user.id,
            symptoms=response.symptoms,
            predicted_diseases=response.possible_diseases,
            severity=response.severity,
            emergency_status=response.emergency,
        )
    except Exception as exc:  # noqa: BLE001 - history saving must never break the endpoint
        logger.error("Failed to save symptom history for user_id=%s: %s", current_user.id, exc)
    finally:
        db.close()


@router.post(
    "/symptom-checker",
    response_model=SymptomCheckerResponse,
    summary="Analyze free-text symptoms: disease prediction, severity, and emergency detection",
    description=(
        "Extracts known symptoms from free-text input, runs emergency detection, ranks candidate "
        "diseases using Jaccard similarity, predicts an overall severity level (Mild/Moderate/Severe/"
        "Emergency), explains the leading prediction, and recommends a specialist. "
        "This endpoint never returns a definitive diagnosis or medication advice - it is a "
        "decision-support screening aid only. If called with a valid Bearer token, the result is "
        "automatically saved to the caller's symptom history."
    ),
)
async def check_symptoms(
    request: SymptomCheckRequest,
    service: SymptomCheckerService = Depends(get_symptom_checker_service),
    history_service: HistoryService = Depends(get_history_service),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> SymptomCheckerResponse:
    logger.info("Received symptom-checker request (%d chars)", len(request.text))
    response = service.check(request.text)
    _save_symptom_history_best_effort(history_service, current_user, response)
    return response
