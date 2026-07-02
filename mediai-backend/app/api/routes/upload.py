"""
Document upload & ingestion endpoint.

Workflow: validate -> save to disk -> ingest (load, chunk, embed, store in
ChromaDB) -> best-effort metadata write to Postgres -> respond.
"""

import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_rag_service
from app.core.config import get_settings
from app.core.exceptions import DocumentProcessingError, FileValidationError
from app.core.security import sanitize_filename, validate_file_extension, validate_file_size
from app.schemas.response import UploadResponse
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Document Ingestion"])


def _persist_document_metadata(filename: str, content_type: str, chunks_count: int) -> None:
    """Best-effort write of upload metadata to Postgres.

    This is "future-ready" plumbing for modules like a dashboard/history
    view. ChromaDB remains the source of truth for Module 1, so a failure
    here (e.g. Postgres not running yet) must never break the upload.
    """
    try:
        from app.database.connection import SessionLocal
        from app.database.models import Document

        if SessionLocal is None:
            return

        db = SessionLocal()
        try:
            db.add(Document(filename=filename, content_type=content_type, chunks_count=chunks_count))
            db.commit()
        finally:
            db.close()
    except Exception as exc:
        logger.warning("Could not persist document metadata to database (non-fatal): %s", exc)


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a medical document (PDF or TXT)",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF or TXT medical document to ingest"),
    rag_service: RAGService = Depends(get_rag_service),
) -> UploadResponse:
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
        logger.error("Failed to save uploaded file '%s': %s", safe_filename, exc)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.") from exc

    logger.info("Saved upload '%s' (%d bytes) to %s", safe_filename, len(contents), file_path)

    # 4. Run the ingestion pipeline (load -> chunk -> embed -> store).
    try:
        chunks_stored = rag_service.ingest_document(file_path, safe_filename)
    except (DocumentProcessingError, FileValidationError):
        # Clean up the saved file if ingestion failed, so we don't keep
        # unusable files around indefinitely.
        if os.path.exists(file_path):
            os.remove(file_path)
        raise

    # 5. Best-effort metadata write (never blocks the response).
    _persist_document_metadata(
        filename=safe_filename,
        content_type=file.content_type or "application/octet-stream",
        chunks_count=chunks_stored,
    )

    return UploadResponse(status="success", document=safe_filename, chunks_stored=chunks_stored)
