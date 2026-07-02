"""
ReportAnalysisService - top-level orchestrator for the Medical Report
Analyzer (Module 3).

Pipeline:

    Report (PDF/TXT)
      -> Extraction        (ReportExtractionService)
      -> Parameter parsing  (ReportParserService)
      -> Range comparison    (MedicalRangeService)  -> Step 4: abnormality detection
      -> Risk assessment      (ReportRiskService)
      -> AI explanation         (LLMService, reused as-is from Module 1)
      -> Response assembly

Mirrors the orchestrator role RAGService and SymptomCheckerService play for
their respective features: the route stays thin (HTTP concerns only) and
depends on this single entry point.

Also owns ReportContextStore (Step 8: RAG integration) - a small in-memory
store holding the most recently analyzed report's summary, so RAGService
can inject "Detected Risks / Abnormal Parameters / Report Summary" into
Gemini's context on subsequent /ask calls without this module needing to
know anything about how RAGService works, and vice versa.
"""

import logging
import threading
from typing import List, Optional

from app.core.constants import REPORT_ANALYSIS_DISCLAIMER
from app.core.exceptions import ReportAnalysisError
from app.schemas.report_response import ReportAnalysisResponse, ReportParameter
from app.services.llm_service import LLMService
from app.services.medical_range_service import MedicalRangeService
from app.services.report_extraction_service import ReportExtractionService
from app.services.report_parser_service import ReportParserService
from app.services.report_risk_service import ReportRiskService

logger = logging.getLogger("report_analysis")


def _build_report_context_block(response: ReportAnalysisResponse) -> str:
    """Render an analyzed report as a labeled context block for Gemini /
    for RAGService's context injection (Step 8), in the format specified:
    Detected Risks, Abnormal Parameters, Report Summary."""
    lines = ["Medical Report Analysis (NOT a diagnosis - for context only):", ""]

    lines.append(f"Report Type: {response.report_type}")
    lines.append("")

    lines.append("Parameters:")
    for parameter in response.parameters:
        range_text = ""
        if parameter.reference_min is not None and parameter.reference_max is not None:
            range_text = f", normal range {parameter.reference_min}-{parameter.reference_max}"
        unit_text = f" {parameter.unit}" if parameter.unit else ""
        lines.append(f"- {parameter.name}: {parameter.value}{unit_text} ({parameter.status}{range_text})")
    lines.append("")

    lines.append("Abnormal Parameters: " + (", ".join(response.abnormal_parameters) or "None"))
    lines.append("")

    lines.append("Detected Risks:")
    if response.risk_assessment:
        for risk in response.risk_assessment:
            lines.append(f"- {risk.risk} ({risk.severity})")
    else:
        lines.append("- None identified")

    return "\n".join(lines)


class ReportContextStore:
    """Thread-safe, in-memory store for the most recently analyzed report's
    context block. The backend has no per-user session/auth layer yet, so
    this mirrors that same simplicity - a single shared "latest report"
    slot, consistent with the rest of the current architecture. Swappable
    for a per-user store later without changing RAGService's call site.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_context: Optional[str] = None

    def set_latest(self, context_block: str) -> None:
        with self._lock:
            self._latest_context = context_block

    def get_latest(self) -> Optional[str]:
        with self._lock:
            return self._latest_context

    def clear(self) -> None:
        with self._lock:
            self._latest_context = None


_report_context_store = ReportContextStore()


def get_report_context_store() -> ReportContextStore:
    """Module-level singleton accessor, used by both ReportAnalysisService
    (writer) and RAGService (reader) so they don't need a direct dependency
    on each other."""
    return _report_context_store


class ReportAnalysisService:
    def __init__(self) -> None:
        self._extraction_service = ReportExtractionService()
        self._parser_service = ReportParserService()
        self._range_service = MedicalRangeService()
        self._risk_service = ReportRiskService()
        self._llm_service = LLMService()

    def analyze_report(self, file_path: str, filename: str) -> ReportAnalysisResponse:
        """Run the full report-analysis pipeline on an uploaded file."""
        logger.info("[1/6] Analyzing report '%s'", filename)

        # Step 1: extraction.
        raw_text = self._extraction_service.extract_text(file_path)
        logger.info("[2/6] Extracted %d chars from '%s'", len(raw_text), filename)

        # Step 2: parameter detection.
        parsed_values = self._parser_service.parse(raw_text)
        if not parsed_values:
            # Instead of a bare "not found" error, include a preview of the
            # extracted text so users/clinicians can quickly see whether the
            # extraction worked and the label vocabulary just did not match.
            preview = raw_text.strip()[:400]
            logger.warning(
                "No recognizable lab parameters found in '%s'. Preview: %r", filename, preview,
            )
            raise ReportAnalysisError(
                "We could read this report but could not detect any known lab parameters "
                "(supported: CBC, Blood Sugar, HbA1c, Lipid Profile, Thyroid, LFT, KFT, "
                "electrolytes). Please verify the report format.\n\n"
                f"Extracted text preview:\n{preview or '(empty)'}"
            )
        logger.info("[3/6] Parsed %d parameter(s) from '%s'", len(parsed_values), filename)

        # Step 3 + 4: range comparison and abnormality detection.
        parameters: List[ReportParameter] = []
        abnormal_parameters: List[str] = []
        for name, value in parsed_values.items():
            comparison = self._range_service.compare(name, value)
            parameters.append(
                ReportParameter(
                    name=name,
                    value=value,
                    unit=comparison.unit,
                    status=comparison.status,
                    reference_min=comparison.reference_min,
                    reference_max=comparison.reference_max,
                )
            )
            if comparison.status != "NORMAL":
                abnormal_parameters.append(name)

        report_type = self._range_service.infer_report_type(list(parsed_values.keys()))
        logger.info("[4/6] Report type inferred: %s (abnormal=%d)", report_type, len(abnormal_parameters))

        # Step 5: risk assessment.
        risk_assessment = self._risk_service.assess(parsed_values)
        logger.info("[5/6] Risk assessment produced %d risk(s)", len(risk_assessment))

        # Assemble response (without AI summary yet, so we can build the
        # context block once and reuse it for both the LLM call and the
        # RAG context store).
        response = ReportAnalysisResponse(
            report_type=report_type,
            parameters=parameters,
            abnormal_parameters=abnormal_parameters,
            risk_assessment=risk_assessment,
            ai_summary="",
            disclaimer=REPORT_ANALYSIS_DISCLAIMER,
        )
        context_block = _build_report_context_block(response)

        # Step 6: AI explanation, via the existing Gemini service - no
        # changes needed to LLMService itself, just a synthetic question.
        try:
            ai_summary = self._llm_service.generate_answer(
                question=(
                    "Provide a plain-English explanation covering EVERY parameter listed in the "
                    "context (not just abnormal ones): note whether each is Normal / Low / High, "
                    "what any abnormal values may indicate, and general lifestyle guidance. "
                    "Do not diagnose or prescribe medication or dosages."
                ),
                context_chunks=[context_block],
            )
        except Exception as exc:
            logger.error("AI explanation failed for report '%s': %s", filename, exc)
            ai_summary = (
                "An AI explanation could not be generated for this report. The structured "
                "findings above are still based on the detected values and reference ranges."
            )
        response.ai_summary = ai_summary
        logger.info("[6/6] AI summary generated (%d chars)", len(ai_summary))

        # Step 8: make this report's findings available to subsequent /ask
        # calls via RAGService.
        _report_context_store.set_latest(context_block)

        logger.info(
            "Report '%s' analyzed: type=%s parameters=%d abnormal=%d risks=%d",
            filename, report_type, len(parameters), len(abnormal_parameters), len(risk_assessment),
        )
        return response
