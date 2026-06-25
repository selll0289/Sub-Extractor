"""Video input handler using ffprobe for MP4 and MKV files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

from ..enums import SubtitleType, VideoFormat
from ..exceptions import InvalidVideoError, UnsupportedFormatError
from ..ffmpeg import ffprobe_json
from ..models import AudioTrack, SubtitleTrack, VideoInfo
from .base import InputHandler

logger = logging.getLogger(__name__)

# Map file extensions to format enum
_EXT_TO_FORMAT: dict[str, VideoFormat] = {
    ".mp4": VideoFormat.MP4,
    ".mkv": VideoFormat.MKV,
}

# Recognised subtitle codec names from ffprobe
_SUBTITLE_CODECS: set[str] = {
    "subrip", "srt",
    "ass", "ssa",
    "webvtt", "vtt",
    "mov_text", "tx3g",
    "dvd_subtitle", "dvb_subtitle",
    "hdmv_pgs_subtitle", "pgs",
    "xsub",
    "microdvd",
    "subviewer", "subviewer1",
    "jacosub",
    "realtext",
    "sami",
    "stl",
}

# Recognised disposition flags for subtitle tracks
_DISPOSITION_KEYS: dict[str, str] = {
    "default": "is_default",
    "forced": "is_forced",
    "hearing_impaired": "is_hearing_impaired",
}


class VideoInputHandler(InputHandler):
    """Handles MP4 and MKV files using ffprobe for metadata extraction.

    Supports registering additional file extensions through the
    ``_supported`` set and ``_EXT_TO_FORMAT`` mapping.
    """

    _supported: set[str] = {".mp4", ".mkv"}

    # --- InputHandler interface ---------------------------------------------

    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in self._supported and file_path.is_file()

    @property
    def supported_formats(self) -> list[str]:
        return sorted(self._supported)

    def process(self, file_path: Path) -> VideoInfo:
        """Probe the video with ffprobe and build a complete VideoInfo.

        Raises:
            InvalidVideoError: If no video stream is found or duration is zero.
            UnsupportedFormatError: If the file extension is not recognised.
        """
        suffix = file_path.suffix.lower()
        if suffix not in _EXT_TO_FORMAT:
            raise UnsupportedFormatError(
                f"Unsupported format '{suffix}'. "
                f"Supported: {', '.join(sorted(_EXT_TO_FORMAT.keys()))}"
            )
        if not file_path.is_file():
            raise InvalidVideoError(f"File not found: {file_path}")

        probe = ffprobe_json(file_path)
        return self._parse_probe(probe, file_path, _EXT_TO_FORMAT[suffix])

    # --- Probe parsing ------------------------------------------------------

    def _parse_probe(
        self, probe: Dict[str, Any], file_path: Path, fmt: VideoFormat
    ) -> VideoInfo:
        """Convert raw ffprobe JSON into a VideoInfo dataclass."""
        streams: List[Dict[str, Any]] = probe.get("streams", [])
        format_info: Dict[str, Any] = probe.get("format", {})

        if not streams:
            raise InvalidVideoError(f"No streams found in: {file_path}")

        # --- Video stream (required) ---
        video_streams = [s for s in streams if s.get("codec_type") == "video"]
        if not video_streams:
            raise InvalidVideoError(f"No video stream found in: {file_path}")
        v = video_streams[0]

        width = int(v.get("width", 0))
        height = int(v.get("height", 0))
        if width <= 0 or height <= 0:
            raise InvalidVideoError(
                f"Invalid video dimensions ({width}x{height}) in: {file_path}"
            )

        duration = float(format_info.get("duration", 0))
        if duration <= 0:
            # Try stream-level duration
            duration = float(v.get("duration", 0))
        if duration <= 0:
            raise InvalidVideoError(
                f"Cannot determine duration for: {file_path}. "
                f"File may be corrupted or a live stream."
            )

        video_codec = v.get("codec_name", "unknown")

        bit_rate_str = format_info.get("bit_rate")
        bit_rate = int(bit_rate_str) if bit_rate_str else None

        # --- Audio streams ---
        audio_tracks: List[AudioTrack] = []
        for s in streams:
            if s.get("codec_type") != "audio":
                continue
            tags = s.get("tags", {})
            audio_tracks.append(AudioTrack(
                index=s["index"],
                codec=s.get("codec_name", "unknown"),
                language=tags.get("language"),
                channels=int(s.get("channels", 2)),
                title=tags.get("title"),
            ))

        # --- Subtitle streams ---
        subtitle_tracks: List[SubtitleTrack] = []
        for s in streams:
            if s.get("codec_type") != "subtitle":
                continue
            codec = s.get("codec_name", "unknown")

            # Only include recognised text/subtitle codecs
            if codec.lower() not in _SUBTITLE_CODECS:
                logger.debug("Skipping unrecognised subtitle codec: %s", codec)
                continue

            tags = s.get("tags", {})
            disposition = s.get("disposition", {})

            subtitle_tracks.append(SubtitleTrack(
                index=s["index"],
                codec=codec,
                language=tags.get("language"),
                title=tags.get("title"),
                is_default=_get_disposition(disposition, "default"),
                is_forced=_get_disposition(disposition, "forced"),
                is_hearing_impaired=_get_disposition(disposition, "hearing_impaired"),
                type=SubtitleType.SOFT,
            ))

        logger.info(
            "Probed %s: %dx%d, %.1fs, %d audio, %d subtitle track(s)",
            file_path.name, width, height, duration,
            len(audio_tracks), len(subtitle_tracks),
        )

        return VideoInfo(
            path=file_path,
            format=fmt,
            duration_seconds=duration,
            video_codec=video_codec,
            width=width,
            height=height,
            bit_rate=bit_rate,
            audio_tracks=audio_tracks,
            subtitle_tracks=subtitle_tracks,
        )


def _get_disposition(disposition: Dict[str, Any], key: str) -> bool:
    """Safely extract a boolean disposition flag from ffprobe output."""
    return bool(disposition.get(key, 0))
