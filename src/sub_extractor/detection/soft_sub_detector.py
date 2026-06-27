"""Soft subtitle detector — finds embedded subtitle tracks from VideoInfo."""

import logging
from typing import List

from ..enums import SubtitleType
from ..models import ExtractionJob, SubtitleTrack, VideoInfo
from .base import SubtitleDetector

logger = logging.getLogger(__name__)


class SoftSubDetector(SubtitleDetector):
    """Detects soft (embedded) subtitle tracks already present in VideoInfo.

    These tracks were discovered by ffprobe during the Input stage.
    This detector filters and validates them.
    """

    @property
    def detection_type(self) -> SubtitleType:
        return SubtitleType.SOFT

    def detect(self, video_info: VideoInfo, job: ExtractionJob) -> List[SubtitleTrack]:
        tracks = [t for t in video_info.subtitle_tracks if t.type == SubtitleType.SOFT]
        logger.info(
            "Soft subtitle detector: %d track(s) found in %s",
            len(tracks), video_info.path.name,
        )
        return tracks
