"""Response schema for POST /analyze-image-report (Module 6)."""

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.report_response import ReportParameter, RiskAssessment


class OCRReportResponse(BaseModel):
    ocr_text: str = Field(..., description="Raw text extracted from the image/scanned PDF by OCR.")
    ocr_confidence: float = Field(..., ge=0.0, le=100.0, description="Mean OCR confidence score (0-100).")
    report_type: str = Field(..., description="Inferred report type, e.g. 'Blood Sugar Report'.")
    parameters: List[ReportParameter] = Field(default_factory=list, description="All detected lab parameters.")
    abnormal_parameters: List[str] = Field(default_factory=list, description="Parameter names outside normal range.")
    risk_assessment: List[RiskAssessment] = Field(default_factory=list, description="Identified health risks.")
    ai_summary: str = Field(..., description="Plain-English AI explanation of findings.")
    disclaimer: str = Field(..., description="Mandatory safety disclaimer.")

    model_config = {
        "json_schema_extra": {
            "example": {
                "ocr_text": "BLOOD SUGAR REPORT\nFasting Blood Sugar: 145 mg/dL\nHbA1c: 6.8 %",
                "ocr_confidence": 92.4,
                "report_type": "Blood Sugar Report",
                "parameters": [
                    {"name": "glucose", "value": 145, "unit": "mg/dL", "status": "HIGH", "reference_min": 70, "reference_max": 99}
                ],
                "abnormal_parameters": ["glucose"],
                "risk_assessment": [{"risk": "Prediabetes Risk", "severity": "Moderate", "based_on": ["glucose"]}],
                "ai_summary": "Your glucose level is elevated...",
                "disclaimer": "This analysis is informational only and not a medical diagnosis.",
            }
        }
    }
