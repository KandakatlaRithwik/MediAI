"""
Tests for Module 6: OCR Medical Report Processing.

Uses a synthetic in-memory image (generated with OpenCV/numpy) so no
external fixture files are required and tests run fully offline.
EasyOCR model weights cannot be downloaded in a network-restricted
environment, so all OCR tests exercise the Tesseract fallback path
directly - which is itself a fully real code path, not a mock.
"""

import io
import os

import cv2
import numpy as np
import pytest

from app.services.image_preprocessing_service import ImagePreprocessingService
from app.services.ocr_service import OCRService


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_report_image(lines: list[str]) -> np.ndarray:
    """Create a white-background BGR image with the given text lines."""
    img = np.ones((400, 900, 3), dtype=np.uint8) * 255
    for i, line in enumerate(lines):
        cv2.putText(img, line, (30, 80 + i * 70), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
    return img


def _save_image(img: np.ndarray, path: str) -> str:
    cv2.imwrite(path, img)
    return path


# ── ImagePreprocessingService ────────────────────────────────────────────────

class TestImagePreprocessingService:
    def test_grayscale_conversion(self):
        svc = ImagePreprocessingService()
        colour_img = _make_report_image(["test"])
        result = svc.preprocess(colour_img, denoise=False, enhance_contrast=False, apply_threshold=False)
        assert len(result.shape) == 2  # 2D = grayscale

    def test_output_is_uint8(self):
        svc = ImagePreprocessingService()
        img = _make_report_image(["test"])
        result = svc.preprocess(img)
        assert result.dtype == np.uint8

    def test_small_image_is_upscaled(self):
        svc = ImagePreprocessingService()
        small_img = np.ones((100, 200, 3), dtype=np.uint8) * 255
        result = svc.preprocess(small_img, target_dpi_width=2480)
        assert result.shape[1] >= 2480

    def test_already_large_image_is_not_upscaled(self):
        svc = ImagePreprocessingService()
        large_img = np.ones((1200, 3000, 3), dtype=np.uint8) * 255
        result = svc.preprocess(large_img, target_dpi_width=2480)
        assert result.shape[1] == 3000

    def test_load_image_from_file(self, tmp_path):
        svc = ImagePreprocessingService()
        img = _make_report_image(["glucose 145"])
        path = str(tmp_path / "test.png")
        cv2.imwrite(path, img)
        loaded = svc.load_image(path)
        assert loaded is not None
        assert loaded.shape == img.shape

    def test_load_nonexistent_file_returns_none(self):
        svc = ImagePreprocessingService()
        result = svc.load_image("/nonexistent/path/image.png")
        assert result is None


# ── OCRService (Tesseract path) ──────────────────────────────────────────────

class TestOCRService:
    def test_tesseract_extracts_text_from_synthetic_image(self):
        svc = OCRService()
        img = _make_report_image(["Glucose: 145"])
        preprocessed = ImagePreprocessingService().preprocess(img)
        text, confidence = svc._ocr_with_tesseract(preprocessed)
        assert "145" in text.replace(" ", "")

    def test_tesseract_returns_zero_confidence_sentinel(self):
        svc = OCRService()
        img = _make_report_image(["TSH: 8.4"])
        preprocessed = ImagePreprocessingService().preprocess(img)
        _, confidence = svc._ocr_with_tesseract(preprocessed)
        assert confidence == 0.0

    def test_extract_text_returns_tuple(self):
        svc = OCRService()
        img = _make_report_image(["Hemoglobin: 11.2"])
        preprocessed = ImagePreprocessingService().preprocess(img)
        result = svc.extract_text(preprocessed)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_ocr_service_is_available(self):
        svc = OCRService()
        assert svc.is_available() is True


# ── /analyze-image-report endpoint ──────────────────────────────────────────

class TestAnalyzeImageReportEndpoint:
    def test_blood_sugar_image_report_recognized(self, client, tmp_path):
        img = _make_report_image(["Fasting Blood Sugar: 145 mg/dL", "HbA1c: 6.8 %"])
        path = str(tmp_path / "bs_report.png")
        cv2.imwrite(path, img)
        with open(path, "rb") as f:
            response = client.post("/analyze-image-report", files={"file": ("report.png", f, "image/png")})
        assert response.status_code == 200
        body = response.json()
        assert body["report_type"] == "Blood Sugar Report"
        assert any(p["name"] == "glucose" and p["status"] == "HIGH" for p in body["parameters"])
        assert "glucose" in body["abnormal_parameters"]
        assert "ocr_confidence" in body
        assert isinstance(body["ocr_text"], str) and len(body["ocr_text"]) > 0
        assert body["disclaimer"] == "This analysis is informational only and not a medical diagnosis."

    def test_jpeg_image_accepted(self, client, tmp_path):
        img = _make_report_image(["Glucose: 85 mg/dL"])
        path = str(tmp_path / "report.jpg")
        cv2.imwrite(path, img)
        with open(path, "rb") as f:
            response = client.post("/analyze-image-report", files={"file": ("report.jpg", f, "image/jpeg")})
        assert response.status_code in (200, 422)  # 422 if OCR reads nothing parseable from jpeg

    def test_unsupported_extension_rejected(self, client):
        response = client.post(
            "/analyze-image-report",
            files={"file": ("report.docx", b"not a real file", "application/octet-stream")},
        )
        assert response.status_code == 400

    def test_empty_file_rejected(self, client):
        response = client.post(
            "/analyze-image-report",
            files={"file": ("report.png", b"", "image/png")},
        )
        assert response.status_code == 400
