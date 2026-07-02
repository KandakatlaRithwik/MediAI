"""
RAG integration tests (Module 2.5).

Tests the symptom-aware /ask pipeline: symptom extraction -> emergency
detection -> Jaccard disease matching -> severity prediction -> context
injection -> Gemini.

RAGService normally constructs heavyweight ML dependencies (embedding
model, ChromaDB, Gemini client) in __init__, which aren't available in this
offline test environment. To test the real symptom-aware integration logic
without those, we bypass __init__ via object.__new__ and inject:
  - REAL SymptomExtractionService, EmergencyDetectionService,
    AdvancedMatchingService, SeverityPredictionService (all stdlib-only,
    fast, deterministic - no reason to fake these).
  - STUB RetrievalService and LLMService (the only genuinely
    network/ML-dependent pieces), so we can assert on exactly what context
    was passed to the LLM.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import pytest

from app.services.advanced_matching_service import AdvancedMatchingService
from app.services.emergency_detection_service import EmergencyDetectionService
from app.services.rag_service import RAGService, _build_intelligence_context_block
from app.services.severity_prediction_service import SeverityPredictionService
from app.services.symptom_extraction_service import SymptomExtractionService


@dataclass
class _StubChunk:
    text: str


class _StubRetrievalService:
    """Always returns no retrieved document chunks, isolating the test to
    the symptom-aware context-injection behavior."""

    def retrieve(
        self, question: str, top_k: Optional[int] = None, source_filter: Optional[str] = None
    ) -> Tuple[List[_StubChunk], List[str]]:
        return [], []


class _CapturingLLMService:
    """Stub LLM service that records exactly what context it was called with,
    instead of making a real Gemini API call."""

    def __init__(self) -> None:
        self.last_question: Optional[str] = None
        self.last_context_chunks: Optional[List[str]] = None

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        self.last_question = question
        self.last_context_chunks = context_chunks
        return "Stubbed medical answer."


def _build_rag_service_with_stubs() -> Tuple[RAGService, _CapturingLLMService]:
    """Construct a RAGService with real symptom-intelligence services but
    stubbed retrieval/LLM, bypassing __init__'s heavyweight ML setup."""
    from app.services.report_analysis_service import ReportContextStore

    service = object.__new__(RAGService)
    service._symptom_extraction_service = SymptomExtractionService()
    service._emergency_service = EmergencyDetectionService()
    service._matching_service = AdvancedMatchingService()
    service._severity_service = SeverityPredictionService()
    # Fresh, empty store so these symptom-focused tests are never affected
    # by report context (Module 3) - that integration has its own dedicated
    # test in test_report_rag_integration.py.
    service._report_context_store = ReportContextStore()
    service._retrieval_service = _StubRetrievalService()
    llm_stub = _CapturingLLMService()
    service._llm_service = llm_stub
    return service, llm_stub


def test_context_block_format():
    from app.services.advanced_matching_service import AdvancedMatchingService as AMS

    matching_service = AMS()
    matches = matching_service.match(["fever", "cough"], top_n=2)
    block = _build_intelligence_context_block(["fever", "cough"], matches, "Moderate", False)

    assert "Detected Symptoms:" in block
    assert "- fever" in block
    assert "- cough" in block
    assert "Possible Diseases:" in block
    assert "Severity:" in block
    assert "Moderate" in block
    assert "Emergency:" in block
    assert "No" in block


def test_answer_question_injects_symptom_context_when_symptoms_detected():
    service, llm_stub = _build_rag_service_with_stubs()
    response = service.answer_question("I have fever cough headache body pain")

    assert response.detected_symptoms == ["fever", "cough", "headache", "body pain"]
    assert len(response.possible_diseases) > 0
    assert response.possible_diseases[0].disease == "Flu"

    # The LLM must have received the intelligence context block.
    assert llm_stub.last_context_chunks is not None
    assert any("Detected Symptoms:" in chunk for chunk in llm_stub.last_context_chunks)
    assert any("Possible Diseases:" in chunk for chunk in llm_stub.last_context_chunks)


def test_answer_question_with_no_symptoms_and_no_chunks_returns_no_context_message():
    service, llm_stub = _build_rag_service_with_stubs()
    response = service.answer_question("What time is it?")

    assert response.answer == "I could not find sufficient medical information."
    assert response.detected_symptoms == []
    assert response.possible_diseases == []
    # LLM should never have been called - nothing to ground an answer in.
    assert llm_stub.last_context_chunks is None


def test_answer_question_appends_disclaimer_when_symptoms_detected():
    service, llm_stub = _build_rag_service_with_stubs()
    response = service.answer_question("I have fever and cough")
    assert "AI-generated health assessment" in response.answer


def test_answer_question_flags_emergency_in_context():
    service, llm_stub = _build_rag_service_with_stubs()
    service.answer_question("I have chest pain and difficulty breathing")

    assert llm_stub.last_context_chunks is not None
    intelligence_block = llm_stub.last_context_chunks[0]
    assert "Emergency:" in intelligence_block
    assert "Yes" in intelligence_block
