"""FFmpeg-based video remuxer — removes subtitle tracks from video.

Uses stream copy (-c copy) to avoid re-encoding, which is fast and lossless.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ..exceptions import ProcessingError
from ..ffmpeg import FFmpegRunner
from ..models import ExtractionJob, VideoInfo
from .base import VideoProcessor

logger = logging.getLogger(__name__)

# Output suffix for the clean video
_CLEAN_SUFFIX = "_clean"


class FFmpegRemuxer(VideoProcessor):
    """Remux video to remove all subtitle streams using ffmpeg stream copy.

    Works with MP4, MKV, and any other format ffmpeg supports with ``-c copy``.

    Strategy:
      ``ffmpeg -i input -map 0 -map -0:s -c copy output``
      - ``-map 0``    : include all streams from input
      - ``-map -0:s`` : subtract all subtitle streams
      - ``-c copy``   : stream copy (no re-encode) — fast and lossless
    """

    def __init__(self) -> None:
        self._runner = FFmpegRunner()

    def can_process(self, video_info: VideoInfo) -> bool:
        return True  # ffmpeg handles everything we support

    def process(self, job: ExtractionJob) -> Path:
        if job.video_info is None:
            raise ProcessingError("No video info available — input stage not run?")

        # Build output path: "movie_clean.mkv"
        suffix = job.input_video.suffix
        stem = job.input_video.stem
        output_path = job.output_dir / f"{stem}{_CLEAN_SUFFIX}{suffix}"

        # Check if we need to copy video at all
        if job.video_info.subtitle_count == 0:
            logger.info("No subtitle tracks to remove — copying video directly")
            import shutil
            shutil.copy2(job.input_video, output_path)
            return output_path

        args = [
            "-i", str(job.input_video),
            "-map", "0",         # Include all streams from input 0
            "-map", "-0:s",      # Subtract ALL subtitle streams from input 0
            "-c", "copy",        # Stream copy (no re-encode)
            "-y",                # Overwrite output
            str(output_path),
        ]

        self._runner.run(args, description=f"remux video (remove subtitles)")

        # Verify output exists
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ProcessingError(
                f"Remuxed video is empty or missing: {output_path}"
            )

        logger.info("Clean video written: %s", output_path.name)
        return output_path
