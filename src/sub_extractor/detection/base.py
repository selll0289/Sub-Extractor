"""Abstract base class for subtitle detectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from ..enums import SubtitleType
from ..models import SubtitleTrack, VideoInfo

if TYPE_CHECKING:
    from ..models import ExtractionJob


class SubtitleDetector(ABC):
    """Discover subtitle tracks associated with a video.

    Each detector handles one *type* of subtitle (soft, external, hard).
    The pipeline runs all registered detectors and merges their results.
    """

    @abstractmethod
    def detect(self, video_info: VideoInfo, job: "ExtractionJob") -> List[SubtitleTrack]:
        """Find and return all subtitle tracks of this detector's type.

        Args:
            video_info: The probed video metadata from the Input stage.
            job: The active extraction job (provides settings like --ocr flags).

        Returns:
            List of SubtitleTrack descriptors (may be empty).
        """
        ...

    @property
    @abstractmethod
    def detection_type(self) -> SubtitleType:
        """The SubtitleType this detector produces."""
        ...
