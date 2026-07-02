"""Tests for MedicalRangeService."""

from app.services.medical_range_service import MedicalRangeService


def test_high_value_detected():
    service = MedicalRangeService()
    result = service.compare("glucose", 145)
    assert result.status == "HIGH"
    assert result.reference_min == 70
    assert result.reference_max == 99
    assert result.unit == "mg/dL"


def test_low_value_detected():
    service = MedicalRangeService()
    result = service.compare("hemoglobin", 11.2)
    assert result.status == "LOW"


def test_normal_value_detected():
    service = MedicalRangeService()
    result = service.compare("glucose", 85)
    assert result.status == "NORMAL"


def test_boundary_values_are_normal():
    service = MedicalRangeService()
    assert service.compare("glucose", 70).status == "NORMAL"
    assert service.compare("glucose", 99).status == "NORMAL"


def test_unknown_parameter_defaults_to_normal_without_crashing():
    service = MedicalRangeService()
    result = service.compare("some_unknown_parameter", 42)
    assert result.status == "NORMAL"
    assert result.reference_min is None


def test_infer_report_type_blood_sugar():
    service = MedicalRangeService()
    assert service.infer_report_type(["glucose", "hba1c"]) == "Blood Sugar Report"


def test_infer_report_type_cbc():
    service = MedicalRangeService()
    assert service.infer_report_type(["hemoglobin", "wbc_count", "platelet_count"]) == "CBC Report"


def test_infer_report_type_empty_list():
    service = MedicalRangeService()
    assert service.infer_report_type([]) == "General Lab Report"
