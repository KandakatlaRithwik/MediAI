"""
Medical explanation engine.

Explains WHY the leading disease prediction was made, by listing which of
the user's symptoms matched that disease's known symptom list. Operates on
the top-ranked AdvancedDiseaseMatch, since the symptom-checker API exposes a
single flat `reasoning` list explaining the leading prediction (per
Improvement 7's response shape).
"""

import logging
from typing import List

from app.services.advanced_matching_service import AdvancedDiseaseMatch

logger = logging.getLogger("medical_ai")


class ExplanationService:
    def explain(self, matches: List[AdvancedDiseaseMatch]) -> List[str]:
        """Build reasoning lines for the top-ranked disease match.

        Returns an empty list when there are no matches at all (nothing to explain).
        """
        if not matches:
            return []

        top_match = matches[0]
        reasoning = [f"Matched symptom: {symptom}" for symptom in top_match.matched_symptoms]

        logger.info(
            "Explanation generated for top match '%s': %d matched symptom(s).",
            top_match.disease.disease, len(reasoning),
        )
        return reasoning
