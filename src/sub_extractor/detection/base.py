"""Abstract base class for subtitle detectors."""

from abc import ABC, abstractmethod
from typing import List

from ..enums import SubtitleType
from ..models import SubtitleTrack, VideoInfo


class SubtitleDetector(ABC):
    """Discover subtitle tracks associated with a video.

    Each detector handles one *type* of subtitle (soft, external, hard).
    The pipeline runs all registered detectors and merges their results.
    """

    @abstractmethod
    def detect(self, video_info: VideoInfo) -> List[SubtitleTrack]:
        """Find and return all subtitle tracks of this detector's type.

        Args:
            video_info: The probed video metadata from the Input stage.

        Returns:
            List of SubtitleTrack descriptors (may be empty).
        """
        ...

    @property
    @abstractmethod
    def detection_type(self) -> SubtitleType:
        """The SubtitleType this detector produces."""
        ...
