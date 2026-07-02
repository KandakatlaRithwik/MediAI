"""
Schemas for disease knowledge-base records and disease match results.

`DiseaseRecord` validates entries loaded from `app/data/diseases.json`.
`PossibleDisease` is the API-facing shape returned to clients once a match
has been scored by `ConfidenceService`.
"""

from typing import List, Literal

from pydantic import BaseModel, Field

Severity = Literal["low", "medium", "high"]


class DiseaseRecord(BaseModel):
    """A single entry in the disease knowledge base."""

    disease: str = Field(..., description="Disease name.")
    category: str = Field(..., description="Medical category, e.g. Cardiology, Neurology.")
    symptoms: List[str] = Field(..., description="Symptoms associated with this disease (lowercase).")
    risk_factors: List[str] = Field(
        default_factory=list, description="Factors that increase likelihood of this disease (lowercase)."
    )
    specialist: str = Field(..., description="Medical specialist typically consulted for this disease.")
    severity: Severity = Field(..., description="Relative severity: low, medium, or high.")
    description: str = Field(..., description="Short, plain-language description of the condition.")
    emergency_flags: List[str] = Field(
        default_factory=list,
        description="Symptoms that, if present alongside this disease, indicate a medical emergency.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "disease": "Diabetes",
                "category": "Endocrinology",
                "symptoms": ["frequent urination", "increased thirst", "fatigue", "blurred vision"],
                "risk_factors": ["obesity", "family history"],
                "specialist": "Endocrinologist",
                "severity": "medium",
                "description": "Chronic condition affecting blood sugar regulation.",
                "emergency_flags": ["confusion", "loss of consciousness"],
            }
        }
    }


class PossibleDisease(BaseModel):
    """A single ranked disease prediction returned by the advanced (Jaccard) matching engine."""

    disease: str = Field(..., description="Disease name.")
    score: float = Field(..., ge=0.0, le=1.0, description="Raw Jaccard similarity score (intersection/union), 0.0-1.0.")
    confidence: int = Field(..., ge=0, le=100, description="Confidence score from 0-100 (score * 100, rounded).")
    level: str = Field(..., description="Confidence level label (Very High / High / Moderate / Low / Very Low).")
    category: str = Field(..., description="Medical category this disease belongs to.")
    specialist: str = Field(..., description="Recommended specialist for this specific disease.")
    severity: Severity = Field(..., description="Relative severity of this disease.")
    matched_symptoms: List[str] = Field(
        default_factory=list,
        description="Symptoms from the user's input that matched this disease's known symptom list.",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "disease": "Influenza",
                "score": 0.87,
                "confidence": 87,
                "level": "High",
                "category": "Infectious Diseases",
                "specialist": "General Physician",
                "severity": "medium",
                "matched_symptoms": ["fever", "cough", "headache", "body pain"],
            }
        }
    }
