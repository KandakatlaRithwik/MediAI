"""
File-upload security helpers: extension validation, size limits, content
sanity checks, and filename sanitization.

Keeping these as small pure functions makes them trivially unit-testable and
reusable from any route or service that needs to accept untrusted file input.
"""

import os
import re
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings
from app.core.exceptions import FileValidationError


def validate_file_extension(filename: str) -> str:
    """Validate the file extension against the configured allow-list.

    Returns the lowercase extension (e.g. ".pdf") on success.
    """
    if not filename:
        raise FileValidationError("No filename was provided.")

    settings = get_settings()
    extension = Path(filename).suffix.lower()

    if extension not in settings.allowed_extensions_list:
        allowed = ", ".join(settings.allowed_extensions_list)
        raise FileValidationError(
            f"Unsupported file format '{extension}'. Allowed formats: {allowed}."
        )
    return extension


def validate_file_size(size_in_bytes: int) -> None:
    """Validate that the uploaded file is non-empty and within the size limit."""
    settings = get_settings()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if size_in_bytes <= 0:
        raise FileValidationError("Uploaded file is empty.")

    if size_in_bytes > max_bytes:
        raise FileValidationError(
            f"File exceeds the maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB."
        )


def sanitize_filename(filename: str) -> str:
    """Strip directory components and unsafe characters, and append a short
    unique suffix so concurrent uploads of files with the same name never
    collide on disk.
    """
    base_name = os.path.basename(filename)
    name, extension = os.path.splitext(base_name)

    # Keep only alphanumerics, dot, dash and underscore.
    safe_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", name).strip("_") or "document"
    unique_suffix = uuid4().hex[:8]

    return f"{safe_name}_{unique_suffix}{extension.lower()}"
