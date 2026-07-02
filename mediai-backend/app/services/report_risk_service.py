"""
Risk assessment engine (Module 3, Step 5).

Rule-based: each rule inspects the raw parameter value (not just its
LOW/NORMAL/HIGH band) so thresholds can differ from the simple reference
range where clinically appropriate - e.g. glucose's normal range tops out
at 99, but the spec's own Prediabetes/Diabetes split sits at 100-125 and
126+, which is more specific than a single HIGH band would allow.

Each rule is a small, independent function so new rules can be added
without touching existing ones (OCP).
"""

import logging
from typing import Callable, Dict, List, Optional

from app.schemas.report_response import RiskAssessment

logger = logging.getLogger("report_analysis")


def _glucose_risk(value: float) -> Optional[RiskAssessment]:
    if value >= 126:
        return RiskAssessment(risk="Diabetes Risk", severity="High", based_on=["glucose"])
    if value >= 100:
        return RiskAssessment(risk="Prediabetes Risk", severity="Moderate", based_on=["glucose"])
    return None


def _hba1c_risk(value: float) -> Optional[RiskAssessment]:
    if value >= 6.5:
        return RiskAssessment(risk="Diabetes Risk", severity="High", based_on=["hba1c"])
    if value >= 5.7:
        return RiskAssessment(risk="Prediabetes Risk", severity="Moderate", based_on=["hba1c"])
    return None


def _hemoglobin_risk(value: float) -> Optional[RiskAssessment]:
    if value < 13.0:
        severity = "High" if value < 9.0 else "Moderate"
        return RiskAssessment(risk="Anemia Risk", severity=severity, based_on=["hemoglobin"])
    return None


def _ldl_risk(value: float) -> Optional[RiskAssessment]:
    if value >= 160:
        return RiskAssessment(risk="Cardiovascular Risk", severity="High", based_on=["ldl"])
    if value > 100:
        return RiskAssessment(risk="Cardiovascular Risk", severity="Moderate", based_on=["ldl"])
    return None


def _triglycerides_risk(value: float) -> Optional[RiskAssessment]:
    if value >= 200:
        return RiskAssessment(risk="Cardiovascular Risk", severity="Moderate", based_on=["triglycerides"])
    return None


def _tsh_risk(value: float) -> Optional[RiskAssessment]:
    if value > 4.0:
        return RiskAssessment(risk="Hypothyroidism Risk", severity="Moderate", based_on=["tsh"])
    if value < 0.4:
        return RiskAssessment(risk="Hyperthyroidism Risk", severity="Moderate", based_on=["tsh"])
    return None


def _creatinine_risk(value: float) -> Optional[RiskAssessment]:
    if value > 1.3:
        severity = "High" if value > 2.0 else "Moderate"
        return RiskAssessment(risk="Kidney Function Risk", severity=severity, based_on=["creatinine"])
    return None


def _uric_acid_risk(value: float) -> Optional[RiskAssessment]:
    if value > 7.2:
        return RiskAssessment(risk="Gout Risk", severity="Low", based_on=["uric_acid"])
    return None


def _liver_enzyme_risk(parameter_name: str) -> Callable[[float], Optional[RiskAssessment]]:
    def _check(value: float) -> Optional[RiskAssessment]:
        upper_bound = 56 if parameter_name == "sgpt" else 40
        if value > upper_bound:
            severity = "High" if value > upper_bound * 2 else "Moderate"
            return RiskAssessment(risk="Liver Function Risk", severity=severity, based_on=[parameter_name])
        return None
    return _check


def _bilirubin_risk(value: float) -> Optional[RiskAssessment]:
    if value > 1.2:
        return RiskAssessment(risk="Liver Function Risk", severity="Moderate", based_on=["bilirubin"])
    return None


def _platelet_risk(value: float) -> Optional[RiskAssessment]:
    if value < 150000:
        return RiskAssessment(risk="Thrombocytopenia Risk", severity="Moderate", based_on=["platelet_count"])
    if value > 450000:
        return RiskAssessment(risk="Thrombocytosis Risk", severity="Low", based_on=["platelet_count"])
    return None


_RISK_RULES: Dict[str, Callable[[float], Optional[RiskAssessment]]] = {
    "glucose": _glucose_risk,
    "hba1c": _hba1c_risk,
    "hemoglobin": _hemoglobin_risk,
    "ldl": _ldl_risk,
    "triglycerides": _triglycerides_risk,
    "tsh": _tsh_risk,
    "creatinine": _creatinine_risk,
    "uric_acid": _uric_acid_risk,
    "sgot": _liver_enzyme_risk("sgot"),
    "sgpt": _liver_enzyme_risk("sgpt"),
    "bilirubin": _bilirubin_risk,
    "platelet_count": _platelet_risk,
}


_SEVERITY_RANK = {"Low": 0, "Moderate": 1, "High": 2}


def _merge_duplicate_risks(risks: List[RiskAssessment]) -> List[RiskAssessment]:
    """Merge risks with the same name (e.g. glucose and hba1c can each
    independently trigger "Diabetes Risk") into one entry, combining their
    triggering parameters and keeping the higher severity."""
    merged: Dict[str, RiskAssessment] = {}
    for risk in risks:
        existing = merged.get(risk.risk)
        if existing is None:
            merged[risk.risk] = risk
            continue
        higher_severity = (
            risk.severity
            if _SEVERITY_RANK.get(risk.severity, 0) > _SEVERITY_RANK.get(existing.severity, 0)
            else existing.severity
        )
        merged[risk.risk] = RiskAssessment(
            risk=risk.risk,
            severity=higher_severity,
            based_on=sorted(set(existing.based_on) | set(risk.based_on)),
        )
    return list(merged.values())


class ReportRiskService:
    def assess(self, parameters: Dict[str, float]) -> List[RiskAssessment]:
        """Run all applicable risk rules against the detected parameter values.

        Operates on raw values (not just LOW/NORMAL/HIGH status) so each rule
        can apply its own clinically-appropriate threshold. Risks triggered
        by more than one parameter (e.g. glucose and hba1c both indicating
        diabetes risk) are merged into a single entry.
        """
        risks: List[RiskAssessment] = []
        for parameter_name, value in parameters.items():
            rule = _RISK_RULES.get(parameter_name)
            if rule is None:
                continue
            risk = rule(value)
            if risk is not None:
                risks.append(risk)

        risks = _merge_duplicate_risks(risks)

        if risks:
            logger.info("Identified %d risk(s): %s", len(risks), [r.risk for r in risks])
        return risks
