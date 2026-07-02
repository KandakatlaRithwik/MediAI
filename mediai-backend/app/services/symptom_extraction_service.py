"""
Symptom extraction engine.

Extracts a normalized, de-duplicated list of *known* symptoms (i.e. terms
that DiseaseMatchingService can actually act on) from free-text user input
such as "I have fever, cough and headache."

Matching strategy:
  1. Normalize the input: lowercase, strip punctuation, collapse whitespace.
  2. Exact phrase matching against the symptom vocabulary derived from the
     disease knowledge base, scanned left-to-right so results preserve the
     order symptoms appear in the input text. Multi-word symptoms (e.g.
     "frequent urination") are matched preferentially over any of their
     individual words via a single alternation regex ordered longest-first.
  3. Typo-tolerant matching on whatever words/word-pairs are left over,
     using a similarity cutoff (difflib) against the same vocabulary.
  4. De-duplicate while preserving first-seen order.
"""

import logging
import re
from difflib import get_close_matches
from typing import List, Set, Tuple

from app.services.disease_matching_service import load_disease_dataset

logger = logging.getLogger(__name__)

_NON_ALPHANUMERIC_PATTERN = re.compile(r"[^a-z0-9\s]")
_WHITESPACE_PATTERN = re.compile(r"\s+")
_FUZZY_MATCH_CUTOFF = 0.84
_MIN_FUZZY_WORD_LENGTH = 3


class SymptomExtractionService:
    def __init__(self) -> None:
        self._vocabulary: Set[str] = self._build_vocabulary()
        self._phrase_pattern = self._build_phrase_pattern(self._vocabulary)

    @staticmethod
    def _build_vocabulary() -> Set[str]:
        vocabulary: Set[str] = set()
        for disease in load_disease_dataset():
            vocabulary.update(disease.symptoms)
            # Emergency flags are themselves symptom-like phrases (e.g. "facial
            # drooping", "suicidal ideation") that may not appear in any
            # disease's regular symptom list verbatim. Including them here
            # lets EmergencyDetectionService recognize them when present in
            # free text, even if they weren't already part of a symptom list.
            vocabulary.update(disease.emergency_flags)
        return vocabulary

    @staticmethod
    def _build_phrase_pattern(vocabulary: Set[str]) -> re.Pattern:
        # Longest phrases first so overlapping alternatives prefer the more
        # specific (multi-word) match, e.g. "persistent cough" over "cough".
        ordered_phrases = sorted(vocabulary, key=len, reverse=True)
        escaped = [re.escape(phrase) for phrase in ordered_phrases]
        return re.compile(r"\b(" + "|".join(escaped) + r")\b")

    @staticmethod
    def _normalize(text: str) -> str:
        lowered = text.lower()
        no_punctuation = _NON_ALPHANUMERIC_PATTERN.sub(" ", lowered)
        return _WHITESPACE_PATTERN.sub(" ", no_punctuation).strip()

    @staticmethod
    def _mask_spans(text: str, spans: List[Tuple[int, int]]) -> str:
        """Blank out already-matched spans so typo-tolerant matching only
        looks at text that wasn't already identified as a known symptom."""
        chars = list(text)
        for start, end in spans:
            for i in range(start, end):
                chars[i] = " "
        return "".join(chars)

    def extract(self, text: str) -> List[str]:
        """Extract known symptoms from free-text input.

        Returns a de-duplicated list of symptom names, in the order they
        first appear in the input text.
        """
        if not text or not text.strip():
            return []

        normalized = self._normalize(text)
        found: List[str] = []
        seen: Set[str] = set()
        covered_spans: List[Tuple[int, int]] = []

        # Pass 1: exact phrase matching, scanned left-to-right.
        for match in self._phrase_pattern.finditer(normalized):
            symptom = match.group(1)
            covered_spans.append(match.span())
            if symptom not in seen:
                found.append(symptom)
                seen.add(symptom)

        # Pass 2: typo-tolerant matching on whatever wasn't matched above.
        leftover_text = self._mask_spans(normalized, covered_spans)
        leftover_words = [w for w in leftover_text.split() if len(w) >= _MIN_FUZZY_WORD_LENGTH]
        candidates = leftover_words + [
            f"{first} {second}" for first, second in zip(leftover_words, leftover_words[1:])
        ]

        for candidate in candidates:
            close_matches = get_close_matches(candidate, self._vocabulary, n=1, cutoff=_FUZZY_MATCH_CUTOFF)
            if close_matches and close_matches[0] not in seen:
                matched_symptom = close_matches[0]
                found.append(matched_symptom)
                seen.add(matched_symptom)
                logger.info("Typo-tolerant symptom match: '%s' -> '%s'", candidate, matched_symptom)

        return found
