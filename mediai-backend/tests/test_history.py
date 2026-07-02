"""Tests for Module 5: automatic history saving + GET /history/* endpoints."""

import os

from tests.conftest import register_and_login

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_anonymous_symptom_check_does_not_save_history(client, db_session):
    client.post("/symptom-checker", json={"text": "I have fever cough headache body pain"})
    # No user was ever created, so there's nothing to check via the API;
    # verify directly that no PatientHistory rows exist at all.
    from app.database.models import PatientHistory

    assert db_session.query(PatientHistory).count() == 0


def test_authenticated_symptom_check_saves_history(client, db_session):
    _, headers, _ = register_and_login(client, "hist_p1@example.com", role="PATIENT")
    response = client.post("/symptom-checker", json={"text": "I have fever cough headache body pain"}, headers=headers)
    assert response.status_code == 200

    history_response = client.get("/history/symptoms", headers=headers)
    entries = history_response.json()
    assert len(entries) == 1
    assert entries[0]["symptoms"] == ["fever", "cough", "headache", "body pain"]
    assert entries[0]["predicted_diseases"][0]["disease"] == "Flu"


def test_authenticated_report_analysis_saves_history(client, db_session):
    _, headers, _ = register_and_login(client, "hist_p2@example.com", role="PATIENT")
    with open(os.path.join(FIXTURES_DIR, "blood_sugar_report.pdf"), "rb") as f:
        response = client.post("/analyze-report", files={"file": ("report.pdf", f, "application/pdf")}, headers=headers)
    assert response.status_code == 200

    history_response = client.get("/history/reports", headers=headers)
    entries = history_response.json()
    assert len(entries) == 1
    assert entries[0]["report_type"] == "Blood Sugar Report"
    assert any(risk["risk"] == "Diabetes Risk" for risk in entries[0]["risk_assessment"])


def test_authenticated_ask_saves_chat_history(client, fake_rag_service, db_session):
    _, headers, _ = register_and_login(client, "hist_p3@example.com", role="PATIENT")
    fake_rag_service.ingested_documents["doc.pdf"] = 3  # so FakeRAGService returns a real answer

    response = client.post("/ask", json={"question": "What is the flu?"}, headers=headers)
    assert response.status_code == 200

    history_response = client.get("/history/chat", headers=headers)
    entries = history_response.json()
    assert len(entries) == 1
    assert entries[0]["question"] == "What is the flu?"


def test_anonymous_ask_does_not_save_chat_history(client, fake_rag_service, db_session):
    fake_rag_service.ingested_documents["doc.pdf"] = 3
    client.post("/ask", json={"question": "What is the flu?"})

    from app.database.models import ChatHistory

    assert db_session.query(ChatHistory).count() == 0


def test_full_profile_combines_all_history_types(client, db_session):
    _, headers, _ = register_and_login(client, "hist_p4@example.com", role="PATIENT")
    client.post("/symptom-checker", json={"text": "I have fever cough headache body pain"}, headers=headers)

    response = client.get("/history/full-profile", headers=headers)
    body = response.json()
    assert body["patient_info"]["email"] == "hist_p4@example.com"
    assert len(body["symptom_history"]) == 1
    assert body["report_history"] == []
    assert body["chat_history"] == []


def test_history_history_is_per_patient_isolated(client, db_session):
    _, p1_headers, _ = register_and_login(client, "hist_p5@example.com", role="PATIENT")
    _, p2_headers, _ = register_and_login(client, "hist_p6@example.com", role="PATIENT")

    client.post("/symptom-checker", json={"text": "I have fever cough headache body pain"}, headers=p1_headers)

    p1_history = client.get("/history/symptoms", headers=p1_headers).json()
    p2_history = client.get("/history/symptoms", headers=p2_headers).json()
    assert len(p1_history) == 1
    assert len(p2_history) == 0
