"""Bitmap subtitle extractor for graphical subtitle formats.

Handles PGS (Blu-ray .sup), VobSub (DVD .sub/.idx), DVB, and XSub
bitmap subtitle tracks. Extracts as-is via ffmpeg stream copy, with
optional mkvextract backend for higher-fidelity MKV extraction.

Reference: ffmpeg docs — https://ffmpeg.org/ffmpeg-codecs.html
           mkvextract — https://mkvtoolnix.download/
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
from .codec_map import get_extension

logger = logging.getLogger(__name__)

# Bitmap subtitle codecs that should be extracted as-is (not converted to text)
_BITMAP_CODECS: set[str] = {
    "dvd_subtitle",          # VobSub (DVD)
    "hdmv_pgs_subtitle",     # PGS (Blu-ray)
    "pgs",                   # PGS alias
    "xsub",                  # XSub (DivX)
    "dvb_subtitle",          # DVB broadcast subtitles
}

# VobSub requires both .sub and .idx files — ffmpeg outputs them as separate streams
# We handle this by extracting the .sub and noting the .idx in warnings
_VOBSUB_CODECS: set[str] = {"dvd_subtitle"}

# PGS output is a single .sup file
_PGS_CODECS: set[str] = {"hdmv_pgs_subtitle", "pgs"}


class BitmapSubExtractor(SubtitleExtractor):
    """Extract bitmap (graphical) subtitles to their native file formats.

    This extractor handles bitmap subtitle codecs that cannot be directly
    converted to text SRT/ASS. The output is the native bitmap format:

    - PGS (hdmv_pgs_subtitle) → .sup
    - VobSub (dvd_subtitle)   → .sub / .idx pair
    - DVB (dvb_subtitle)       → .sub
    - XSub (xsub)              → .sub

    For OCR-based conversion to text, use OCRHardSubExtractor instead.

    When mkvextract is available and the input is MKV, it is used as the
    preferred backend for higher-fidelity extraction. Falls back to ffmpeg.
    """

    def __init__(self) -> None:
        self._runner = FFmpegRunner()

    # --- SubtitleExtractor interface ----------------------------------------

    def can_extract(self, track: SubtitleTrack, job: ExtractionJob) -> bool:
        """Return True if this track is a bitmap subtitle codec."""
        return (
            track.type in (SubtitleType.SOFT, SubtitleType.EXTERNAL)
            and track.codec.lower() in _BITMAP_CODECS
        )

    def get_output_extension(self, track: SubtitleTrack) -> str:
        """Return the native file extension for this bitmap codec."""
        return get_extension(track.codec)

    def extract(self, track: SubtitleTrack, job: ExtractionJob) -> Path:
        """Extract a bitmap subtitle track to its native format."""
        ext = self.get_output_extension(track)
        stem = job.input_video.stem.rstrip(". ")

        # Build label for filename — include track index for disambiguation
        if track.language:
            label = f"{track.language}_{track.index}"
        elif track.type == SubtitleType.SOFT:
            label = f"track_{track.index}"
        else:
            label = "external"

        output_path = job.output_dir / f"{stem}.{label}.{ext}"

        # Try mkvextract first for MKV files (higher fidelity)
        if job.input_video.suffix.lower() == ".mkv" and _mkvextract_available():
            try:
                self._extract_mkvextract(track, job, output_path, ext)
            except ExtractionError:
                logger.info(
                    "mkvextract failed for track %d, falling back to ffmpeg",
                    track.index,
                )
                self._extract_ffmpeg(track, job, output_path)
        else:
            self._extract_ffmpeg(track, job, output_path)

        # Verify output
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise ExtractionError(
                f"Extracted bitmap subtitle file is empty: {output_path}",
                track_index=track.index,
            )

        logger.info("Extracted bitmap subtitle: %s", output_path.name)
        return output_path

    # --- Backend-specific extraction ----------------------------------------

    def _extract_ffmpeg(
        self, track: SubtitleTrack, job: ExtractionJob, output_path: Path
    ) -> None:
        """Extract bitmap subtitle using ffmpeg stream copy.

        ffmpeg -i input -map 0:s:N -c:s copy output.ext
        """
        args = [
            "-i", str(job.input_video),
            "-map", f"0:{track.index}",
            "-c:s", "copy",
            "-y",
            str(output_path),
        ]
        self._runner.run(
            args,
            description=f"extract bitmap subtitle track {track.index}",
        )

    def _extract_mkvextract(
        self, track: SubtitleTrack, job: ExtractionJob, output_path: Path, ext: str
    ) -> None:
        """Extract bitmap subtitle using mkvextract (mkvtoolnix).

        mkvextract tracks input.mkv track_id:output_file

        mkvextract uses 1-based track IDs. For VobSub, it outputs .sub and .idx.
        For PGS, it outputs .sup.
        """
        import subprocess

        mkv_path = shutil.which("mkvextract")
        if not mkv_path:
            raise ExtractionError("mkvextract not found")

        # mkvextract uses 1-based track numbering
        track_id = str(track.index + 1)
        cmd = [mkv_path, "tracks", str(job.input_video), f"{track_id}:{output_path}"]

        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=120)
        if result.returncode != 0:
            raise ExtractionError(
                f"mkvextract failed for track {track.index}",
                track_index=track.index,
            )


def _mkvextract_available() -> bool:
    """Check if mkvextract (from mkvtoolnix) is available on PATH."""
    return shutil.which("mkvextract") is not None


def is_bitmap_codec(codec: str) -> bool:
    """Return True if the given codec name is a bitmap subtitle format.

    Useful for other modules to check without importing the extractor.
    """
    return codec.lower() in _BITMAP_CODECS
