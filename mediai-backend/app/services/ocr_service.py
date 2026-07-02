"""
OCR engine (Module 6).

Primary: EasyOCR (deep-learning-based, handles printed and handwritten text,
works well on noisy scans). Tesseract is the fallback for environments where
EasyOCR cannot run (missing GPU or memory constraints) or when EasyOCR
returns no results.

The singleton pattern here mirrors EmbeddingService - EasyOCR's Reader
object is expensive to initialize (loads neural network weights) so it is
created once and reused for all subsequent calls.

Returns both extracted text and a mean confidence score (0-100) so callers
can decide how much to trust the result and surface it in the API response.
"""

import logging
import threading
from typing import Optional, Tuple

import numpy as np

from app.core.exceptions import OCRError

logger = logging.getLogger("ocr")


class OCRService:
    _instance: Optional["OCRService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "OCRService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._reader = None
                    instance._reader_lock = threading.Lock()
                    cls._instance = instance
        return cls._instance

    def _get_reader(self):
        """Lazily initialize EasyOCR reader (thread-safe)."""
        if self._reader is None:
            with self._reader_lock:
                if self._reader is None:
                    try:
                        import easyocr
                        logger.info("Initializing EasyOCR reader (first use - loading model weights)...")
                        self._reader = easyocr.Reader(["en"], gpu=False, verbose=False)
                        logger.info("EasyOCR reader initialized.")
                    except Exception as exc:
                        logger.error("Failed to initialize EasyOCR: %s", exc)
                        self._reader = None
        return self._reader

    def _ocr_with_easyocr(self, image: np.ndarray) -> Tuple[str, float]:
        """Run EasyOCR on a preprocessed image array.
        Returns (text, mean_confidence_0_to_100)."""
        reader = self._get_reader()
        if reader is None:
            raise RuntimeError("EasyOCR reader unavailable.")

        results = reader.readtext(image, detail=1, paragraph=False)
        if not results:
            return "", 0.0

        lines = []
        confidences = []
        for _bbox, text, confidence in results:
            stripped = text.strip()
            if stripped:
                lines.append(stripped)
                confidences.append(float(confidence))

        combined_text = "\n".join(lines)
        mean_confidence = (sum(confidences) / len(confidences) * 100) if confidences else 0.0
        return combined_text, round(mean_confidence, 2)

    def _ocr_with_tesseract(self, image: np.ndarray) -> Tuple[str, float]:
        """Tesseract fallback. Returns (text, 0.0) — Tesseract's word-level
        confidence requires additional per-word querying which we skip for
        the fallback path, returning 0.0 as the confidence sentinel."""
        import pytesseract
        config = "--oem 3 --psm 6"
        text = pytesseract.image_to_string(image, lang="eng", config=config)
        return text.strip(), 0.0

    def extract_text(self, image: np.ndarray) -> Tuple[str, float]:
        """Extract text from a preprocessed image (numpy array).

        Returns:
            (text, ocr_confidence) where confidence is 0-100. Raises
            OCRError if both engines fail to extract any usable text.
        """
        # Primary: EasyOCR
        try:
            text, confidence = self._ocr_with_easyocr(image)
            if text.strip():
                logger.info("EasyOCR extracted %d chars, confidence=%.1f%%", len(text), confidence)
                logger.debug("EasyOCR raw text:\n%s", text)
                return text, confidence
            logger.warning("EasyOCR returned no text. Falling back to Tesseract.")
        except Exception as exc:
            logger.warning("EasyOCR failed (%s). Falling back to Tesseract.", exc)

        # Fallback: Tesseract
        try:
            text, confidence = self._ocr_with_tesseract(image)
            if text.strip():
                logger.info("Tesseract fallback extracted %d chars.", len(text))
                logger.debug("Tesseract raw text:\n%s", text)
                return text, confidence
        except Exception as exc:
            logger.error("Tesseract fallback also failed: %s", exc)

        raise OCRError(
            "OCR could not extract any usable text from this image. "
            "Ensure the image is a clear, well-lit scan of a printed medical report."
        )

    def is_available(self) -> bool:
        """Check whether at least one OCR engine is available."""
        try:
            self._get_reader()
            if self._reader is not None:
                return True
        except Exception:
            pass
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
