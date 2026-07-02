"""
SQLAlchemy ORM models package.

Split into one module per logical group (document, user, history) for
clarity as the schema has grown. Everything is re-exported here so existing
code (`from app.database.models import Document`) keeps working unchanged.
"""

from app.database.models.document import Document
from app.database.models.history import ChatHistory, MedicalReportHistory, PatientHistory
from app.database.models.user import User, UserRole

__all__ = [
    "Document",
    "User",
    "UserRole",
    "PatientHistory",
    "MedicalReportHistory",
    "ChatHistory",
]
