"""OCR-based hardcoded subtitle extractor.

Extracts burned-in (hardcoded) subtitles from video by:
1. Extracting frames at regular intervals via ffmpeg
2. Preprocessing each frame for OCR
3. Running OCR text recognition
4. Deduplicating recognized text across consecutive frames
5. Assigning timestamps and formatting output as SRT or ASS

Reference implementations:
    VideoSubFinder (C++, Tesseract): https://sourceforge.net/projects/videosubfinder/
    video-subtitle-extractor (Python, PaddleOCR): https://github.com/YaoFANGUK/video-subtitle-extractor
    esrXP (classic tool for hardcoded subs)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ..enums import SubtitleType
from ..exceptions import (
    ExtractionError,
    OCREngineNotAvailableError,
    OCRError,
)
from ..models import ExtractionJob, SubtitleTrack
from ..ocr import OCR_AVAILABLE, get_available_engines
from ..ocr.deduplicator import SubtitleEntry
from ..ocr.formatter import to_ass, to_srt
from .base import SubtitleExtractor

logger = logging.getLogger(__name__)

# Mapping of output format to encoder extension
_FORMAT_TO_EXT: dict[str, str] = {
    "srt": "srt",
    "ass": "ass",
    "ssa": "ass",  # SSA uses ASS format internally
    "vtt": "srt",  # We output SRT for VTT (user can convert after)
}


class OCRHardSubExtractor(SubtitleExtractor):
    """Extract hardcoded subtitles via OCR frame analysis.

    This extractor orchestrates the full OCR pipeline:
      FrameExtractor → Preprocessor → OCREngine → Deduplicator → Formatter

    When successful, produces a .srt or .ass subtitle file. Processing time
    depends on video duration and frame interval (e.g., 2h video at 1.0s
    interval = 7200 frames; ~5-15 min with EasyOCR on CPU).
    """

    def __init__(self) -> None:
        self._job: Optional[ExtractionJob] = None

    # --- SubtitleExtractor interface ----------------------------------------

    def can_extract(self, track: SubtitleTrack, job: ExtractionJob) -> bool:
        """Return True if this is a hard subtitle track and OCR is available."""
        return (
            track.type == SubtitleType.HARD
            and job.enable_hard_sub_ocr
            and OCR_AVAILABLE
        )

    def get_output_extension(self, track: SubtitleTrack) -> str:
        """Return the output file extension based on job format preference."""
        if self._job:
            fmt = self._job.preferred_sub_format.lower()
            return _FORMAT_TO_EXT.get(fmt, "srt")
        return "srt"

    def extract(self, track: SubtitleTrack, job: ExtractionJob) -> Path:
        """Run the complete OCR extraction pipeline.

        Returns:
            Path to the generated subtitle file.

        Raises:
            OCREngineNotAvailableError: If OCR dependencies are missing.
            ExtractionError: If OCR fails or produces no text.
        """
        self._job = job

        if not OCR_AVAILABLE:
            raise OCREngineNotAvailableError(job.ocr_engine)

        # Build output path
        ext = self.get_output_extension(track)
        stem = job.input_video.stem
        lang_suffix = job.ocr_language or "ocr"
        output_path = job.output_dir / f"{stem}.{lang_suffix}.ocr.{ext}"

        logger.info(
            "Starting OCR extraction for %s (engine=%s, lang=%s, interval=%.1fs)",
            job.input_video.name,
            job.ocr_engine,
            job.ocr_language,
            job.ocr_frame_interval,
        )

        # Run the OCR pipeline
        try:
            entries = self._run_pipeline(job)
        except ImportError as exc:
            raise OCREngineNotAvailableError(job.ocr_engine) from exc
        except Exception as exc:
            raise ExtractionError(
                f"OCR extraction failed: {exc}",
                track_index=track.index,
            ) from exc

        if not entries:
            raise ExtractionError(
                "OCR completed but no text was recognized. "
                "Try a different OCR engine or lower the confidence threshold.",
                track_index=track.index,
            )

        # Format and write output
        content = self._format_output(entries, ext, job)
        output_path.write_text(content, encoding="utf-8")

        logger.info(
            "OCR extraction complete: %d subtitle entries written to %s",
            len(entries),
            output_path.name,
        )

        return output_path

    # --- Internal ------------------------------------------------------------

    def _run_pipeline(self, job: ExtractionJob) -> list[SubtitleEntry]:
        """Execute the OCR pipeline with progress reporting."""
        from sub_extractor.ocr import run_ocr_pipeline

        vi = job.video_info

        class _Progress:
            """Adapter from pipeline progress callback to OCR progress."""

            def __init__(self, job):
                self._job = job

            def __call__(self, stage, message, fraction):
                # Map OCR stages to the PipelineStage enum
                logger.debug("[OCR:%s] %s (%.0f%%)", stage, message, fraction * 100)

        entries = run_ocr_pipeline(
            video_path=job.input_video,
            engine=job.ocr_engine,
            language=job.ocr_language,
            frame_interval=job.ocr_frame_interval,
            confidence_threshold=job.ocr_confidence_threshold,
            subtitle_region=job.ocr_subtitle_region,
            output_format=job.preferred_sub_format,
            progress_callback=_Progress(job) if logger.isEnabledFor(logging.DEBUG) else None,
            video_width=vi.width if vi else 0,
            video_height=vi.height if vi else 0,
        )

        return entries

    def _format_output(
        self, entries: list[SubtitleEntry], ext: str, job: ExtractionJob
    ) -> str:
        """Format entries as SRT or ASS content."""
        if ext in ("ass", "ssa"):
            vi = job.video_info
            return to_ass(
                entries,
                video_width=vi.width if vi else 1920,
                video_height=vi.height if vi else 1080,
            )
        else:
            return to_srt(entries)
