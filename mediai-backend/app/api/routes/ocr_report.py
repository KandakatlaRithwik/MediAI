"""
OCR Medical Report Analysis endpoint (Module 6).

Accepts JPG/JPEG/PNG images and scanned PDFs, preprocesses them with
OpenCV, extracts text via EasyOCR (Tesseract fallback), then runs the
same Module 3 analysis pipeline as /analyze-report.

File validation reuses the existing security utilities but with an expanded
extension whitelist that includes image types.
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_history_service, get_report_image_parser_service
from app.core.config import get_settings
from app.core.constants import OCR_SUPPORTED_IMAGE_EXTENSIONS
from app.core.exceptions import DocumentProcessingError, OCRError
from app.core.security import sanitize_filename, validate_file_size
from app.database.connection import get_db_session_or_none
from app.database.models.user import User
from app.schemas.ocr_report import OCRReportResponse
from app.services.history_service import HistoryService
from app.services.report_image_parser_service import ReportImageParserService
from app.services.role_service import get_optional_current_user

logger = logging.getLogger("ocr")

router = APIRouter(tags=["OCR Medical Report Analyzer"])

# All file extensions accepted at this endpoint.
_ACCEPTED_EXTENSIONS = OCR_SUPPORTED_IMAGE_EXTENSIONS | {".pdf", ".txt"}


def _validate_ocr_extension(filename: str) -> None:
    from pathlib import Path
    ext = Path(filename).suffix.lower()
    if ext not in _ACCEPTED_EXTENSIONS:
        from app.core.exceptions import FileValidationError
        raise FileValidationError(
            f"Unsupported file type '{ext}' for image report analysis. "
            f"Accepted: {sorted(_ACCEPTED_EXTENSIONS)}"
        )


def _save_report_history_best_effort(
    history_service: HistoryService, current_user: Optional[User], result
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
            report_type=result.analysis.report_type,
            report_summary=result.analysis.ai_summary,
            risk_assessment=result.analysis.risk_assessment,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to save OCR report history for user_id=%s: %s", current_user.id, exc)
    finally:
        db.close()


@router.post(
    "/analyze-image-report",
    response_model=OCRReportResponse,
    summary="Analyze a scanned/photographed medical report (OCR)",
    description=(
        "Upload a JPG, JPEG, PNG image or scanned PDF of a lab report. The image is preprocessed "
        "(grayscale, denoising, contrast enhancement, thresholding) and processed through EasyOCR "
        "(Tesseract fallback) before running the same analysis pipeline as /analyze-report. "
        "Returns OCR text, confidence score, parameter extraction, risk assessment, and AI explanation. "
        "If called with a valid Bearer token, the result is saved to the caller's report history."
    ),
)
async def analyze_image_report(
    file: UploadFile = File(..., description="JPG/JPEG/PNG image or scanned PDF of a lab report"),
    service: ReportImageParserService = Depends(get_report_image_parser_service),
    history_service: HistoryService = Depends(get_history_service),
    current_user: Optional[User] = Depends(get_optional_current_user),
) -> OCRReportResponse:
    settings = get_settings()

    _validate_ocr_extension(file.filename)
    contents = await file.read()
    validate_file_size(len(contents))

    safe_filename = sanitize_filename(file.filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    try:
        with open(file_path, "wb") as out_file:
            out_file.write(contents)
    except OSError as exc:
        logger.error("Failed to save uploaded image report '%s': %s", safe_filename, exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.") from exc

    logger.info("Saved OCR report upload '%s' (%d bytes)", safe_filename, len(contents))

    try:
        result = service.parse_image_report(file_path, safe_filename)
    except (OCRError, DocumentProcessingError):
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    _save_report_history_best_effort(history_service, current_user, result)

    return OCRReportResponse(
        ocr_text=result.ocr_text,
        ocr_confidence=result.ocr_confidence,
        report_type=result.analysis.report_type,
        parameters=result.analysis.parameters,
        abnormal_parameters=result.analysis.abnormal_parameters,
        risk_assessment=result.analysis.risk_assessment,
        ai_summary=result.analysis.ai_summary,
        disclaimer=result.analysis.disclaimer,
    )
