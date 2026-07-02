"""
Shared pytest fixtures.

Tests run against a `TestClient` with `get_rag_service` overridden by a
fake, in-memory RAGService double. This keeps the test suite fast and fully
offline: no embedding model download, no ChromaDB disk writes, no real
Gemini API calls. Each test gets a fresh app instance via the `client`
fixture so overrides never leak between tests.
"""

from typing import List, Optional

import pytest
from fastapi.testclient import TestClient

from app.core.constants import NO_CONTEXT_MESSAGE
from app.schemas.response import AskResponse


class FakeRAGService:
    """In-memory double for RAGService, used to isolate route-level tests
    from the real ML/vector-store/LLM stack."""

    def __init__(self) -> None:
        self.ingested_documents: dict = {}

    def ingest_document(self, file_path: str, filename: str) -> int:
        # Pretend every ingested document produces 3 chunks.
        self.ingested_documents[filename] = 3
        return 3

    def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None,
        current_user=None,
    ) -> AskResponse:
        if not self.ingested_documents:
            return AskResponse(answer=NO_CONTEXT_MESSAGE, sources=[])
        return AskResponse(
            answer=f"Stub answer for: {question}",
            sources=sorted(self.ingested_documents.keys()),
        )


@pytest.fixture()
def fake_rag_service() -> FakeRAGService:
    return FakeRAGService()


@pytest.fixture()
def client(fake_rag_service: FakeRAGService) -> TestClient:
    from main import app
    from app.api.deps import get_rag_service

    app.dependency_overrides[get_rag_service] = lambda: fake_rag_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session():
    """A real SQLAlchemy session against the configured Postgres database,
    used by Module 4/5 tests. Cleans all auth/history tables before
    yielding, so each test starts from a known-empty state regardless of
    execution order."""
    from app.database.connection import SessionLocal
    from app.database.models import ChatHistory, MedicalReportHistory, PatientHistory, User

    session = SessionLocal()
    session.query(ChatHistory).delete()
    session.query(MedicalReportHistory).delete()
    session.query(PatientHistory).delete()
    session.query(User).delete()
    session.commit()
    yield session
    session.close()


def register_and_login(client: TestClient, email: str, role: str = "PATIENT", password: str = "password123"):
    """Test helper: register a user and return (uuid, auth_headers)."""
    client.post(
        "/auth/register",
        json={"full_name": "Test User", "email": email, "password": password, "role": role},
    )
    tokens = client.post("/auth/login", json={"email": email, "password": password}).json()
    user_uuid = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()["uuid"]
    return user_uuid, {"Authorization": f"Bearer {tokens['access_token']}"}, tokens
