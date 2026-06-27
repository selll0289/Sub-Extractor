"""OCR engine abstraction layer.

Provides a common interface for multiple OCR backends:
- EasyOCR (recommended default — good multi-language, easy install)
- PaddleOCR (excellent Chinese recognition, faster for batch)

Both engines implement the OCREngine abstract base class with lazy
initialization — models are loaded only on first use.

References:
    EasyOCR: https://github.com/JaidedAI/EasyOCR
    PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OCRResult:
    """A single OCR recognition result.

    Attributes:
        text: Recognized text string.
        confidence: Confidence score (0.0–1.0).
        bbox: Optional bounding box (x1, y1, x2, y2) in the source image.
    """

    text: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


class OCREngine(ABC):
    """Abstract OCR engine — all backends implement this interface."""

    @abstractmethod
    def recognize(self, image: "np.ndarray") -> List[OCRResult]:
        """Recognize text in a preprocessed image.

        Args:
            image: Binary or grayscale image as numpy array (H, W) or (H, W, 1).

        Returns:
            List of OCRResult objects, sorted by confidence descending.
        """
        ...

    @abstractmethod
    def available_languages(self) -> List[str]:
        """Return the list of language codes supported by this engine."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name: 'easyocr', 'paddleocr', etc."""
        ...


# ---------------------------------------------------------------------------
# EasyOCR backend
# ---------------------------------------------------------------------------


class EasyOCREngine(OCREngine):
    """OCR engine backed by EasyOCR.

    EasyOCR supports 80+ languages and works offline. Models are downloaded
    automatically on first use (~100-500 MB total, cached in ~/.EasyOCR/).
    """

    def __init__(self, languages: List[str], gpu: bool = True) -> None:
        self._languages = languages
        self._gpu = gpu
        self._reader = None  # Lazy init

    @property
    def name(self) -> str:
        return "easyocr"

    def available_languages(self) -> List[str]:
        # EasyOCR supports many languages; we return the configured ones
        return list(self._languages)

    def recognize(self, image: "np.ndarray") -> List[OCRResult]:
        reader = self._get_reader()
        # EasyOCR expects a numpy array; handles both BGR and grayscale
        raw_results = reader.readtext(image)
        return [
            OCRResult(
                text=text,
                confidence=confidence,
                bbox=(
                    int(bbox[0][0]), int(bbox[0][1]),
                    int(bbox[2][0]), int(bbox[2][1]),
                ),
            )
            for bbox, text, confidence in raw_results
        ]

    def _get_reader(self):
        """Lazy-initialize the EasyOCR reader (model download on first call)."""
        if self._reader is None:
            import easyocr
            logger.info(
                "Initializing EasyOCR with languages=%s (first use — "
                "may download models, ~100-500 MB)",
                self._languages,
            )
            self._reader = easyocr.Reader(
                self._languages,
                gpu=self._gpu,
                verbose=False,
            )
        return self._reader


# ---------------------------------------------------------------------------
# PaddleOCR backend
# ---------------------------------------------------------------------------


class PaddleOCREngine(OCREngine):
    """OCR engine backed by PaddleOCR.

    PaddleOCR provides state-of-the-art Chinese text recognition and
    excellent multi-language support. The PaddlePaddle framework is
    required as a dependency.
    """

    def __init__(self, languages: List[str], gpu: bool = True) -> None:
        self._languages = languages
        self._gpu = gpu
        self._ocr = None  # Lazy init

    @property
    def name(self) -> str:
        return "paddleocr"

    def available_languages(self) -> List[str]:
        return list(self._languages)

    def recognize(self, image: "np.ndarray") -> List[OCRResult]:
        ocr = self._get_ocr()
        raw_results = ocr.ocr(image, cls=False)
        if not raw_results or not raw_results[0]:
            return []

        results: List[OCRResult] = []
        for line in raw_results[0]:
            bbox_points, (text, confidence) = line
            results.append(OCRResult(
                text=text,
                confidence=confidence,
                bbox=(
                    int(bbox_points[0][0]), int(bbox_points[0][1]),
                    int(bbox_points[2][0]), int(bbox_points[2][1]),
                ),
            ))
        return results

    def _get_ocr(self):
        """Lazy-initialize PaddleOCR (model download on first call)."""
        if self._ocr is None:
            from paddleocr import PaddleOCR
            logger.info(
                "Initializing PaddleOCR with lang=%s (first use — "
                "may download models)",
                self._languages[0] if self._languages else "ch",
            )
            self._ocr = PaddleOCR(
                lang=self._languages[0] if self._languages else "ch",
                use_gpu=self._gpu,
                show_log=False,
            )
        return self._ocr


# ---------------------------------------------------------------------------
# Engine factory
# ---------------------------------------------------------------------------


def create_engine(name: str, languages: List[str]) -> OCREngine:
    """Create an OCR engine instance by name.

    Args:
        name: Engine name ('easyocr' or 'paddleocr').
        languages: List of language codes (e.g., ['ch_sim', 'en']).

    Returns:
        An OCREngine instance.

    Raises:
        ImportError: If the requested engine's dependencies are not installed.
        ValueError: If the engine name is unrecognized.
    """
    if name == "easyocr":
        try:
            import easyocr  # noqa: F401
        except ImportError:
            raise ImportError(
                "EasyOCR is not installed. "
                "Install with: pip install sub-extractor[ocr-easyocr]"
            )
        return EasyOCREngine(languages)

    elif name == "paddleocr":
        try:
            import paddleocr  # noqa: F401
        except ImportError:
            raise ImportError(
                "PaddleOCR is not installed. "
                "Install with: pip install sub-extractor[ocr-paddleocr]"
            )
        return PaddleOCREngine(languages)

    else:
        raise ValueError(
            f"Unknown OCR engine: '{name}'. "
            f"Available engines: easyocr, paddleocr"
        )
