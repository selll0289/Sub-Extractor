"""Abstract base class for subtitle extractors."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import ExtractionJob, SubtitleTrack


class SubtitleExtractor(ABC):
    """Extract a subtitle track to a standalone file.

    Each concrete implementation handles one or more subtitle codecs/types.
    """

    @abstractmethod
    def can_extract(self, track: SubtitleTrack, job: ExtractionJob) -> bool:
        """Return True if this extractor can handle the given track."""
        ...

    @abstractmethod
    def extract(self, track: SubtitleTrack, job: ExtractionJob) -> Path:
        """Extract a single subtitle track to a file.

        Args:
            track: The subtitle track descriptor to extract.
            job: The active extraction job (provides input video, output dir, options).

        Returns:
            Path to the created subtitle file.

        Raises:
            ExtractionError: If extraction fails.
        """
        ...

    @abstractmethod
    def get_output_extension(self, track: SubtitleTrack) -> str:
        """Return the file extension (without dot) for this track's output.

        Example: ``"srt"``, ``"ass"``.
        """
        ...
