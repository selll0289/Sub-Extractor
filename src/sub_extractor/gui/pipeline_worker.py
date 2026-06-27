"""PipelineWorker — runs the extraction pipeline on a background QThread.

Qt signals bridge the synchronous Pipeline progress callbacks to the main
thread's event loop, keeping the UI responsive during long ffmpeg operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from sub_extractor.enums import PipelineStage
from sub_extractor.exceptions import SubExtractorError
from sub_extractor.models import ExtractionJob, VideoInfo
from sub_extractor.pipeline import Pipeline


class PipelineWorker(QObject):
    """Runs Pipeline.run() on a worker thread, emitting progress via signals.

    Usage::

        thread = QThread()
        worker = PipelineWorker()
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.extraction_finished.connect(on_done)
        worker.extraction_finished.connect(thread.quit)
        worker.progress_updated.connect(on_progress)
        worker.extraction_error.connect(on_error)

        worker.set_job(job)
        thread.start()
    """

    # --- Signals (emitted from worker thread, delivered to main thread) ---

    progress_updated = Signal(PipelineStage, str, float)
    """Emitted during pipeline execution: stage, message, fraction (0.0-1.0)."""

    extraction_finished = Signal(object)
    """Emitted when pipeline.run() completes successfully. Carries the ExtractionJob."""

    extraction_error = Signal(str)
    """Emitted when pipeline.run() raises an exception. Carries the error message."""

    info_loaded = Signal(object)
    """Emitted when video info probing completes. Carries a VideoInfo."""

    external_subs_loaded = Signal(object)
    """Emitted when external subtitle detection completes. Carries list[SubtitleTrack]."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._job: Optional[ExtractionJob] = None
        self._mode: str = "extract"  # "extract" | "info"

    def set_job(self, job: ExtractionJob) -> None:
        """Set the extraction job to run. Call before starting the thread."""
        self._job = job

    def set_mode(self, mode: str) -> None:
        """Set the worker mode: 'extract' or 'info'."""
        self._mode = mode

    @Slot()
    def run(self) -> None:
        """Entry point called when QThread starts. Runs on the worker thread."""
        pipeline = Pipeline()
        pipeline.on_progress = self._on_pipeline_progress

        try:
            if self._mode == "extract":
                if self._job is None:
                    self.extraction_error.emit("No job configured.")
                    return
                job = pipeline.run(self._job)
                self.extraction_finished.emit(job)

            elif self._mode == "info":
                if self._job is None or self._job.input_video is None:
                    self.extraction_error.emit("No input file configured.")
                    return
                handler = pipeline._find_input_handler(self._job.input_video)
                video_info = handler.process(self._job.input_video)

                # Also detect external subtitles
                from sub_extractor.detection.external_sub_detector import ExternalSubDetector
                detector = ExternalSubDetector()
                external = detector.detect(video_info, self._job)

                self.info_loaded.emit(video_info)
                if external:
                    self.external_subs_loaded.emit(external)

        except SubExtractorError as exc:
            self.extraction_error.emit(str(exc))
        except Exception as exc:
            self.extraction_error.emit(f"Unexpected error: {exc}")

    def _on_pipeline_progress(
        self, stage: PipelineStage, message: str, fraction: float
    ) -> None:
        """Called synchronously by Pipeline._report() on the worker thread.

        Qt handles cross-thread signal delivery to the main thread automatically
        via queued connections (the default when sender and receiver are on
        different threads).
        """
        self.progress_updated.emit(stage, message, fraction)
