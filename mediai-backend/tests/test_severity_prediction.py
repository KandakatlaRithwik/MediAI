"""Tests for SeverityPredictionService."""

from app.services.severity_prediction_service import SeverityPredictionService


def test_mild_example_from_spec():
    # Spec: fever, cough -> Mild
    service = SeverityPredictionService()
    result = service.predict(["fever", "cough"])
    # fever=3, cough=2 -> total 5 -> Mild band (0-5)
    assert result.score == 5
    assert result.level == "Mild"


def test_emergency_example_from_spec():
    # Spec: high fever, chest pain, breathing difficulty -> Emergency
    service = SeverityPredictionService()
    result = service.predict(["high fever", "chest pain", "difficulty breathing"])
    # high fever=6, chest pain=10, difficulty breathing=10 -> total 26 -> Emergency (16+)
    assert result.score == 26
    assert result.level == "Emergency"


def test_severity_band_boundaries():
    service = SeverityPredictionService()
    assert service._level_for_score(0) == "Mild"
    assert service._level_for_score(5) == "Mild"
    assert service._level_for_score(6) == "Moderate"
    assert service._level_for_score(10) == "Moderate"
    assert service._level_for_score(11) == "Severe"
    assert service._level_for_score(15) == "Severe"
    assert service._level_for_score(16) == "Emergency"
    assert service._level_for_score(100) == "Emergency"


def test_unweighted_symptom_falls_back_to_default_weight():
    service = SeverityPredictionService()
    result = service.predict(["some symptom not in the weights file"])
    assert result.score > 0


def test_empty_symptom_list_yields_mild():
    service = SeverityPredictionService()
    result = service.predict([])
    assert result.score == 0
    assert result.level == "Mild"
