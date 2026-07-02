"""
Report image parser orchestrator (Module 6).

Bridges the OCR layer (Module 6) and the existing text-based report analysis
pipeline (Module 3). Given a path to an image file or a scanned-PDF page,
it applies preprocessing, runs OCR to extract text, and hands the extracted
text off to ReportParserService + the rest of the Module 3 pipeline.

This service is intentionally a thin orchestrator - it does not duplicate
any logic from Module 3; it only adds the image-to-text conversion step
that Module 3 previously could not do.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import cv2
import numpy as np

from app.core.constants import OCR_SUPPORTED_IMAGE_EXTENSIONS
from app.core.exceptions import DocumentProcessingError, OCRError
from app.schemas.report_response import ReportAnalysisResponse
from app.services.image_preprocessing_service import ImagePreprocessingService
from app.services.llm_service import LLMService
from app.services.medical_range_service import MedicalRangeService
from app.services.ocr_service import OCRService
from app.services.report_analysis_service import _build_report_context_block, get_report_context_store
from app.services.report_parser_service import ReportParserService
from app.services.report_risk_service import ReportRiskService
from app.core.constants import REPORT_ANALYSIS_DISCLAIMER

logger = logging.getLogger("ocr")


@dataclass
class OCRReportResult:
    """Extends ReportAnalysisResponse with OCR-specific metadata."""
    analysis: ReportAnalysisResponse
    ocr_text: str
    ocr_confidence: float


def _load_image_pages(file_path: str) -> List[np.ndarray]:
    """Load image pages from a file.

    - For standard images (JPG/PNG): returns a single-element list.
    - For PDFs containing scanned pages: converts each page to an image
      using pdfplumber + PIL (avoids a Poppler dependency). Returns a list
      of numpy arrays, one per page.
    """
    extension = Path(file_path).suffix.lower()

    if extension in OCR_SUPPORTED_IMAGE_EXTENSIONS:
        image = cv2.imread(file_path)
        if image is None:
            raise DocumentProcessingError(f"Cannot read image file: '{file_path}'.")
        return [image]

    if extension == ".pdf":
        try:
            import pdfplumber
            from PIL import Image

            pages = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    pil_img = page.to_image(resolution=300).original
                    np_img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    pages.append(np_img)
            if not pages:
                raise DocumentProcessingError("PDF has no pages to process via OCR.")
            return pages
        except ImportError:
            raise DocumentProcessingError("pdfplumber is required for OCR on PDF files.")

    raise DocumentProcessingError(
        f"Unsupported file type for OCR: '{extension}'. Supported: {sorted(OCR_SUPPORTED_IMAGE_EXTENSIONS | {'.pdf'})}"
    )


class ReportImageParserService:
    def __init__(self) -> None:
        self._preprocessing_service = ImagePreprocessingService()
        self._ocr_service = OCRService()
        self._parser_service = ReportParserService()
        self._range_service = MedicalRangeService()
        self._risk_service = ReportRiskService()
        self._llm_service = LLMService()

    def parse_image_report(self, file_path: str, filename: str) -> OCRReportResult:
        """OCR an image/scanned-PDF report and run the full Module 3 analysis pipeline."""
        logger.info("Starting OCR analysis for '%s'", filename)

        # 1. Load image pages.
        pages = _load_image_pages(file_path)

        # 2. Preprocess + OCR each page, concat results.
        all_text_parts: List[str] = []
        all_confidences: List[float] = []
        for i, page_image in enumerate(pages):
            preprocessed = self._preprocessing_service.preprocess(page_image)
            try:
                page_text, page_confidence = self._ocr_service.extract_text(preprocessed)
                all_text_parts.append(page_text)
                all_confidences.append(page_confidence)
                logger.info(
                    "Page %d/%d: OCR extracted %d chars, confidence=%.1f%%",
                    i + 1, len(pages), len(page_text), page_confidence,
                )
            except OCRError as exc:
                logger.warning("OCR failed on page %d: %s", i + 1, exc.message)

        if not all_text_parts:
            raise OCRError("OCR could not extract text from any page of this report.")

        combined_text = "\n\n".join(all_text_parts)
        mean_confidence = sum(all_confidences) / len(all_confidences)
        logger.info(
            "OCR complete for '%s': %d chars total, mean confidence=%.1f%%",
            filename, len(combined_text), mean_confidence,
        )

        # 3. Parse extracted text through the existing Module 3 pipeline
        # (parameter detection, range comparison, risk assessment, AI explanation).
        from app.services.report_analysis_service import ReportAnalysisService
        from app.schemas.report_response import ReportParameter

        parsed_values = self._parser_service.parse(combined_text)
        if not parsed_values:
            preview = combined_text.strip()[:400]
            raise OCRError(
                "We could OCR this image but could not detect any known lab parameters. "
                "The image may be too unclear, or the report may use labels the parser does "
                "not yet recognize (supported: CBC, Blood Sugar, HbA1c, Lipid, Thyroid, LFT, "
                f"KFT, electrolytes).\n\nOCR text preview:\n{preview or '(empty)'}"
            )

        parameters: List[ReportParameter] = []
        abnormal_parameters: List[str] = []
        for name, value in parsed_values.items():
            comparison = self._range_service.compare(name, value)
            parameters.append(
                ReportParameter(
                    name=name, value=value, unit=comparison.unit,
                    status=comparison.status,
                    reference_min=comparison.reference_min,
                    reference_max=comparison.reference_max,
                )
            )
            if comparison.status != "NORMAL":
                abnormal_parameters.append(name)

        report_type = self._range_service.infer_report_type(list(parsed_values.keys()))
        risk_assessment = self._risk_service.assess(parsed_values)

        analysis = ReportAnalysisResponse(
            report_type=report_type,
            parameters=parameters,
            abnormal_parameters=abnormal_parameters,
            risk_assessment=risk_assessment,
            ai_summary="",
            disclaimer=REPORT_ANALYSIS_DISCLAIMER,
        )
        context_block = _build_report_context_block(analysis)

        try:
            ai_summary = self._llm_service.generate_answer(
                question=(
                    "Explain EVERY parameter in the context in plain English (not just the "
                    "abnormal ones): note Normal/Low/High, what any abnormal values may "
                    "indicate, and general lifestyle guidance. "
                    "Do not diagnose or prescribe medication."
                ),
                context_chunks=[context_block],
            )
        except Exception as exc:
            logger.error("AI explanation failed for OCR report '%s': %s", filename, exc)
            ai_summary = (
                "An AI explanation could not be generated. "
                "The structured findings above are based on the OCR-extracted values."
            )

        analysis.ai_summary = ai_summary
        get_report_context_store().set_latest(context_block)

        return OCRReportResult(analysis=analysis, ocr_text=combined_text, ocr_confidence=round(mean_confidence, 2))
