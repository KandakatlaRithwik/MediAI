"""
Custom exception hierarchy and global FastAPI exception handlers.

Every error path in the application should ultimately surface as one of the
exceptions below (or a FastAPI HTTPException), and every error response sent
to the client follows the same consistent shape:

    {"status": "error", "message": "..."}
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class MedicalAssistantException(Exception):
    """Base class for all domain-level errors raised by this application."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class DocumentProcessingError(MedicalAssistantException):
    """Raised when a document cannot be loaded, parsed, or chunked."""


class EmbeddingGenerationError(MedicalAssistantException):
    """Raised when the embedding model fails to generate vectors."""


class VectorStoreError(MedicalAssistantException):
    """Raised when ChromaDB read/write operations fail."""


class LLMServiceError(MedicalAssistantException):
    """Raised when the Gemini API call fails or returns an invalid response."""


class FileValidationError(MedicalAssistantException):
    """Raised when an uploaded file fails validation (type, size, content)."""


class KnowledgeBaseError(MedicalAssistantException):
    """Raised when the disease knowledge base (app/data/diseases.json) cannot be loaded or is invalid."""


class ReportAnalysisError(MedicalAssistantException):
    """Raised when a medical report cannot be meaningfully analyzed (e.g. no recognizable
    lab parameters were found in the extracted text). Distinct from DocumentProcessingError,
    which covers raw file-reading failures (corrupt/unreadable PDF, etc.)."""


class DatabaseUnavailableError(MedicalAssistantException):
    """Raised when a database-backed feature (auth, history) is used but Postgres
    is unreachable or not configured."""


class AuthenticationError(MedicalAssistantException):
    """Raised for invalid credentials, invalid/expired/malformed tokens, or
    an inactive user attempting to authenticate."""


class AuthorizationError(MedicalAssistantException):
    """Raised when an authenticated user's role does not permit the requested action."""


class UserAlreadyExistsError(MedicalAssistantException):
    """Raised on registration when the email address is already in use."""


class OCRError(MedicalAssistantException):
    """Raised when OCR processing fails to extract any usable text from an image."""


def _error_response(message: str, status_code: int) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI app instance."""

    @app.exception_handler(FileValidationError)
    async def file_validation_handler(request: Request, exc: FileValidationError):
        logger.warning("File validation failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(DocumentProcessingError)
    async def document_processing_handler(request: Request, exc: DocumentProcessingError):
        logger.error("Document processing failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(EmbeddingGenerationError)
    async def embedding_error_handler(request: Request, exc: EmbeddingGenerationError):
        logger.error("Embedding generation failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(VectorStoreError)
    async def vector_store_error_handler(request: Request, exc: VectorStoreError):
        logger.error("Vector store operation failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(KnowledgeBaseError)
    async def knowledge_base_error_handler(request: Request, exc: KnowledgeBaseError):
        logger.error("Knowledge base error: %s", exc.message)
        return _error_response(exc.message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @app.exception_handler(ReportAnalysisError)
    async def report_analysis_error_handler(request: Request, exc: ReportAnalysisError):
        logger.error("Report analysis error: %s", exc.message)
        return _error_response(exc.message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(DatabaseUnavailableError)
    async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError):
        logger.error("Database unavailable: %s", exc.message)
        return _error_response(exc.message, status.HTTP_503_SERVICE_UNAVAILABLE)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        logger.warning("Authentication failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(AuthorizationError)
    async def authorization_error_handler(request: Request, exc: AuthorizationError):
        logger.warning("Authorization denied: %s", exc.message)
        return _error_response(exc.message, status.HTTP_403_FORBIDDEN)

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsError):
        logger.warning("Registration conflict: %s", exc.message)
        return _error_response(exc.message, status.HTTP_409_CONFLICT)

    @app.exception_handler(OCRError)
    async def ocr_error_handler(request: Request, exc: OCRError):
        logger.error("OCR processing failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(LLMServiceError)
    async def llm_error_handler(request: Request, exc: LLMServiceError):
        logger.error("LLM service failed: %s", exc.message)
        return _error_response(exc.message, status.HTTP_503_SERVICE_UNAVAILABLE)

    @app.exception_handler(MedicalAssistantException)
    async def generic_domain_error_handler(request: Request, exc: MedicalAssistantException):
        logger.error("Unhandled domain exception: %s", exc.message)
        return _error_response(exc.message, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning("Request validation failed: %s", exc.errors())
        return _error_response("Invalid request data. Please check the submitted fields.", status.HTTP_422_UNPROCESSABLE_ENTITY)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.warning("HTTP exception: %s - %s", exc.status_code, exc.detail)
        return _error_response(str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response("An unexpected error occurred. Please try again later.", status.HTTP_500_INTERNAL_SERVER_ERROR)
