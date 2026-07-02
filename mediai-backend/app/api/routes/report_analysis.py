"""
Medical Report Analyzer endpoint (Module 3).

Workflow: validate -> save to disk -> extract -> parse -> compare against
reference ranges -> assess risk -> AI explanation -> respond. Mirrors the
validate/save/process structure of app.api.routes.upload for consistency.

Module 5: if the caller is authenticated, the result is automatically saved
to their report history. Fully optional and best-effort, same pattern as
app.api.routes.symptom_checker.
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_history_service, get_report_analysis_service
from app.core.config import get_settings
from app.core.exceptions import DocumentProcessingError, FileValidationError, ReportAnalysisError
from app.core.security import sanitize_filename, validate_file_extension, validate_file_size
from app.database.connection import get_db_session_or_none
from app.database.models.user import User
from app.schemas.report_response import ReportAnalysisResponse
from app.services.history_service import HistoryService
from app.services.report_analysis_service import ReportAnalysisService
from app.services.role_service import get_optional_current_user

logger = logging.getLogger("report_analysis")

router = APIRouter(tags=["Medical Report Analyzer"])


def _save_report_history_best_effort(
    history_service: HistoryService, current_user: Optional[User], response: ReportAnalysisResponse
) -> None:
    if current_user is None:
        return
    db = get_db_session_or_none()
    if db is None:
        return
    try:
        history_service.save_report_history(
            db,
            patient_id=current_user.id,
            report_type=response.report_type,
            report_summary=response.ai_summary,
            risk_assessment=response.risk_assessment,
        )
    except Exception as exc:  # noqa: BLE001 - history saving must never break the endpoint
        logger.error("Failed to save report history for user_id=%s: %s", current_user.id, exc)
    finally:
        db.close()


@router.post(
    "/analyze-report",
    response_model=ReportAnalysisResponse,
    summary="Analyze a medical lab report (PDF or TXT)",
    description=(
        "Upload a lab report (CBC, Blood Sugar, Lipid Profile, Thyroid Profile, Kidney Function "
        "Test, or Liver Function Test) and receive parameter extraction, normal-range comparison, "
        "abnormal value detection, risk assessment, and a plain-English AI explanation. "
        "Image-based reports are not yet supported (future-ready). "
        "This endpoint never returns a definitive diagnosis or medication advice. If called with "
        "a valid Bearer token, the result is automatically saved to the caller's report history."
    ),
)
async def analyze_report(
    file: UploadFile = File(..., description="PDF or TXT medical lab report to analyze"),
    service: ReportAnalysisService = Depends(get_report_analysis_service),
    history_service: HistoryService = Depends(get_history_service),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> ReportAnalysisResponse:
    settings = get_settings()

    # 1. Validate extension up front (cheap, fails fast without reading the file).
    validate_file_extension(file.filename)

    # 2. Read and validate size/content.
    contents = await file.read()
    validate_file_size(len(contents))

    # 3. Sanitize filename and persist to disk.
    safe_filename = sanitize_filename(file.filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as out_file:
            out_file.write(contents)
    except OSError as exc:
        logger.error("Failed to save uploaded report '%s': %s", safe_filename, exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded report.") from exc

    logger.info("Saved report upload '%s' (%d bytes) to %s", safe_filename, len(contents), file_path)

    # 4. Run the analysis pipeline (extract -> parse -> compare -> assess risk -> explain).
    try:
        response = service.analyze_report(file_path, safe_filename)
    except (DocumentProcessingError, FileValidationError, ReportAnalysisError):
        # Clean up the saved file if analysis failed, so we don't keep
        # unusable files around indefinitely (mirrors upload.py's behavior).
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    _save_report_history_best_effort(history_service, current_user, response)
    return response
