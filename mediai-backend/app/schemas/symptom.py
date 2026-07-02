"""Request/response schemas for the Symptom Checker endpoint (Module 2.5)."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.disease import PossibleDisease


class SymptomCheckRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=3,
        max_length=2000,
        description="Free-text description of symptoms, e.g. 'I have fever, cough and headache.'",
    )

    model_config = {
        "json_schema_extra": {
            "example": {"text": "I have fever cough headache body pain"}
        }
    }


class SymptomExtractionResult(BaseModel):
    """Standalone shape for the symptom-extraction step, useful for debugging/testing."""

    symptoms: List[str] = Field(default_factory=list, description="Normalized, de-duplicated extracted symptoms.")


class EmergencyAssessment(BaseModel):
    emergency: bool = Field(..., description="Whether a potentially life-threatening symptom pattern was detected.")
    alert: Optional[str] = Field(
        default=None, description="Emergency alert message, present only when emergency is true."
    )
    matched_emergency_symptoms: List[str] = Field(
        default_factory=list, description="The specific emergency-indicating symptoms that were detected."
    )


class SymptomCheckerResponse(BaseModel):
    """Upgraded Module 2.5 symptom-checker response.

    Pipeline: extraction -> emergency detection -> Jaccard disease matching ->
    severity prediction -> explanation -> specialist recommendation.
    """

    symptoms: List[str] = Field(
        default_factory=list, description="Symptoms recognized in the input text."
    )
    possible_diseases: List[PossibleDisease] = Field(
        default_factory=list, description="Top candidate diseases ranked by Jaccard confidence, highest first."
    )
    severity: str = Field(..., description="Overall predicted severity: Mild, Moderate, Severe, or Emergency.")
    emergency: bool = Field(..., description="True if a potentially life-threatening symptom pattern was detected.")
    recommended_specialist: str = Field(
        ..., description="The medical specialist recommended based on the top match (or General Physician)."
    )
    reasoning: List[str] = Field(
        default_factory=list, description="Human-readable explanation of why the top disease(s) were predicted."
    )
    disclaimer: str = Field(
        ..., description="Mandatory safety disclaimer - this is a screening aid, not a diagnosis."
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "symptoms": ["fever", "cough", "headache", "body pain"],
                "possible_diseases": [
                    {
                        "disease": "Flu",
                        "score": 0.83,
                        "confidence": 83,
                        "level": "High",
                        "category": "Infectious Diseases",
                        "specialist": "General Physician",
                        "severity": "medium",
                        "matched_symptoms": ["fever", "cough", "headache", "body pain"],
                    },
                    {
                        "disease": "COVID-19",
                        "score": 0.5,
                        "confidence": 50,
                        "level": "Moderate",
                        "category": "Infectious Diseases",
                        "specialist": "General Physician",
                        "severity": "high",
                        "matched_symptoms": ["fever", "cough", "body pain"],
                    },
                ],
                "severity": "Moderate",
                "emergency": False,
                "recommended_specialist": "General Physician",
                "reasoning": [
                    "Matched symptom: fever",
                    "Matched symptom: cough",
                    "Matched symptom: headache",
                    "Matched symptom: body pain",
                ],
                "disclaimer": (
                    "This is an AI-generated health assessment and not a medical diagnosis. "
                    "Consult a qualified healthcare professional for medical advice."
                ),
            }
        }
    }
