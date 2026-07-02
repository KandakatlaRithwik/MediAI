"""
Reference range engine (Module 3, Step 3).

Loads app/data/reference_ranges.json and compares parameter values against
the configured normal range, returning LOW / NORMAL / HIGH. Also infers an
overall report-type label (e.g. "Blood Sugar Report") from whichever
category the majority of detected parameters belong to.
"""

import json
import logging
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from app.core.constants import DEFAULT_REPORT_TYPE_LABEL
from app.core.exceptions import KnowledgeBaseError

logger = logging.getLogger("report_analysis")

_RANGES_PATH = Path(__file__).resolve().parent.parent / "data" / "reference_ranges.json"


@lru_cache()
def load_reference_ranges() -> Dict[str, dict]:
    """Load and cache the parameter -> {min, max, unit, report_type} mapping."""
    try:
        with open(_RANGES_PATH, "r", encoding="utf-8") as ranges_file:
            raw_ranges = json.load(ranges_file)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Failed to load reference ranges from %s: %s", _RANGES_PATH, exc)
        raise KnowledgeBaseError(f"Failed to load reference ranges: {exc}") from exc

    if not raw_ranges:
        raise KnowledgeBaseError("Reference ranges dataset is empty.")

    return raw_ranges


@dataclass
class RangeComparison:
    status: str  # "LOW" | "NORMAL" | "HIGH"
    unit: Optional[str]
    reference_min: Optional[float]
    reference_max: Optional[float]


class MedicalRangeService:
    def __init__(self) -> None:
        self._ranges = load_reference_ranges()

    def compare(self, parameter_name: str, value: float) -> RangeComparison:
        """Compare a single value against its configured reference range.

        Parameters with no configured range (shouldn't normally happen,
        since ReportParserService only emits canonical names that exist in
        reference_ranges.json) are reported as NORMAL with no bounds,
        rather than raising - a missing range should never block the rest
        of the analysis.
        """
        range_info = self._ranges.get(parameter_name)
        if not range_info:
            logger.warning("No reference range configured for parameter '%s'.", parameter_name)
            return RangeComparison(status="NORMAL", unit=None, reference_min=None, reference_max=None)

        minimum = range_info.get("min")
        maximum = range_info.get("max")

        if minimum is not None and value < minimum:
            status = "LOW"
        elif maximum is not None and value > maximum:
            status = "HIGH"
        else:
            status = "NORMAL"

        return RangeComparison(
            status=status, unit=range_info.get("unit"), reference_min=minimum, reference_max=maximum
        )

    def infer_report_type(self, parameter_names: List[str]) -> str:
        """Infer the overall report type from whichever category the majority
        of detected parameters belong to (e.g. mostly CBC params -> 'CBC Report')."""
        if not parameter_names:
            return DEFAULT_REPORT_TYPE_LABEL

        categories = [
            self._ranges[name]["report_type"]
            for name in parameter_names
            if name in self._ranges and "report_type" in self._ranges[name]
        ]
        if not categories:
            return DEFAULT_REPORT_TYPE_LABEL

        most_common_category, _ = Counter(categories).most_common(1)[0]
        return f"{most_common_category} Report"
