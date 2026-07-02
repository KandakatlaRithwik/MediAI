"""
Tests for the POST /analyze-report endpoint.

Uses the existing `client` fixture from conftest.py, which only overrides
`get_rag_service` - ReportAnalysisService runs for real here (extraction,
parsing, range comparison, risk assessment all run against real logic; the
Gemini call inside it will fail in this offline sandbox and gracefully fall
back to a placeholder ai_summary, which is itself a real, intentional
behavior under test - not a workaround).
"""

import os

from app.core.constants import REPORT_ANALYSIS_DISCLAIMER

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_analyze_report_pdf_blood_sugar(client):
    with open(os.path.join(FIXTURES_DIR, "blood_sugar_report.pdf"), "rb") as f:
        response = client.post("/analyze-report", files={"file": ("report.pdf", f, "application/pdf")})

    assert response.status_code == 200
    body = response.json()
    assert body["report_type"] == "Blood Sugar Report"
    assert "glucose" in body["abnormal_parameters"]
    assert "hba1c" in body["abnormal_parameters"]
    assert any(r["risk"] == "Diabetes Risk" for r in body["risk_assessment"])
    assert body["disclaimer"] == REPORT_ANALYSIS_DISCLAIMER
    assert isinstance(body["ai_summary"], str) and len(body["ai_summary"]) > 0


def test_analyze_report_txt_liver_function(client):
    with open(os.path.join(FIXTURES_DIR, "lft_report.txt"), "rb") as f:
        response = client.post("/analyze-report", files={"file": ("report.txt", f, "text/plain")})

    assert response.status_code == 200
    body = response.json()
    assert body["report_type"] == "Liver Function Test Report"
    assert "sgot" in body["abnormal_parameters"]
    assert "sgpt" in body["abnormal_parameters"]


def test_analyze_report_cbc_pdf(client):
    with open(os.path.join(FIXTURES_DIR, "cbc_report.pdf"), "rb") as f:
        response = client.post("/analyze-report", files={"file": ("report.pdf", f, "application/pdf")})

    assert response.status_code == 200
    body = response.json()
    assert body["report_type"] == "CBC Report"
    assert "hemoglobin" in body["abnormal_parameters"]


def test_analyze_report_with_no_lab_values_returns_422(client):
    with open(os.path.join(FIXTURES_DIR, "no_lab_values.txt"), "rb") as f:
        response = client.post("/analyze-report", files={"file": ("report.txt", f, "text/plain")})

    assert response.status_code == 422
    assert response.json()["status"] == "error"


def test_analyze_report_rejects_unsupported_extension(client):
    response = client.post(
        "/analyze-report", files={"file": ("report.docx", b"not a real docx", "application/octet-stream")}
    )
    assert response.status_code == 400


def test_analyze_report_response_includes_parameter_details(client):
    with open(os.path.join(FIXTURES_DIR, "blood_sugar_report.pdf"), "rb") as f:
        response = client.post("/analyze-report", files={"file": ("report.pdf", f, "application/pdf")})

    body = response.json()
    glucose_param = next(p for p in body["parameters"] if p["name"] == "glucose")
    assert glucose_param["value"] == 145
    assert glucose_param["status"] == "HIGH"
    assert glucose_param["unit"] == "mg/dL"
    assert glucose_param["reference_min"] == 70
    assert glucose_param["reference_max"] == 99
