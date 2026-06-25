"""Abstract base class for input handlers."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import VideoInfo


class InputHandler(ABC):
    """Validate a video file and extract its metadata (VideoInfo).

    Each concrete handler supports one or more file extensions. The pipeline
    iterates registered handlers and selects the first whose ``can_handle()``
    returns True.
    """

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """Return True if this handler supports the given file format."""
        ...

    @abstractmethod
    def process(self, file_path: Path) -> VideoInfo:
        """Probe the file and build a complete VideoInfo.

        Must raise on invalid or unplayable files.
        """
        ...

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """List of lowercase file extensions this handler supports."""
        ...
