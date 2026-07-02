"""
SymptomCheckerService - top-level orchestrator for the Symptom Checker
feature (Module 2.5 - Advanced Medical Intelligence Engine).

Pipeline:

    Free text
      -> Symptom Extraction      (SymptomExtractionService)
      -> Emergency Detection     (EmergencyDetectionService) - runs BEFORE
         matching, per the explicit Module 2.5 requirement
      -> Disease Matching        (AdvancedMatchingService - Jaccard similarity)
      -> Severity Prediction     (SeverityPredictionService - weighted rules)
      -> Explanation             (ExplanationService - reasoning for top match)
      -> Specialist Recommendation (RecommendationService)

This mirrors the role RAGService plays for the document Q&A flow: the route
stays thin (HTTP concerns only) and depends on this single entry point.
"""

import logging

from app.core.constants import DEFAULT_SPECIALIST, SYMPTOM_CHECKER_DISCLAIMER
from app.schemas.symptom import SymptomCheckerResponse
from app.services.advanced_matching_service import AdvancedMatchingService
from app.services.emergency_detection_service import EmergencyDetectionService
from app.services.explanation_service import ExplanationService
from app.services.recommendation_service import RecommendationService
from app.services.severity_prediction_service import SeverityPredictionService
from app.services.symptom_extraction_service import SymptomExtractionService

logger = logging.getLogger("medical_ai")


class SymptomCheckerService:
    def __init__(self) -> None:
        self._extraction_service = SymptomExtractionService()
        self._emergency_service = EmergencyDetectionService()
        self._matching_service = AdvancedMatchingService()
        self._severity_service = SeverityPredictionService()
        self._explanation_service = ExplanationService()
        self._recommendation_service = RecommendationService()

    def check(self, text: str, top_n: int = 5) -> SymptomCheckerResponse:
        """Run the full symptom-checker pipeline on free-text input."""
        symptoms = self._extraction_service.extract(text)
        logger.info("Symptom extraction: %d symptom(s) detected: %s", len(symptoms), symptoms)

        if not symptoms:
            return SymptomCheckerResponse(
                symptoms=[],
                possible_diseases=[],
                severity="Mild",
                emergency=False,
                recommended_specialist=DEFAULT_SPECIALIST,
                reasoning=[],
                disclaimer=SYMPTOM_CHECKER_DISCLAIMER,
            )

        # Emergency detection runs before disease matching, by design.
        emergency_assessment = self._emergency_service.detect(symptoms)

        ranked_matches = self._matching_service.match(symptoms, top_n=top_n)
        severity_assessment = self._severity_service.predict(symptoms)
        reasoning = self._explanation_service.explain(ranked_matches)
        recommended_specialist = self._recommendation_service.recommend_specialist(ranked_matches)

        # An emergency-level symptom always forces "Emergency" severity in the
        # response, even if the weighted symptom score alone would not have
        # crossed the Emergency threshold - a single red-flag symptom (e.g.
        # "loss of consciousness") should never be diluted by averaging
        # against several mild ones reported in the same sentence.
        severity_label = "Emergency" if emergency_assessment.emergency else severity_assessment.level

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

        logger.info(
            "Symptom check complete: severity=%s emergency=%s specialist=%s diseases=%d",
            severity_label, emergency_assessment.emergency, recommended_specialist, len(possible_diseases),
        )

        return SymptomCheckerResponse(
            symptoms=symptoms,
            possible_diseases=possible_diseases,
            severity=severity_label,
            emergency=emergency_assessment.emergency,
            recommended_specialist=recommended_specialist,
            reasoning=reasoning,
            disclaimer=SYMPTOM_CHECKER_DISCLAIMER,
        )
