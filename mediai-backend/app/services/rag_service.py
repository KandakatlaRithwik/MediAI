"""
RAGService - top-level orchestrator for Module 1 (document Q&A), the
symptom-aware flow added in Module 2.5, Module 3's report-context
injection, and Module 5's patient-history-aware RAG memory.

Pipeline for /ask:

    Question
      -> Patient History          (HistoryService, Module 5) - loaded first,
                                    if the caller is authenticated
      -> Symptom Extraction       (SymptomExtractionService)
      -> Emergency Detection      (EmergencyDetectionService) - runs first
      -> Disease Matching         (AdvancedMatchingService - Jaccard)
      -> Severity Prediction      (SeverityPredictionService)
      -> Retriever                (RetrievalService - unchanged from Module 1)
      -> Context Assembly         (patient history + symptoms + diseases +
                                    severity + emergency + report context
                                    + retrieved chunks)
      -> Gemini                   (LLMService - unchanged from Module 1)
      -> Final Medical Response

If the caller is anonymous (no valid Bearer token) and no symptoms are
detected in the question, behavior is identical to Module 1: only retrieved
document chunks are used as context. Patient-history loading is fully
optional and best-effort - a missing/invalid token, or a DB failure, never
breaks /ask (see role_service.get_optional_current_user and
database.connection.get_db_session_or_none).
"""

import logging
from typing import TYPE_CHECKING, List, Optional

from app.core.constants import NO_CONTEXT_MESSAGE, REPORT_ANALYSIS_DISCLAIMER, SYMPTOM_CHECKER_DISCLAIMER
from app.database.connection import get_db_session_or_none
from app.rag.pipeline import IngestionPipeline
from app.schemas.response import AskResponse
from app.services.advanced_matching_service import AdvancedDiseaseMatch, AdvancedMatchingService
from app.services.emergency_detection_service import EmergencyDetectionService
from app.services.history_service import HistoryService
from app.services.llm_service import LLMService
from app.services.report_analysis_service import get_report_context_store
from app.services.retrieval_service import RetrievalService
from app.services.severity_prediction_service import SeverityPredictionService
from app.services.symptom_extraction_service import SymptomExtractionService

if TYPE_CHECKING:
    from app.database.models.user import User

logger = logging.getLogger("medical_ai")

_PATIENT_HISTORY_LIMIT = 3


def _build_intelligence_context_block(
    symptoms: List[str],
    matches: List[AdvancedDiseaseMatch],
    severity_level: str,
    is_emergency: bool,
) -> str:
    """Render the Module 2.5 medical-intelligence findings as a labeled
    context block for Gemini, in the format specified by Improvement 5:

        Detected Symptoms:
        - fever
        - cough

        Possible Diseases:
        - Influenza (87%)
        - COVID-19 (81%)

        Severity:
        Moderate

        Emergency:
        No

    Explicitly labeled as analysis, not diagnosis - the model is also told
    via system prompt rule 8 (app.core.constants.MEDICAL_SYSTEM_PROMPT) to
    never present this as a confirmed diagnosis.
    """
    lines = ["Symptom-pattern analysis (NOT a diagnosis - for context only):", ""]

    lines.append("Detected Symptoms:")
    for symptom in symptoms:
        lines.append(f"- {symptom}")
    lines.append("")

    lines.append("Possible Diseases:")
    if matches:
        for match in matches:
            lines.append(f"- {match.disease.disease} ({match.confidence}%)")
    else:
        lines.append("- None matched with sufficient confidence")
    lines.append("")

    lines.append("Severity:")
    lines.append(severity_level)
    lines.append("")

    lines.append("Emergency:")
    lines.append("Yes" if is_emergency else "No")

    return "\n".join(lines)


def _build_patient_history_context_block(symptom_entries, report_entries, chat_entries) -> str:
    """Render a patient's recent history (Module 5) as a labeled context
    block, per the spec's "Past Symptoms / Past Reports / Previous
    Questions" RAG memory requirement. Limited to the most recent few
    entries of each type to keep the context reasonably sized."""
    lines = ["Patient History (prior visits - for background context only):", ""]

    if symptom_entries:
        lines.append("Past Symptoms:")
        for entry in symptom_entries:
            symptoms_str = ", ".join(entry.symptoms) if entry.symptoms else "none recorded"
            lines.append(f"- {entry.created_at.date()}: {symptoms_str} (severity: {entry.severity})")
        lines.append("")

    if report_entries:
        lines.append("Past Reports:")
        for entry in report_entries:
            risk_names = ", ".join(risk.get("risk", "") for risk in (entry.risk_assessment or []))
            risk_text = risk_names if risk_names else "no risks identified"
            lines.append(f"- {entry.created_at.date()}: {entry.report_type} - {risk_text}")
        lines.append("")

    if chat_entries:
        lines.append("Previous Questions:")
        for entry in chat_entries:
            lines.append(f"- {entry.created_at.date()}: {entry.question}")

    return "\n".join(lines)


class RAGService:
    def __init__(self) -> None:
        self._pipeline = IngestionPipeline()
        self._retrieval_service = RetrievalService()
        self._llm_service = LLMService()
        self._symptom_extraction_service = SymptomExtractionService()
        self._emergency_service = EmergencyDetectionService()
        self._matching_service = AdvancedMatchingService()
        self._severity_service = SeverityPredictionService()
        self._report_context_store = get_report_context_store()
        self._history_service = HistoryService()

    def ingest_document(self, file_path: str, filename: str) -> int:
        """Ingest a single uploaded document. Returns the chunk count stored."""
        return self._pipeline.ingest(file_path, filename)

    def _load_patient_history_context(self, current_user: Optional["User"]) -> Optional[str]:
        """Best-effort: load a small slice of the authenticated patient's
        recent history and render it as a context block. Returns None for
        anonymous callers, or if the database is unavailable - never raises."""
        if current_user is None:
            return None

        db = get_db_session_or_none()
        if db is None:
            return None
        try:
            symptom_entries = self._history_service.get_symptom_history(
                db, current_user.id, limit=_PATIENT_HISTORY_LIMIT
            )
            report_entries = self._history_service.get_report_history(
                db, current_user.id, limit=_PATIENT_HISTORY_LIMIT
            )
            chat_entries = self._history_service.get_chat_history(
                db, current_user.id, limit=_PATIENT_HISTORY_LIMIT
            )
        except Exception as exc:  # noqa: BLE001 - history loading must never break /ask
            logger.error("Failed to load patient history for user_id=%s: %s", current_user.id, exc)
            return None
        finally:
            db.close()

        if not symptom_entries and not report_entries and not chat_entries:
            return None

        return _build_patient_history_context_block(symptom_entries, report_entries, chat_entries)

    def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        source_filter: Optional[str] = None,
        current_user: Optional["User"] = None,
    ) -> AskResponse:
        """Run the full patient-history -> symptom-detection -> retrieve ->
        generate flow for a question. `current_user` is optional - pass it
        when the caller is authenticated to enable history-aware context."""
        # 0. Patient history (Module 5) - loaded first, per the spec's
        # "User Query -> Patient History -> RAG Context" architecture.
        patient_history_context = self._load_patient_history_context(current_user)

        # 1. Symptom extraction.
        detected_symptoms = self._symptom_extraction_service.extract(question)

        # 2. Emergency detection - runs before disease matching, by design.
        emergency_assessment = self._emergency_service.detect(detected_symptoms)

        # 3. Disease matching (Jaccard) + 4. Severity prediction.
        ranked_matches: List[AdvancedDiseaseMatch] = []
        severity_level = "Mild"
        if detected_symptoms:
            ranked_matches = self._matching_service.match(detected_symptoms)
            severity_assessment = self._severity_service.predict(detected_symptoms)
            severity_level = "Emergency" if emergency_assessment.emergency else severity_assessment.level

            logger.info(
                "RAG symptom-aware decision: symptoms=%s diseases=%d severity=%s emergency=%s",
                detected_symptoms, len(ranked_matches), severity_level, emergency_assessment.emergency,
            )

        # 5. RAG retrieval - unchanged from Module 1.
        chunks, sources = self._retrieval_service.retrieve(
            question, top_k=top_k, source_filter=source_filter
        )

        # Step 8 (Module 3): pull in the most recently analyzed report's
        # findings, if any - independent of whether this question itself
        # mentions symptoms (e.g. "What does my report mean?").
        report_context = self._report_context_store.get_latest()

        # Nothing to ground an answer in at all -> preserve Module 1 behavior exactly.
        if (
            not chunks
            and not ranked_matches
            and not emergency_assessment.emergency
            and not report_context
            and not patient_history_context
        ):
            logger.info("No relevant chunks or symptom/report/history context found for question: %s", question)
            return AskResponse(answer=NO_CONTEXT_MESSAGE, sources=[])

        # 6. Context assembly: patient history first, then the intelligence
        # block, then report context, then retrieved document chunks.
        context_texts = [chunk.text for chunk in chunks]
        if detected_symptoms:
            intelligence_block = _build_intelligence_context_block(
                detected_symptoms, ranked_matches, severity_level, emergency_assessment.emergency
            )
            context_texts = [intelligence_block] + context_texts
        if report_context:
            context_texts = [report_context] + context_texts
        if patient_history_context:
            context_texts = [patient_history_context] + context_texts

        # 7. Gemini - unchanged from Module 1 (same system prompt, same call signature).
        answer = self._llm_service.generate_answer(question, context_texts)

        # 8. Safety layer: guarantee the relevant disclaimer whenever
        # symptom/disease or report analysis influenced this answer,
        # regardless of what the model said.
        if detected_symptoms and SYMPTOM_CHECKER_DISCLAIMER not in answer:
            answer = f"{answer}\n\n{SYMPTOM_CHECKER_DISCLAIMER}"
        if report_context and REPORT_ANALYSIS_DISCLAIMER not in answer:
            answer = f"{answer}\n\n{REPORT_ANALYSIS_DISCLAIMER}"

        possible_diseases = [
            {
                "disease": match.disease.disease,
                "score": match.jaccard_score,
                "confidence": match.confidence,
                "level": match.level,
                "category": match.disease.category,
                "specialist": match.disease.specialist,
                "severity": match.disease.severity,
                "matched_symptoms": match.matched_symptoms,
            }
            for match in ranked_matches
        ]

        return AskResponse(
            answer=answer,
            sources=sources,
            detected_symptoms=detected_symptoms,
            possible_diseases=possible_diseases,
        )
