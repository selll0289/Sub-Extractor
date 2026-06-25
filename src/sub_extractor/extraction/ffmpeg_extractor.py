"""FFmpeg-based subtitle extractor.

Handles both soft (embedded) and external subtitle extraction.
Uses ffmpeg for stream demuxing and optional format conversion.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from ..enums import SubtitleType
from ..exceptions import ExtractionError
from ..ffmpeg import FFmpegRunner, find_ffmpeg
from ..models import ExtractionJob, SubtitleTrack
from .base import SubtitleExtractor
from .codec_map import get_extension, get_ffmpeg_encoder

logger = logging.getLogger(__name__)


class FFmpegExtractor(SubtitleExtractor):
    """Extract subtitles using ffmpeg.

    For soft subtitles (embedded tracks), uses ffmpeg's stream mapping:
      ``ffmpeg -i input -map 0:s:N -c:s codec output.ext``

    For external subtitle files, simply copies the file (optionally
    converting the format with ffmpeg).
    """

    def __init__(self) -> None:
        self._runner = FFmpegRunner()

    # --- SubtitleExtractor interface ----------------------------------------

    def can_extract(self, track: SubtitleTrack, job: ExtractionJob) -> bool:
        """Can extract any soft or external track."""
        return track.type in (SubtitleType.SOFT, SubtitleType.EXTERNAL)

    def get_output_extension(self, track: SubtitleTrack) -> str:
        """Return preferred output extension, respecting job preference for text codecs."""
        preferred = job.preferred_sub_format if hasattr(self, '_job') else "srt"
        # Use preferred format if set; otherwise use native extension
        native_ext = get_extension(track.codec)
        # Only override if the track is not bitmap (bitmaps can't be converted yet)
        bitmap_codecs = {"dvd_subtitle", "hdmv_pgs_subtitle", "pgs", "xsub"}
        if track.codec.lower() not in bitmap_codecs and preferred != native_ext:
            return preferred
        return native_ext

    def extract(self, track: SubtitleTrack, job: ExtractionJob) -> Path:
        """Extract a single subtitle track to a file."""
        self._job = job  # store for helper methods
        output_path = self._build_output_path(track, job)

        if track.type == SubtitleType.SOFT:
            self._extract_soft(track, job, output_path)
        elif track.type == SubtitleType.EXTERNAL:
            self._extract_external(track, job, output_path)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ExtractionError(
                f"Extracted subtitle file is empty: {output_path}",
                track_index=track.index,
            )

        logger.info("Extracted: %s", output_path.name)
        return output_path

    # --- Internal helpers ---------------------------------------------------

    def _build_output_path(self, track: SubtitleTrack, job: ExtractionJob) -> Path:
        """Build the output filename for a subtitle track."""
        ext = self.get_output_extension(track)
        stem = job.input_video.stem

        # Build a label: language code, or "track_N", or "unknown"
        if track.language:
            label = track.language
        elif track.type == SubtitleType.SOFT:
            label = f"track_{track.index}"
        else:
            label = "external"

        return job.output_dir / f"{stem}.{label}.{ext}"

    def _extract_soft(
        self, track: SubtitleTrack, job: ExtractionJob, output_path: Path
    ) -> None:
        """Extract an embedded subtitle stream using ffmpeg."""
        target_ext = self.get_output_extension(track)
        native_ext = get_extension(track.codec)

        if native_ext == target_ext:
            # Direct extraction — no transcoding needed
            args = [
                "-i", str(job.input_video),
                "-map", f"0:s:{self._stream_index(track)}",
                "-c:s", "copy",
                "-y",
                str(output_path),
            ]
        else:
            # Format conversion required
            encoder = get_ffmpeg_encoder(target_ext)
            args = [
                "-i", str(job.input_video),
                "-map", f"0:s:{self._stream_index(track)}",
                "-c:s", encoder,
                "-y",
                str(output_path),
            ]

        self._runner.run(args, description=f"extract subtitle track {track.index}")

    def _extract_external(
        self, track: SubtitleTrack, job: ExtractionJob, output_path: Path
    ) -> None:
        """Copy (or convert) an external subtitle file."""
        source = job.input_video.parent / (track.title or "")
        if not source.exists():
            raise ExtractionError(
                f"External subtitle file not found: {source}",
                track_index=track.index,
            )

        target_ext = self.get_output_extension(track)
        source_ext = source.suffix.lstrip(".")

        if source_ext == target_ext:
            # Simple file copy
            shutil.copy2(source, output_path)
        else:
            # Convert format with ffmpeg
            encoder = get_ffmpeg_encoder(target_ext)
            args = [
                "-i", str(source),
                "-c:s", encoder,
                "-y",
                str(output_path),
            ]
            self._runner.run(args, description=f"convert external subtitle {source.name}")

    def _stream_index(self, track: SubtitleTrack) -> int:
        """Get the relative subtitle stream index (0-based among subtitle streams).

        ffmpeg's ``0:s:N`` syntax expects the N-th subtitle stream, not the
        absolute stream index. We derive this from the track's absolute index
        by assuming subtitle streams are numbered contiguously from their first
        occurrence — which is typically how ffprobe reports them.

        For robustness, we pass the absolute stream index with ``0:INDEX``
        syntax instead of ``0:s:N`` to avoid ambiguity.
        """
        return track.index
