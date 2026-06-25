"""Pipeline orchestrator — the central coordinator for subtitle extraction.

The Pipeline class owns the handler registries for each layer and executes
them in order: Input → Detection → Extraction → Processing → Output.

Each layer is independently extensible — adding a new handler to a registry
adds support for a new format or subtitle type without modifying the pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, List, Optional

from .detection.base import SubtitleDetector
from .detection.external_sub_detector import ExternalSubDetector
from .detection.soft_sub_detector import SoftSubDetector
from .enums import PipelineStage, SubtitleType
from .exceptions import (
    ExtractionError,
    NoSubtitlesFoundError,
    ProcessingError,
    SubExtractorError,
)
from .extraction.base import SubtitleExtractor
from .extraction.ffmpeg_extractor import FFmpegExtractor
from .input.base import InputHandler
from .input.video_input import VideoInputHandler
from .models import ExtractionJob, SubtitleTrack
from .output.base import OutputHandler
from .output.file_output import FileOutput
from .processing.base import VideoProcessor
from .processing.ffmpeg_remuxer import FFmpegRemuxer

logger = logging.getLogger(__name__)

# Progress callback signature: stage, current step name, fraction 0.0–1.0
ProgressCallback = Callable[[PipelineStage, str, float], None]


class Pipeline:
    """Coordinates input, detection, extraction, processing, and output stages.

    Each stage uses a registry of handlers (strategy pattern). The pipeline
    iterates registered handlers and picks the first one that can handle the
    current context. This means new format support is added by registering a
    new handler — zero changes to the pipeline itself.

    Usage::

        pipeline = Pipeline()
        job = ExtractionJob(
            input_video=Path("movie.mkv"),
            output_dir=Path("./subtitles"),
        )
        job = pipeline.run(job)
    """

    # ------------------------------------------------------------------
    # Constructor — assemble the default handler registries
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        # Input handlers — probe video files and build VideoInfo
        self._input_handlers: list[InputHandler] = [
            VideoInputHandler(),
        ]

        # Subtitle detectors — find subtitles of each type
        self._detectors: list[SubtitleDetector] = [
            SoftSubDetector(),
            ExternalSubDetector(),
            # Future: HardSubDetector() — OCR-based
        ]

        # Subtitle extractors — extract tracks to standalone files
        self._extractors: list[SubtitleExtractor] = [
            FFmpegExtractor(),
            # Future: OCRHardSubExtractor()
        ]

        # Video processors — produce clean video without subtitle tracks
        self._processors: list[VideoProcessor] = [
            FFmpegRemuxer(),
        ]

        # Output handlers — write results to target destination
        self._output_handler: OutputHandler = FileOutput()

        # Progress callback (set by CLI or GUI)
        self._on_progress: Optional[ProgressCallback] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def on_progress(self) -> Optional[ProgressCallback]:
        return self._on_progress

    @on_progress.setter
    def on_progress(self, cb: Optional[ProgressCallback]) -> None:
        self._on_progress = cb

    def register_input_handler(self, handler: InputHandler) -> None:
        """Register an additional input handler for a new format."""
        self._input_handlers.append(handler)

    def register_detector(self, detector: SubtitleDetector) -> None:
        """Register an additional subtitle detector."""
        self._detectors.append(detector)

    def register_extractor(self, extractor: SubtitleExtractor) -> None:
        """Register an additional subtitle extractor."""
        self._extractors.append(extractor)

    def register_processor(self, processor: VideoProcessor) -> None:
        """Register an additional video processor."""
        self._processors.append(processor)

    def run(self, job: ExtractionJob) -> ExtractionJob:
        """Execute the full pipeline on a job.

        Each stage catches exceptions and records them in ``job.errors``.
        The pipeline continues when possible (e.g., one subtitle track failing
        won't prevent other tracks from being extracted).

        Returns:
            The same ExtractionJob with results populated.
        """
        self._report(PipelineStage.INPUT, "Starting", 0)

        # ---- Stage 1: Input ----
        self._report(PipelineStage.INPUT, "Validating input file", 0.1)
        try:
            handler = self._find_input_handler(job.input_video)
            job.video_info = handler.process(job.input_video)
        except SubExtractorError as exc:
            job.errors.append(f"[Input] {exc}")
            return job
        self._report(PipelineStage.INPUT, f"Probed: {job.video_info.path.name}", 0.25)

        # ---- Stage 2: Detection ----
        self._report(PipelineStage.DETECTION, "Detecting subtitles", 0.3)
        all_tracks: list[SubtitleTrack] = []
        for detector in self._detectors:
            try:
                tracks = detector.detect(job.video_info)
                all_tracks.extend(tracks)
            except SubExtractorError as exc:
                job.warnings.append(f"[Detection:{detector.detection_type.name}] {exc}")

        if not all_tracks:
            job.warnings.append("No subtitles found.")
            # This is not necessarily an error — user may want clean video only
        else:
            logger.info("Detected %d subtitle track(s) total", len(all_tracks))

        # Apply filters
        tracks_to_extract = self._filter_tracks(all_tracks, job)
        self._report(
            PipelineStage.DETECTION,
            f"Found {len(tracks_to_extract)} track(s) to extract",
            0.35,
        )

        # ---- Stage 3: Extraction ----
        self._report(PipelineStage.EXTRACTION, "Extracting subtitles", 0.4)
        total_tracks = len(tracks_to_extract)
        for i, track in enumerate(tracks_to_extract):
            fraction = 0.4 + (0.2 * (i / max(total_tracks, 1)))
            self._report(
                PipelineStage.EXTRACTION,
                f"Track {i+1}/{total_tracks}: {track.codec}",
                fraction,
            )
            self._extract_one_track(track, job)

        # ---- Stage 4: Processing (clean video) ----
        if job.keep_video and job.video_info:
            self._report(PipelineStage.PROCESSING, "Removing subtitle tracks from video", 0.65)
            try:
                processor = self._find_processor(job.video_info)
                job.output_video = processor.process(job)
            except (ProcessingError, SubExtractorError) as exc:
                job.errors.append(f"[Processing] {exc}")
            self._report(PipelineStage.PROCESSING, "Video processed", 0.85)

        # ---- Stage 5: Output ----
        self._report(PipelineStage.OUTPUT, "Finalizing output", 0.9)
        try:
            resolved_dir = self._output_handler.prepare(job.output_dir)
            job.output_dir = resolved_dir
            job = self._output_handler.finalize(job)
        except SubExtractorError as exc:
            job.errors.append(f"[Output] {exc}")
        self._report(PipelineStage.OUTPUT, "Complete", 1.0)

        return job

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_input_handler(self, file_path: Path) -> InputHandler:
        """Find the first input handler that can handle this file."""
        for handler in self._input_handlers:
            if handler.can_handle(file_path):
                return handler
        raise NoSubtitlesFoundError(
            f"No input handler found for: {file_path}\n"
            f"Supported formats: {self._list_supported_formats()}"
        )

    def _find_processor(self, video_info) -> VideoProcessor:
        """Find the first processor that can handle this video format."""
        for processor in self._processors:
            if processor.can_process(video_info):
                return processor
        raise ProcessingError(
            f"No video processor found for format: {video_info.format.value}"
        )

    def _find_extractor(self, track: SubtitleTrack, job: ExtractionJob) -> SubtitleExtractor | None:
        """Find the first extractor that can handle this track."""
        for extractor in self._extractors:
            if extractor.can_extract(track, job):
                return extractor
        return None

    def _filter_tracks(
        self, tracks: list[SubtitleTrack], job: ExtractionJob
    ) -> list[SubtitleTrack]:
        """Apply user-specified filters to the detected tracks."""
        filtered = list(tracks)

        # Filter by type
        if not job.include_external:
            filtered = [t for t in filtered if t.type != SubtitleType.EXTERNAL]

        # Filter by language
        if job.target_languages:
            filtered = [
                t for t in filtered
                if t.language and t.language.lower() in _normalize(job.target_languages)
            ]

        # Filter by specific track indices
        if job.target_track_indices is not None:
            filtered = [
                t for t in filtered
                if t.index in job.target_track_indices
            ]

        return filtered

    def _extract_one_track(self, track: SubtitleTrack, job: ExtractionJob) -> None:
        """Extract a single subtitle track, recording any error."""
        try:
            extractor = self._find_extractor(track, job)
            if extractor is None:
                job.warnings.append(
                    f"No extractor available for track {track.index} "
                    f"(codec: {track.codec}, type: {track.type.name})"
                )
                return
            output_path = extractor.extract(track, job)
            job.extracted_subtitles.append(output_path)
        except ExtractionError as exc:
            job.errors.append(
                f"[Extraction] Track {track.index}: {exc}"
            )
        except SubExtractorError as exc:
            job.errors.append(
                f"[Extraction] Track {track.index}: {exc}"
            )

    def _list_supported_formats(self) -> str:
        """Return a comma-separated list of supported file extensions."""
        exts: set[str] = set()
        for h in self._input_handlers:
            exts.update(h.supported_formats)
        return ", ".join(sorted(exts))

    def _report(self, stage: PipelineStage, message: str, fraction: float) -> None:
        """Fire the progress callback if one is set."""
        logger.debug("[%s] %s (%.0f%%)", stage.value, message, fraction * 100)
        if self._on_progress:
            try:
                self._on_progress(stage, message, fraction)
            except Exception:
                # Progress callback should never crash the pipeline
                pass


def _normalize(items: list[str]) -> set[str]:
    """Normalize a list of strings to lowercase for case-insensitive comparison."""
    return {i.lower() for i in items}
