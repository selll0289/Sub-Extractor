"""Abstract base class for video processors."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ExtractionJob, VideoInfo


class VideoProcessor(ABC):
    """Produce a clean video file without subtitle tracks."""

    @abstractmethod
    def can_process(self, video_info: VideoInfo) -> bool:
        """Return True if this processor can handle the given video format."""
        ...

    @abstractmethod
    def process(self, job: ExtractionJob) -> Path:
        """Remux/transcode the video, removing all subtitle streams.

        Args:
            job: The active extraction job.

        Returns:
            Path to the output clean video file.

        Raises:
            ProcessingError: If remuxing fails.
        """
        ...
