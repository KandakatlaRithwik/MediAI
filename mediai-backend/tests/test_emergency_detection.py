"""Tests for EmergencyDetectionService."""

from app.services.emergency_detection_service import EmergencyDetectionService


def test_detects_chest_pain_as_emergency():
    service = EmergencyDetectionService()
    result = service.detect(["chest pain", "fatigue"])
    assert result.emergency is True
    assert result.alert == "Seek immediate medical attention."
    assert "chest pain" in result.matched_emergency_symptoms


def test_detects_stroke_symptoms_as_emergency():
    service = EmergencyDetectionService()
    result = service.detect(["facial drooping", "slurred speech"])
    assert result.emergency is True
    assert set(result.matched_emergency_symptoms) == {"facial drooping", "slurred speech"}


def test_non_emergency_symptoms_return_false():
    service = EmergencyDetectionService()
    result = service.detect(["cough", "sore throat", "runny nose"])
    assert result.emergency is False
    assert result.alert is None
    assert result.matched_emergency_symptoms == []


def test_empty_symptom_list_is_not_an_emergency():
    service = EmergencyDetectionService()
    result = service.detect([])
    assert result.emergency is False


def test_loss_of_consciousness_is_an_emergency():
    service = EmergencyDetectionService()
    result = service.detect(["loss of consciousness"])
    assert result.emergency is True
