"""
PostgreSQL connection setup.

Module 1 (the RAG engine) does not require a relational database to function
-- ChromaDB is the source of truth for document chunks and embeddings.
Module 4 (Authentication) and Module 5 (Patient History) DO require it -
they are the first features that genuinely need persistent relational
storage.

The engine is still created lazily and defensively: if the database is
unreachable or misconfigured, the RAG/symptom-checker/report-analyzer
features keep working exactly as before (history-saving on those endpoints
is best-effort and skipped, not blocking); only Module 4/5 endpoints that
actually call `get_db()` will return a clear 503 via DatabaseUnavailableError.
"""

import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

Base = declarative_base()

settings = get_settings()

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,   # test connections before use — handles stale connections
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=1800,    # recycle connections after 30 min to avoid server-side timeouts
        future=True,
    )
    # expire_on_commit=False: by default, SQLAlchemy expires all attributes
    # on commit/close, requiring a live session to re-fetch them on next
    # access. This app's auth pattern resolves a User in one short-lived
    # session (get_optional_current_user) and then passes that object on to
    # several independent best-effort operations (history saving, RAG
    # context loading) that each open their own session - so the User
    # object must remain safely readable (id, uuid, role, etc.) after its
    # original session has closed, or every one of those call sites raises
    # DetachedInstanceError.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True, expire_on_commit=False)
except Exception as exc:  # pragma: no cover - defensive, env-dependent
    logger.warning("Could not initialize database engine (this is fine for Module 1): %s", exc)
    engine = None
    SessionLocal = None


def get_db():
    """FastAPI dependency yielding a SQLAlchemy session.

    Used by database-backed modules (Module 4 auth, Module 5 history).
    Raises DatabaseUnavailableError - not a bare RuntimeError - if a route
    tries to use it without a configured/reachable database, so it gets the
    same consistent {"status": "error", "message": ...} response shape as
    every other failure mode in this app via the global exception handler.
    """
    from app.core.exceptions import DatabaseUnavailableError  # local import: avoids a circular import

    if SessionLocal is None:
        raise DatabaseUnavailableError(
            "This feature requires a database connection, which is not currently available."
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all tables registered on `Base`.

    Not called automatically on startup (Module 1 does not need it). Future
    modules should call this explicitly once their models are defined, or
    manage schema via migrations (e.g. Alembic) in production.
    """
    if engine is None:
        logger.warning("Skipping init_db(): no database engine available.")
        return
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized.")


def get_db_session_or_none():
    """Return a new SQLAlchemy session, or None if the database is
    unavailable. Used for best-effort writes (e.g. automatic history
    saving on /ask, /symptom-checker, /analyze-report) that must never
    raise just because Postgres happens to be down - unlike `get_db()`,
    which intentionally raises for routes that genuinely require the
    database to function at all."""
    if SessionLocal is None:
        return None
    return SessionLocal()
