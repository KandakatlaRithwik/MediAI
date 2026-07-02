"""Tests for GET /dashboard/summary (Module 5)."""

import os

from tests.conftest import register_and_login

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_dashboard_summary_with_no_activity(client, db_session):
    _, headers, _ = register_and_login(client, "dash_p1@example.com", role="PATIENT")
    response = client.get("/dashboard/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "total_reports": 0,
        "total_symptom_checks": 0,
        "high_risk_reports": 0,
        "last_report_date": None,
    }


def test_dashboard_summary_counts_symptom_checks(client, db_session):
    _, headers, _ = register_and_login(client, "dash_p2@example.com", role="PATIENT")
    client.post("/symptom-checker", json={"text": "I have fever and cough"}, headers=headers)
    client.post("/symptom-checker", json={"text": "I have a headache"}, headers=headers)

    response = client.get("/dashboard/summary", headers=headers)
    assert response.json()["total_symptom_checks"] == 2


def test_dashboard_summary_counts_high_risk_reports(client, db_session):
    _, headers, _ = register_and_login(client, "dash_p3@example.com", role="PATIENT")
    with open(os.path.join(FIXTURES_DIR, "blood_sugar_report.pdf"), "rb") as f:
        client.post("/analyze-report", files={"file": ("report.pdf", f, "application/pdf")}, headers=headers)

    response = client.get("/dashboard/summary", headers=headers)
    body = response.json()
    assert body["total_reports"] == 1
    assert body["high_risk_reports"] == 1  # Diabetes Risk is High severity
    assert body["last_report_date"] is not None


def test_dashboard_summary_does_not_count_low_risk_reports_as_high_risk(client, db_session):
    _, headers, _ = register_and_login(client, "dash_p4@example.com", role="PATIENT")
    with open(os.path.join(FIXTURES_DIR, "cbc_report.pdf"), "rb") as f:
        client.post("/analyze-report", files={"file": ("report.pdf", f, "application/pdf")}, headers=headers)

    response = client.get("/dashboard/summary", headers=headers)
    body = response.json()
    assert body["total_reports"] == 1
    # CBC fixture only triggers Anemia Risk (Moderate), not High.
    assert body["high_risk_reports"] == 0
