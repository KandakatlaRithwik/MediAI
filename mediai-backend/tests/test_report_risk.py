"""Tests for ReportRiskService."""

from app.services.report_risk_service import ReportRiskService


def test_high_glucose_triggers_diabetes_risk():
    service = ReportRiskService()
    risks = service.assess({"glucose": 145})
    assert any(r.risk == "Diabetes Risk" for r in risks)


def test_borderline_glucose_triggers_prediabetes_risk():
    service = ReportRiskService()
    risks = service.assess({"glucose": 110})
    assert any(r.risk == "Prediabetes Risk" for r in risks)


def test_low_hemoglobin_triggers_anemia_risk():
    service = ReportRiskService()
    risks = service.assess({"hemoglobin": 9.5})
    assert any(r.risk == "Anemia Risk" for r in risks)


def test_high_ldl_triggers_cardiovascular_risk():
    service = ReportRiskService()
    risks = service.assess({"ldl": 165})
    assert any(r.risk == "Cardiovascular Risk" for r in risks)


def test_high_tsh_triggers_hypothyroidism_risk():
    service = ReportRiskService()
    risks = service.assess({"tsh": 8.4})
    assert any(r.risk == "Hypothyroidism Risk" for r in risks)


def test_normal_values_trigger_no_risk():
    service = ReportRiskService()
    risks = service.assess({"glucose": 85, "hemoglobin": 14.0})
    assert risks == []


def test_duplicate_risks_from_multiple_parameters_are_merged():
    service = ReportRiskService()
    risks = service.assess({"glucose": 145, "hba1c": 6.8})
    diabetes_risks = [r for r in risks if r.risk == "Diabetes Risk"]
    assert len(diabetes_risks) == 1
    assert set(diabetes_risks[0].based_on) == {"glucose", "hba1c"}


def test_unrecognized_parameter_produces_no_risk():
    service = ReportRiskService()
    risks = service.assess({"some_unknown_parameter": 999})
    assert risks == []
