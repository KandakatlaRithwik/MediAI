"""
Image preprocessing engine (Module 6) — production-grade pipeline.

Pipeline:
  load -> grayscale -> upscale (target DPI) -> denoise -> CLAHE contrast
  -> deskew (auto-rotation correction) -> sharpen -> adaptive threshold
"""

import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger("ocr")


class ImagePreprocessingService:
    def preprocess(
        self,
        image_array: np.ndarray,
        *,
        target_dpi_width: int = 2480,  # ~A4 at 300 DPI
        denoise: bool = True,
        enhance_contrast: bool = True,
        deskew: bool = True,
        sharpen: bool = True,
        apply_threshold: bool = True,
    ) -> np.ndarray:
        image = image_array.copy()

        # 1. Grayscale
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 2. Upscale
        h, w = image.shape[:2]
        if w < target_dpi_width:
            scale = target_dpi_width / w
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            logger.debug("Upscaled image %.2fx", scale)

        # 3. Denoise
        if denoise:
            image = cv2.fastNlMeansDenoising(image, h=10, searchWindowSize=21, templateWindowSize=7)

        # 4. CLAHE contrast
        if enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            image = clahe.apply(image)

        # 5. Deskew (correct slight scan rotation)
        if deskew:
            image = self._deskew(image)

        # 6. Sharpen — small unsharp mask
        if sharpen:
            blur = cv2.GaussianBlur(image, (0, 0), sigmaX=1.0)
            image = cv2.addWeighted(image, 1.5, blur, -0.5, 0)

        # 7. Adaptive threshold
        if apply_threshold:
            image = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, blockSize=31, C=15,
            )

        return image

    @staticmethod
    def _deskew(image: np.ndarray) -> np.ndarray:
        try:
            inverted = cv2.bitwise_not(image)
            _, binary = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            coords = np.column_stack(np.where(binary > 0))
            if coords.size == 0:
                return image
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            # Only correct meaningful skew; ignore tiny noise rotations.
            if abs(angle) < 0.5 or abs(angle) > 15:
                return image
            (h, w) = image.shape[:2]
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            return cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE,
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Deskew skipped: %s", exc)
            return image

    def load_image(self, file_path: str) -> Optional[np.ndarray]:
        image = cv2.imread(file_path)
        if image is None:
            logger.error("cv2.imread returned None for '%s'", file_path)
        return image

    def preprocess_file(self, file_path: str) -> Optional[np.ndarray]:
        image = self.load_image(file_path)
        if image is None:
            return None
        return self.preprocess(image)
