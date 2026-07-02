"""
Severity prediction engine.

Rule-based scoring: each extracted symptom contributes a configurable
weight (app/data/symptom_weights.json); the summed weight is mapped to a
severity band (Mild / Moderate / Severe / Emergency) per
app.core.constants.SEVERITY_SCORE_THRESHOLDS.

Symptoms with no explicit entry in the weights file fall back to
DEFAULT_SYMPTOM_WEIGHT rather than being silently ignored, so an unweighted
symptom still contributes something to the overall picture instead of
disappearing from the score entirely.
"""

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from app.core.constants import DEFAULT_SYMPTOM_WEIGHT, SEVERITY_SCORE_THRESHOLDS
from app.core.exceptions import KnowledgeBaseError

logger = logging.getLogger("medical_ai")

_WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "data" / "symptom_weights.json"


@lru_cache()
def load_symptom_weights() -> Dict[str, int]:
    """Load and cache the symptom -> weight mapping."""
    try:
        with open(_WEIGHTS_PATH, "r", encoding="utf-8") as weights_file:
            raw_weights = json.load(weights_file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load symptom weights from %s: %s", _WEIGHTS_PATH, exc)
        raise KnowledgeBaseError(f"Failed to load symptom weights: {exc}") from exc

    return {symptom.strip().lower(): int(weight) for symptom, weight in raw_weights.items()}


@dataclass
class SeverityAssessment:
    level: str
    score: int
    contributing_symptoms: Dict[str, int]


class SeverityPredictionService:
    def __init__(self) -> None:
        self._weights = load_symptom_weights()

    def predict(self, symptoms: List[str]) -> SeverityAssessment:
        """Score a list of extracted symptoms and map the total to a severity band."""
        contributing: Dict[str, int] = {}
        total_score = 0

        for symptom in symptoms:
            normalized = symptom.strip().lower()
            weight = self._weights.get(normalized, DEFAULT_SYMPTOM_WEIGHT)
            contributing[normalized] = weight
            total_score += weight

        level = self._level_for_score(total_score)
        logger.info(
            "Severity prediction: score=%d level=%s symptoms=%s",
            total_score, level, symptoms,
        )
        return SeverityAssessment(level=level, score=total_score, contributing_symptoms=contributing)

    @staticmethod
    def _level_for_score(score: int) -> str:
        for threshold, label in SEVERITY_SCORE_THRESHOLDS:
            if score >= threshold:
                return label
        return SEVERITY_SCORE_THRESHOLDS[-1][1]
