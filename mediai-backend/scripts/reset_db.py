"""Drop and recreate all tables — for a truly fresh database.

Usage:
    python -m scripts.reset_db     # WIPES all data, then runs migrations

This is intentionally destructive: it removes ALL users, chat history,
report history, documents, and patient history. Use only in development.
"""
import subprocess
import sys

from app.core.config import get_settings
from app.database.connection import Base, engine
from app.database.models import (  # noqa: F401  - ensure models are registered
    ChatHistory, Document, MedicalReportHistory, PatientHistory, User,
)


def main() -> None:
    settings = get_settings()
    print(f"Resetting database at: {settings.DATABASE_URL}")

    # Drop everything the ORM knows about.
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")

    # Also drop the alembic bookkeeping table so migrations run cleanly.
    with engine.begin() as conn:
        conn.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")

    # Re-apply all migrations from scratch.
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=False,
    )
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("Fresh database ready. No users exist.")


if __name__ == "__main__":
    main()