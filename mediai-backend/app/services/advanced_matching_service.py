"""
Advanced disease matching engine (Jaccard similarity).

Replaces the simple overlap-ratio scoring (matched / total_disease_symptoms,
still available via DiseaseMatchingService for backward compatibility) with
Jaccard similarity for the main symptom-checker and RAG pipelines:

    score = |intersection(user_symptoms, disease_symptoms)| / |union(user_symptoms, disease_symptoms)|

Jaccard is symmetric and penalizes diseases with large symptom lists that
happen to share a few terms with the input, which the simple overlap ratio
does not - a disease with 20 listed symptoms matching 2 of them scores much
lower under Jaccard than under the old asymmetric formula, which is a more
conservative (and arguably more honest) confidence signal.

Reuses load_disease_dataset() from disease_matching_service.py (the single
source of truth for the knowledge base) rather than re-loading it.
"""

import logging
from dataclasses import dataclass
from difflib import get_close_matches
from typing import List, Set

from app.schemas.disease import DiseaseRecord
from app.services.confidence_service import ConfidenceService
from app.services.disease_matching_service import load_disease_dataset

logger = logging.getLogger("medical_ai")

_FUZZY_MATCH_CUTOFF = 0.85


@dataclass
class AdvancedDiseaseMatch:
    """A single ranked match produced by Jaccard similarity scoring.

    Exposes a `.disease` attribute (a DiseaseRecord) so this remains
    interface-compatible with RecommendationService.recommend_specialist(),
    which only reads `.disease.specialist` - no changes needed there.
    """

    disease: DiseaseRecord
    matched_symptoms: List[str]
    jaccard_score: float
    confidence: int
    level: str


class AdvancedMatchingService:
    def __init__(self) -> None:
        self._diseases: List[DiseaseRecord] = load_disease_dataset()
        self._confidence_service = ConfidenceService()
        # Full symptom vocabulary, used for fuzzy-matching support when this
        # service is called standalone (e.g. directly in tests) with symptom
        # strings that weren't already vocabulary-validated by
        # SymptomExtractionService.
        self._vocabulary: Set[str] = {
            symptom for disease in self._diseases for symptom in disease.symptoms
        }

    def _normalize_symptoms(self, symptoms: List[str]) -> Set[str]:
        """Normalize (lowercase/strip), deduplicate, and fuzzy-correct symptoms
        against the known vocabulary."""
        normalized: Set[str] = set()
        for raw in symptoms:
            candidate = raw.strip().lower()
            if not candidate:
                continue
            if candidate in self._vocabulary:
                normalized.add(candidate)
                continue
            close_matches = get_close_matches(candidate, self._vocabulary, n=1, cutoff=_FUZZY_MATCH_CUTOFF)
            normalized.add(close_matches[0] if close_matches else candidate)
        return normalized

    def match(self, symptoms: List[str], top_n: int = 5) -> List[AdvancedDiseaseMatch]:
        """Rank diseases against extracted symptoms using Jaccard similarity, return top N."""
        normalized_input = self._normalize_symptoms(symptoms)
        if not normalized_input:
            return []

        matches: List[AdvancedDiseaseMatch] = []
        for disease in self._diseases:
            disease_symptoms = set(disease.symptoms)
            if not disease_symptoms:
                continue

            intersection = normalized_input & disease_symptoms
            if not intersection:
                continue

            union = normalized_input | disease_symptoms
            jaccard_score = len(intersection) / len(union) if union else 0.0

            confidence = self._confidence_service.to_score(jaccard_score)
            level = self._confidence_service.level_for_score(confidence)

            matches.append(
                AdvancedDiseaseMatch(
                    disease=disease,
                    matched_symptoms=sorted(intersection),
                    jaccard_score=round(jaccard_score, 4),
                    confidence=confidence,
                    level=level,
                )
            )

        matches.sort(key=lambda m: (-m.jaccard_score, m.disease.disease.lower()))

        logger.info(
            "Advanced (Jaccard) matching: %d input symptom(s) -> %d disease match(es), returning top %d.",
            len(normalized_input), len(matches), top_n,
        )
        return matches[:top_n]
