"""
Emergency detection engine.

Checks extracted symptoms against a curated set of potentially
life-threatening symptom patterns. This runs immediately after symptom
extraction and BEFORE disease matching in the pipeline - the spec is
explicit that "Emergency detection must run before disease prediction" (this
takes precedence over the looser ordering implied by the RAG flow diagram,
which lists severity/emergency after matching; the explicit ordering
requirement wins).

Detection is intentionally a static, explainable lookup (not inferred from
disease matches) so it cannot be delayed by, or made dependent on, the
disease-matching step - an emergency symptom must be flagged even if it
happens to match no disease in the knowledge base at all.
"""

import logging
from typing import List

from app.core.constants import EMERGENCY_ALERT_MESSAGE, EMERGENCY_SYMPTOMS
from app.schemas.symptom import EmergencyAssessment

logger = logging.getLogger("medical_ai")


class EmergencyDetectionService:
    def __init__(self) -> None:
        self._emergency_symptoms = EMERGENCY_SYMPTOMS

    def detect(self, symptoms: List[str]) -> EmergencyAssessment:
        """Check a list of extracted symptoms for emergency-indicating patterns."""
        normalized = {s.strip().lower() for s in symptoms}
        matched = sorted(normalized & self._emergency_symptoms)

        if matched:
            logger.warning("EMERGENCY DETECTED. Matched emergency symptom(s): %s", matched)
            return EmergencyAssessment(
                emergency=True,
                alert=EMERGENCY_ALERT_MESSAGE,
                matched_emergency_symptoms=matched,
            )

        return EmergencyAssessment(emergency=False, alert=None, matched_emergency_symptoms=[])
