"""
Disease matching engine.

Loads the static disease knowledge base (app/data/diseases.json) and ranks
diseases against a set of extracted symptoms using a simple, explainable
overlap formula:

    confidence_ratio = matched_symptom_count / total_symptoms_for_disease

`load_disease_dataset()` is the single source of truth for reading and
validating the knowledge base; it is cached so the file is parsed exactly
once per process, and it is reused by other services (e.g.
SymptomExtractionService builds its vocabulary from the same dataset) so
the knowledge base never has more than one loader.
"""

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List

from app.core.exceptions import KnowledgeBaseError
from app.schemas.disease import DiseaseRecord

logger = logging.getLogger(__name__)

_DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "diseases.json"


@lru_cache()
def load_disease_dataset() -> List[DiseaseRecord]:
    """Load and validate the disease knowledge base.

    Cached for the lifetime of the process: this is static reference data,
    not something that changes at runtime, so repeated calls are free after
    the first.
    """
    try:
        with open(_DATASET_PATH, "r", encoding="utf-8") as dataset_file:
            raw_records = json.load(dataset_file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load disease knowledge base from %s: %s", _DATASET_PATH, exc)
        raise KnowledgeBaseError(f"Failed to load disease knowledge base: {exc}") from exc

    records: List[DiseaseRecord] = []
    for raw_record in raw_records:
        try:
            normalized_record = {
                **raw_record,
                "symptoms": [symptom.strip().lower() for symptom in raw_record.get("symptoms", [])],
            }
            records.append(DiseaseRecord(**normalized_record))
        except Exception as exc:  # noqa: BLE001 - log and skip malformed entries, don't crash startup
            logger.error("Skipping invalid disease record %r: %s", raw_record.get("disease", "?"), exc)

    if not records:
        raise KnowledgeBaseError("Disease knowledge base is empty or contains no valid records.")

    logger.info("Loaded %d disease record(s) from knowledge base.", len(records))
    return records


@dataclass
class DiseaseMatch:
    """A single ranked match between the user's symptoms and a known disease."""

    disease: DiseaseRecord
    matched_symptoms: List[str]
    confidence_ratio: float


class DiseaseMatchingService:
    """Ranks diseases by symptom overlap against a list of extracted symptoms."""

    def __init__(self) -> None:
        self._diseases: List[DiseaseRecord] = load_disease_dataset()

    def match(self, symptoms: List[str], top_n: int = 5) -> List[DiseaseMatch]:
        """Compare extracted symptoms against every disease, rank by overlap, return top N.

        Diseases with zero overlapping symptoms are excluded entirely
        (a confidence of 0% is not a "possible disease").
        """
        if not symptoms:
            return []

        normalized_input = {symptom.strip().lower() for symptom in symptoms if symptom.strip()}
        if not normalized_input:
            return []

        matches: List[DiseaseMatch] = []
        for disease in self._diseases:
            disease_symptoms = set(disease.symptoms)
            if not disease_symptoms:
                continue

            overlap = normalized_input & disease_symptoms
            if not overlap:
                continue

            confidence_ratio = len(overlap) / len(disease_symptoms)
            matches.append(
                DiseaseMatch(
                    disease=disease,
                    matched_symptoms=sorted(overlap),
                    confidence_ratio=confidence_ratio,
                )
            )

        # Rank by confidence descending; break ties alphabetically for determinism.
        matches.sort(key=lambda m: (-m.confidence_ratio, m.disease.disease.lower()))

        logger.info(
            "Matched %d disease(s) against %d input symptom(s); returning top %d.",
            len(matches), len(normalized_input), top_n,
        )
        return matches[:top_n]
