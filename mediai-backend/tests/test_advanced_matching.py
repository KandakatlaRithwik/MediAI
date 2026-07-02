"""Tests for AdvancedMatchingService (Jaccard similarity disease matching)."""

from app.services.advanced_matching_service import AdvancedMatchingService


def test_jaccard_score_is_intersection_over_union():
    service = AdvancedMatchingService()
    # Diabetes symptoms: frequent urination, increased thirst, fatigue,
    # blurred vision, unexplained weight loss (5 total).
    symptoms = ["frequent urination", "increased thirst"]
    matches = service.match(symptoms, top_n=10)

    diabetes_match = next(m for m in matches if m.disease.disease == "Diabetes")
    # intersection = 2 (both symptoms matched), union = 5 (disease symptoms,
    # since both input symptoms are a subset of them) -> 2/5 = 0.4
    assert diabetes_match.jaccard_score == 0.4
    assert diabetes_match.confidence == 40


def test_returns_top_n_ranked_by_score_descending():
    service = AdvancedMatchingService()
    matches = service.match(["fever", "cough", "headache", "body pain"], top_n=3)
    assert len(matches) <= 3
    scores = [m.jaccard_score for m in matches]
    assert scores == sorted(scores, reverse=True)


def test_no_symptoms_returns_no_matches():
    service = AdvancedMatchingService()
    assert service.match([], top_n=5) == []


def test_unrecognized_symptoms_return_no_matches():
    service = AdvancedMatchingService()
    matches = service.match(["spontaneous combustion"], top_n=5)
    assert matches == []


def test_diseases_with_zero_overlap_are_excluded():
    service = AdvancedMatchingService()
    matches = service.match(["chest pain"], top_n=50)
    for match in matches:
        assert "chest pain" in match.matched_symptoms


def test_confidence_level_label_is_consistent_with_score():
    service = AdvancedMatchingService()
    matches = service.match(["fever", "cough", "headache", "body pain", "sore throat"], top_n=10)
    for match in matches:
        if match.confidence >= 90:
            assert match.level == "Very High"
        elif match.confidence >= 70:
            assert match.level == "High"
        elif match.confidence >= 50:
            assert match.level == "Moderate"
        elif match.confidence >= 30:
            assert match.level == "Low"
        else:
            assert match.level == "Very Low"
