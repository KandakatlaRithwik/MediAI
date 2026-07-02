"""Tests for SymptomExtractionService."""

from app.services.symptom_extraction_service import SymptomExtractionService


def test_extracts_symptoms_from_spec_example():
    service = SymptomExtractionService()
    result = service.extract("I have fever, cough and headache.")
    assert result == ["fever", "cough", "headache"]


def test_normalizes_case_and_strips_punctuation():
    service = SymptomExtractionService()
    result = service.extract("FEVER!!! cough???")
    assert result == ["fever", "cough"]


def test_removes_duplicates_preserving_first_occurrence_order():
    service = SymptomExtractionService()
    # Note: phrases like "high fever" or "severe headache" are intentionally
    # distinct, more specific symptoms in the dataset (used for
    # severity/emergency weighting), so they are correctly extracted
    # separately rather than deduplicated against the plain term. Use
    # "cough", which has no overlapping superstring variant, to test
    # straightforward dedup.
    result = service.extract("cough cough cough, just a cough")
    assert result == ["cough"]


def test_recognizes_multi_word_symptom_phrases():
    service = SymptomExtractionService()
    result = service.extract("I have frequent urination and increased thirst")
    assert "frequent urination" in result
    assert "increased thirst" in result
    # The individual words should not also leak through as separate bogus symptoms.
    assert "frequent" not in result
    assert "urination" not in result


def test_typo_tolerance():
    service = SymptomExtractionService()
    result = service.extract("I have feever and haedache")
    assert "fever" in result
    assert "headache" in result


def test_empty_and_whitespace_only_input_returns_empty_list():
    service = SymptomExtractionService()
    assert service.extract("") == []
    assert service.extract("   ") == []


def test_text_with_no_recognizable_symptoms_returns_empty_list():
    service = SymptomExtractionService()
    result = service.extract("I went for a walk and had a sandwich")
    assert result == []


def test_extracts_full_demo_payload_exactly():
    service = SymptomExtractionService()
    result = service.extract("I have fever cough headache body pain")
    assert result == ["fever", "cough", "headache", "body pain"]
