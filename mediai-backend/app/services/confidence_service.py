"""
Confidence scoring engine.

Converts the raw symptom-overlap ratio (0.0-1.0) produced by
DiseaseMatchingService into a user-facing confidence score (0-100) and a
human-readable level label, then assembles the final API-facing
`PossibleDisease` objects. Centralizing that assembly here (rather than
duplicating it in every caller) keeps both the Symptom Checker endpoint and
the symptom-aware /ask flow consistent by construction.

Pure, stateless logic - no I/O, trivially unit-testable.
"""

import logging
from typing import List

from app.core.constants import CONFIDENCE_LEVEL_THRESHOLDS
from app.schemas.disease import PossibleDisease
from app.services.disease_matching_service import DiseaseMatch

logger = logging.getLogger(__name__)


class ConfidenceService:
    def to_score(self, confidence_ratio: float) -> int:
        """Convert a 0.0-1.0 overlap ratio into a 0-100 integer confidence score."""
        clamped_ratio = max(0.0, min(1.0, confidence_ratio))
        return round(clamped_ratio * 100)

    def level_for_score(self, score: int) -> str:
        """Map a 0-100 confidence score to its human-readable level label."""
        for threshold, label in CONFIDENCE_LEVEL_THRESHOLDS:
            if score >= threshold:
                return label
        return CONFIDENCE_LEVEL_THRESHOLDS[-1][1]

    def score_matches(self, matches: List[DiseaseMatch]) -> List[PossibleDisease]:
        """Score a ranked list of DiseaseMatch objects into API-facing PossibleDisease results."""
        possible_diseases: List[PossibleDisease] = []
        for match in matches:
            score = self.to_score(match.confidence_ratio)
            level = self.level_for_score(score)
            possible_diseases.append(
                PossibleDisease(
                    name=match.disease.disease,
                    confidence=score,
                    level=level,
                    specialist=match.disease.specialist,
                    severity=match.disease.severity,
                    matched_symptoms=match.matched_symptoms,
                )
            )
        return possible_diseases
