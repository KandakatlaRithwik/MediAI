"""
Step 8 RAG integration test (Module 3): verifies that an analyzed report's
findings get injected into RAGService's context on a subsequent /ask call.

Uses the same object.__new__ DI-bypass pattern as
test_rag_symptom_integration.py, to exercise the real pipeline logic
without needing the heavyweight ML dependencies (embedding model, Gemini)
that aren't available in this offline test environment.
"""

import os
from typing import List, Optional, Tuple

from app.core.constants import REPORT_ANALYSIS_DISCLAIMER
from app.services.advanced_matching_service import AdvancedMatchingService
from app.services.emergency_detection_service import EmergencyDetectionService
from app.services.medical_range_service import MedicalRangeService
from app.services.rag_service import RAGService
from app.services.report_analysis_service import ReportAnalysisService, get_report_context_store
from app.services.report_extraction_service import ReportExtractionService
from app.services.report_parser_service import ReportParserService
from app.services.report_risk_service import ReportRiskService
from app.services.severity_prediction_service import SeverityPredictionService
from app.services.symptom_extraction_service import SymptomExtractionService

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


class _StubLLM:
    def __init__(self) -> None:
        self.last_context_chunks: Optional[List[str]] = None

    def generate_answer(self, question: str, context_chunks: List[str]) -> str:
        self.last_context_chunks = context_chunks
        return "Stubbed answer."


class _StubRetrieval:
    def retrieve(
        self, question: str, top_k: Optional[int] = None, source_filter: Optional[str] = None
    ) -> Tuple[List, List[str]]:
        return [], []


def test_analyzed_report_context_flows_into_subsequent_ask_call():
    # Reset shared store so this test doesn't depend on execution order.
    store = get_report_context_store()
    store.clear()

    report_service = object.__new__(ReportAnalysisService)
    report_service._extraction_service = ReportExtractionService()
    report_service._parser_service = ReportParserService()
    report_service._range_service = MedicalRangeService()
    report_service._risk_service = ReportRiskService()
    report_service._llm_service = _StubLLM()

    report_service.analyze_report(
        os.path.join(FIXTURES_DIR, "blood_sugar_report.pdf"), "blood_sugar_report.pdf"
    )

    assert store.get_latest() is not None

    rag_service = object.__new__(RAGService)
    rag_service._symptom_extraction_service = SymptomExtractionService()
    rag_service._emergency_service = EmergencyDetectionService()
    rag_service._matching_service = AdvancedMatchingService()
    rag_service._severity_service = SeverityPredictionService()
    rag_service._report_context_store = store
    rag_service._retrieval_service = _StubRetrieval()
    ask_llm_stub = _StubLLM()
    rag_service._llm_service = ask_llm_stub

    response = rag_service.answer_question("What does my report mean?")

    assert ask_llm_stub.last_context_chunks is not None
    injected_context = ask_llm_stub.last_context_chunks[0]
    assert "Medical Report Analysis" in injected_context
    assert "Diabetes Risk" in injected_context
    assert "glucose" in injected_context

    assert REPORT_ANALYSIS_DISCLAIMER in response.answer

    store.clear()
