"""
Report parameter detection engine (Module 3, Step 2).

Detects medical lab values from raw report text using regex, matching each
canonical parameter (as defined in app/data/reference_ranges.json) against
a configurable list of common aliases/abbreviations actually used on lab
report printouts (e.g. "Hb" for hemoglobin, "FBS" for fasting glucose).

Patterns are applied line-by-line rather than against the whole text blob:
lab reports are typically laid out as one parameter per line, and matching
line-by-line avoids one greedy match accidentally spanning unrelated lines
in a malformed/poorly-structured extraction.
"""

import logging
import re
from typing import Dict, List, Pattern

logger = logging.getLogger("report_analysis")

# Canonical parameter name -> alternative labels seen on real report printouts.
# Longest aliases are tried first per parameter so "fasting blood sugar"
# matches before the more generic "blood sugar".
PARAMETER_ALIASES: Dict[str, List[str]] = {
    "hemoglobin": ["hemoglobin", "haemoglobin", "hb", "hgb"],
    "wbc_count": ["total leucocyte count", "white blood cell count", "wbc count", "wbc", "tlc"],
    "rbc_count": ["red blood cell count", "rbc count", "rbc"],
    "platelet_count": ["platelet count", "platelets", "plt"],
    "hematocrit": ["hematocrit", "haematocrit", "pcv", "hct"],
    "mcv": ["mcv"],
    "mch": ["mch"],
    "mchc": ["mchc"],
    "glucose": [
        "fasting blood sugar", "fasting blood glucose", "fasting glucose",
        "blood glucose", "blood sugar", "glucose", "fbs", "f.b.s", "gluc",
    ],
    "postprandial_glucose": [
        "post prandial blood sugar", "postprandial blood sugar", "post-prandial blood sugar",
        "postprandial glucose", "post prandial glucose", "pp blood sugar", "ppbs", "pp",
    ],
    "random_glucose": [
        "random blood sugar", "random blood glucose", "random glucose", "rbs",
    ],
    "hba1c": [
        "glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c",
        "hba1c", "hb a1c", "hbaic", "a1c",
    ],
    "estimated_average_glucose": [
        "estimated average glucose", "average glucose", "eag",
    ],
    "cholesterol": ["total cholesterol", "cholesterol"],
    "ldl": ["ldl cholesterol", "low density lipoprotein", "ldl"],
    "hdl": ["hdl cholesterol", "high density lipoprotein", "hdl"],
    "triglycerides": ["triglycerides", "triglyceride", "tg", "trig"],
    "vldl": ["vldl"],
    "tsh": ["thyroid stimulating hormone", "tsh", "s.tsh", "s tsh"],
    "t3": ["total triiodothyronine", "triiodothyronine", "t3", "tt3"],
    "t4": ["total thyroxine", "thyroxine", "t4", "tt4"],
    "free_t3": ["free t3", "ft3"],
    "free_t4": ["free t4", "ft4"],
    "creatinine": ["serum creatinine", "s. creatinine", "creatinine"],
    "urea": ["blood urea nitrogen", "blood urea", "urea", "bun"],
    "bun": ["blood urea nitrogen", "bun"],
    "uric_acid": ["serum uric acid", "uric acid"],
    "sodium": ["serum sodium", "sodium", "na+", "na"],
    "potassium": ["serum potassium", "potassium", "k+", "k"],
    "chloride": ["serum chloride", "chloride", "cl-", "cl"],
    "calcium": ["serum calcium", "calcium", "ca++", "ca"],
    "sgot": ["aspartate aminotransferase", "sgot", "ast"],
    "sgpt": ["alanine aminotransferase", "sgpt", "alt"],
    "ggt": ["gamma glutamyl transferase", "gamma-glutamyl transferase", "ggt", "ggtp"],
    "bilirubin": ["total bilirubin", "bilirubin"],
    "direct_bilirubin": ["direct bilirubin", "conjugated bilirubin", "d.bilirubin"],
    "indirect_bilirubin": ["indirect bilirubin", "unconjugated bilirubin"],
    "alkaline_phosphatase": ["alkaline phosphatase", "s. alkaline phosphatase", "alp"],
    "albumin": ["serum albumin", "albumin"],
    "total_protein": ["total protein", "s. total protein"],
    "globulin": ["globulin"],
}

_NUMBER_PATTERN = r"([\d,]+(?:\.\d+)?)"


def _compile_patterns() -> Dict[str, Pattern]:
    """Compile one alternation regex per canonical parameter from its aliases,
    longest alias first so more specific labels win over generic ones."""
    compiled: Dict[str, Pattern] = {}
    for canonical_name, aliases in PARAMETER_ALIASES.items():
        ordered_aliases = sorted(set(aliases), key=len, reverse=True)
        alias_group = "|".join(re.escape(alias) for alias in ordered_aliases)
        pattern = re.compile(
            rf"\b(?:{alias_group})\b\s*[:\-]?\s*{_NUMBER_PATTERN}",
            re.IGNORECASE,
        )
        compiled[canonical_name] = pattern
    return compiled


_COMPILED_PATTERNS = _compile_patterns()


class ReportParserService:
    def parse(self, raw_text: str) -> Dict[str, float]:
        """Extract {canonical_parameter_name: numeric_value} pairs from raw report text.

        Each parameter is matched against every line; the first match wins
        per parameter (duplicate mentions later in the report are ignored,
        consistent with how the rest of this codebase de-duplicates).
        """
        detected: Dict[str, float] = {}
        lines = raw_text.splitlines()

        for canonical_name, pattern in _COMPILED_PATTERNS.items():
            if canonical_name in detected:
                continue
            for line in lines:
                match = pattern.search(line)
                if not match:
                    continue
                raw_value = match.group(1).replace(",", "")
                try:
                    detected[canonical_name] = float(raw_value)
                except ValueError:
                    continue
                break

        logger.info("Parsed %d parameter(s) from report: %s", len(detected), sorted(detected.keys()))
        return detected
