"""
Document metadata model (Module 1).

Tracks metadata about ingested files for reporting/auditing purposes. It is
intentionally separate from ChromaDB, which remains the source of truth for
retrieval. Writing here is best-effort: if Postgres is unavailable,
ingestion into ChromaDB still succeeds (see app/api/routes/upload.py).
"""

from sqlalchemy import Column, DateTime, Integer, String, func

from app.database.connection import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, nullable=False, index=True)
    content_type = Column(String(50), nullable=False)
    chunks_count = Column(Integer, default=0, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<Document id={self.id} filename={self.filename!r} chunks={self.chunks_count}>"
