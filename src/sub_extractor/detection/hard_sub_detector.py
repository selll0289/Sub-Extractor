"""Hardcoded (burned-in) subtitle detector.

Detects the potential presence of hardcoded subtitles in video files and
creates a synthetic subtitle track that triggers the OCR extraction pipeline.

Unlike soft subtitles (embedded as separate streams) and external subtitles
(sidecar files), hardcoded subtitles are part of the video image itself.
Detection is deferred to the OCR extraction stage; this detector simply
signals that OCR should be attempted when explicitly enabled.

Reference:
    VideoSubFinder: https://sourceforge.net/projects/videosubfinder/
"""

from __future__ import annotations

import logging
from typing import List

from ..enums import SubtitleType
from ..models import ExtractionJob, SubtitleTrack, VideoInfo
from ..ocr import OCR_AVAILABLE
from .base import SubtitleDetector

logger = logging.getLogger(__name__)


class HardSubDetector(SubtitleDetector):
    """Detects hardcoded (burned-in) subtitle potential in video files.

    This detector creates a synthetic HARD SubtitleTrack when:
    1. OCR dependencies are available on the system.
    2. The user has explicitly enabled OCR extraction.

    The actual analysis (frame extraction, preprocessing, OCR) happens in
    the extraction stage (OCRHardSubExtractor). This detector is just the
    trigger that tells the pipeline "try OCR on this video."

    In future versions, this could perform lightweight frame sampling to
    auto-detect the presence of burned-in text before committing to a full
    OCR pass.
    """

    @property
    def detection_type(self) -> SubtitleType:
        return SubtitleType.HARD

    def detect(
        self, video_info: VideoInfo, job: ExtractionJob
    ) -> List[SubtitleTrack]:
        """Create a synthetic hard-sub track if OCR is enabled and available.

        Args:
            video_info: The probed video metadata.
            job: The extraction job with user settings.

        Returns:
            A list with one SubtitleTrack(type=HARD) if OCR is enabled,
            or an empty list otherwise.
        """
        if not job.enable_hard_sub_ocr:
            logger.debug("Hard-sub OCR is disabled — skipping detection.")
            return []

        if not OCR_AVAILABLE:
            logger.warning(
                "Hard-sub OCR is enabled but OCR dependencies are not installed. "
                "Install with: pip install sub-extractor[ocr-easyocr]"
            )
            return []

        logger.info(
            "Hard-sub OCR enabled for %s (engine=%s, language=%s)",
            video_info.path.name,
            job.ocr_engine,
            job.ocr_language,
        )

        # Create a synthetic track — index -1 means "not a real stream"
        return [
            SubtitleTrack(
                index=-1,
                codec="ocr_hard_sub",
                language=job.ocr_language or "unknown",
                title=f"OCR: {job.ocr_engine} ({job.ocr_language})",
                type=SubtitleType.HARD,
            )
        ]
