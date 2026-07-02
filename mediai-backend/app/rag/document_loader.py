"""
Document loading utilities.

Converts raw uploaded files (PDF, TXT) into LangChain `Document` objects
ready for chunking. Each loader function is isolated and reusable so new
formats can be added later (e.g. DOCX) without touching the rest of the
pipeline.
"""

import logging
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document as LCDocument

from app.core.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


def load_pdf(file_path: str) -> List[LCDocument]:
    """Load a PDF file into a list of LangChain Documents (one per page)."""
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
    except DocumentProcessingError:
        raise
    except Exception as exc:
        logger.error("Failed to load PDF '%s': %s", file_path, exc)
        raise DocumentProcessingError(f"Failed to read PDF file: {exc}") from exc

    if not documents or not any(doc.page_content.strip() for doc in documents):
        raise DocumentProcessingError(
            "No extractable text found in PDF. It may be a scanned/image-only document."
        )

    logger.info("Loaded %d page(s) from PDF '%s'", len(documents), file_path)
    return documents


def load_txt(file_path: str) -> List[LCDocument]:
    """Load a plain-text file into a single-element list of LangChain Documents."""
    try:
        loader = TextLoader(file_path, encoding="utf-8")
        documents = loader.load()
    except DocumentProcessingError:
        raise
    except Exception as exc:
        logger.error("Failed to load text file '%s': %s", file_path, exc)
        raise DocumentProcessingError(f"Failed to read text file: {exc}") from exc

    if not documents or not documents[0].page_content.strip():
        raise DocumentProcessingError("The uploaded text file is empty or unreadable.")

    logger.info("Loaded text file '%s' (%d chars)", file_path, len(documents[0].page_content))
    return documents


def load_document(file_path: str) -> List[LCDocument]:
    """Dispatch to the correct loader based on file extension."""
    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return load_pdf(file_path)
    if extension == ".txt":
        return load_txt(file_path)

    raise DocumentProcessingError(f"Unsupported file extension for loading: '{extension}'.")
