"""Tests for POST /ask."""

import io


def test_ask_without_any_ingested_documents_returns_no_context_message(client):
    response = client.post("/ask", json={"question": "What are the symptoms of diabetes?"})

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "I could not find sufficient medical information."
    assert body["sources"] == []


def test_ask_after_upload_returns_answer_with_sources(client):
    files = {"file": ("diabetes.txt", io.BytesIO(b"Diabetes info content."), "text/plain")}
    client.post("/upload", files=files)

    response = client.post("/ask", json={"question": "What are the symptoms of diabetes?"})

    assert response.status_code == 200
    body = response.json()
    assert "Stub answer for" in body["answer"]
    assert any(src.startswith("diabetes") for src in body["sources"])


def test_ask_rejects_too_short_question(client):
    response = client.post("/ask", json={"question": "Hi"})

    assert response.status_code == 422
    body = response.json()
    assert body["status"] == "error"
