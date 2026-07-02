"""Tests for ReportExtractionService."""

import os

import pytest

from app.core.exceptions import DocumentProcessingError
from app.services.report_extraction_service import ReportExtractionService

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_extracts_text_from_pdf():
    service = ReportExtractionService()
    text = service.extract_text(os.path.join(FIXTURES_DIR, "blood_sugar_report.pdf"))
    assert "Fasting Blood Sugar" in text
    assert "145" in text


def test_extracts_text_from_txt():
    service = ReportExtractionService()
    text = service.extract_text(os.path.join(FIXTURES_DIR, "lft_report.txt"))
    assert "SGOT" in text


def test_unsupported_extension_raises():
    service = ReportExtractionService()
    with pytest.raises(DocumentProcessingError):
        service.extract_text("report.docx")


def test_image_extension_raises_not_yet_supported():
    service = ReportExtractionService()
    with pytest.raises(DocumentProcessingError):
        service.extract_text("report.png")
