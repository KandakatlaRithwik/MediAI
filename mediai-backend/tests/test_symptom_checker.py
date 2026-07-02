"""Tests for the POST /symptom-checker endpoint.

Uses the existing `client` fixture from conftest.py. Note this fixture only
overrides `get_rag_service` (Module 1's heavyweight ML dependency) -
SymptomCheckerService runs for real here, since it depends only on the
stdlib (json, re, difflib) and the static disease/weights datasets, making
it fast and fully offline without needing a fake.
"""

from app.core.constants import SYMPTOM_CHECKER_DISCLAIMER


def test_symptom_checker_matches_spec_example(client):
    response = client.post("/symptom-checker", json={"text": "I have fever cough headache body pain"})
    assert response.status_code == 200
    body = response.json()

    assert body["symptoms"] == ["fever", "cough", "headache", "body pain"]
    assert len(body["possible_diseases"]) > 0
    assert body["possible_diseases"][0]["disease"] == "Flu"
    assert body["recommended_specialist"] == "General Physician"
    assert body["disclaimer"] == SYMPTOM_CHECKER_DISCLAIMER
    assert body["emergency"] is False
    assert body["severity"] in ("Mild", "Moderate", "Severe", "Emergency")


def test_symptom_checker_detects_emergency(client):
    response = client.post(
        "/symptom-checker", json={"text": "I have chest pain, difficulty breathing and cold sweat"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["emergency"] is True
    assert body["severity"] == "Emergency"


def test_symptom_checker_specialist_examples(client):
    cases = {
        "I have frequent urination, increased thirst, fatigue and blurred vision": "Endocrinologist",
        "I have wheezing, chest tightness and shortness of breath": "Pulmonologist",
        "I have excessive worry, restlessness and difficulty concentrating": "Psychiatrist",
    }
    for text, expected_specialist in cases.items():
        response = client.post("/symptom-checker", json={"text": text})
        assert response.status_code == 200
        assert response.json()["recommended_specialist"] == expected_specialist


def test_symptom_checker_no_symptoms_falls_back_to_general_physician(client):
    response = client.post("/symptom-checker", json={"text": "I feel completely fine today"})
    assert response.status_code == 200
    body = response.json()
    assert body["symptoms"] == []
    assert body["possible_diseases"] == []
    assert body["recommended_specialist"] == "General Physician"
    assert body["emergency"] is False


def test_symptom_checker_rejects_too_short_text(client):
    response = client.post("/symptom-checker", json={"text": "hi"})
    assert response.status_code == 422


def test_symptom_checker_includes_reasoning(client):
    response = client.post("/symptom-checker", json={"text": "I have fever cough headache body pain"})
    body = response.json()
    assert len(body["reasoning"]) > 0
    assert all(line.startswith("Matched symptom:") for line in body["reasoning"])


def test_symptom_checker_response_always_includes_disclaimer(client):
    for text in ["I have fever", "I feel completely fine today"]:
        response = client.post("/symptom-checker", json={"text": text})
        assert response.json()["disclaimer"] == SYMPTOM_CHECKER_DISCLAIMER
