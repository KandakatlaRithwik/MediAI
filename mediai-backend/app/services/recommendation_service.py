"""
Specialist recommendation engine.

Determines which medical specialist to recommend, based on the ranked
disease predictions produced by either DiseaseMatchingService (Module 2,
simple overlap ratio) or AdvancedMatchingService (Module 2.5, Jaccard
similarity). Both produce match objects exposing a `.disease` attribute
(a DiseaseRecord), so this works unmodified against either via duck typing.
Falls back to a General Physician whenever no disease could be confidently
matched - the safe default for ambiguous, mild, or unrecognized symptom
combinations.
"""

import logging
from typing import Any, Sequence

from app.core.constants import DEFAULT_SPECIALIST

logger = logging.getLogger(__name__)


class RecommendationService:
    def recommend_specialist(self, ranked_matches: Sequence[Any]) -> str:
        """Recommend a specialist based on the single most likely disease match.

        Ranked matches are assumed to already be sorted highest-confidence
        first (both matching services guarantee this), so the top-ranked
        match's specialist is always the recommendation - no separate
        escalation/consensus logic, by design: it would let a lower-ranked,
        lower-confidence match silently override the leading prediction.
        """
        if not ranked_matches:
            return DEFAULT_SPECIALIST

        top_match = ranked_matches[0]
        return top_match.disease.specialist or DEFAULT_SPECIALIST
