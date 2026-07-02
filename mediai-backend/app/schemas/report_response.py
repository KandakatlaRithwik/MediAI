"""Response schemas for the Medical Report Analyzer."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

RangeStatus = Literal["LOW", "NORMAL", "HIGH"]


class ReportParameter(BaseModel):
    name: str = Field(..., description="Canonical parameter name, e.g. 'glucose'.")
    value: float = Field(..., description="Extracted numeric value.")
    unit: Optional[str] = Field(default=None, description="Unit of measurement, e.g. 'mg/dL'.")
    status: RangeStatus = Field(..., description="LOW, NORMAL, or HIGH relative to the reference range.")
    reference_min: Optional[float] = Field(default=None, description="Lower bound of the normal range.")
    reference_max: Optional[float] = Field(default=None, description="Upper bound of the normal range.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "glucose",
                "value": 145,
                "unit": "mg/dL",
                "status": "HIGH",
                "reference_min": 70,
                "reference_max": 99,
            }
        }
    }


class RiskAssessment(BaseModel):
    risk: str = Field(..., description="Identified health risk, e.g. 'Prediabetes Risk'.")
    severity: str = Field(..., description="Severity of the identified risk: Low, Moderate, or High.")
    based_on: List[str] = Field(
        default_factory=list, description="Parameter(s) that triggered this risk assessment."
    )

    model_config = {
        "json_schema_extra": {"example": {"risk": "Prediabetes Risk", "severity": "Moderate", "based_on": ["glucose"]}}
    }


class ReportAnalysisResponse(BaseModel):
    report_type: str = Field(..., description="Inferred report type, e.g. 'Blood Sugar Report'.")
    parameters: List[ReportParameter] = Field(default_factory=list, description="All detected lab parameters.")
    abnormal_parameters: List[str] = Field(
        default_factory=list, description="Names of parameters outside the normal range."
    )
    risk_assessment: List[RiskAssessment] = Field(
        default_factory=list, description="Identified health risks based on abnormal values."
    )
    ai_summary: str = Field(..., description="Plain-English AI explanation of the findings.")
    disclaimer: str = Field(..., description="Mandatory safety disclaimer.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_type": "Blood Sugar Report",
                "parameters": [
                    {
                        "name": "glucose",
                        "value": 145,
                        "unit": "mg/dL",
                        "status": "HIGH",
                        "reference_min": 70,
                        "reference_max": 99,
                    }
                ],
                "abnormal_parameters": ["glucose"],
                "risk_assessment": [{"risk": "Prediabetes Risk", "severity": "Moderate", "based_on": ["glucose"]}],
                "ai_summary": (
                    "Your glucose level is higher than the typical fasting range, which can be an early "
                    "indicator of prediabetes. This is not a diagnosis - please discuss these results with "
                    "a healthcare professional."
                ),
                "disclaimer": "This analysis is informational only and not a medical diagnosis.",
            }
        }
    }
