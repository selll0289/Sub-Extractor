"""External subtitle detector — discovers sidecar subtitle files."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List

from ..enums import SubtitleType
from ..models import ExtractionJob, SubtitleTrack, VideoInfo
from .base import SubtitleDetector

logger = logging.getLogger(__name__)

# Sidecar file extensions we recognise, mapped to their codec name
_SIDECAR_EXTS: dict[str, str] = {
    ".srt": "subrip",
    ".ass": "ass",
    ".ssa": "ssa",
    ".vtt": "webvtt",
    ".sub": "microdvd",
    ".idx": "dvd_subtitle",  # Usually paired with .sub; we only pick .sub
}

# Common patterns for language tags in filenames
# video.en.srt, video.zh-Hans.ass, video.eng.srt, video_chs.srt
_LANG_PATTERN = re.compile(
    r"[\._]([a-z]{2,3}(?:-[A-Z][a-z]+)?)$",  # after the stem, before the ext
)

# Mapping from common language tags to ISO 639-2 codes
_LANG_ALIASES: dict[str, str] = {
    "chs": "chi", "zh": "chi", "zho": "chi",
    "cht": "chi",
    "jp": "jpn", "ja": "jpn",
    "kr": "kor", "ko": "kor",
    "en": "eng", "eng": "eng",
    "fr": "fre", "fra": "fre",
    "de": "ger", "deu": "ger",
    "es": "spa", "spa": "spa",
    "pt": "por", "por": "por",
    "ru": "rus", "rus": "rus",
    "ar": "ara", "ara": "ara",
    "it": "ita", "ita": "ita",
    "nl": "dut", "nld": "dut",
    "sv": "swe", "swe": "swe",
    "no": "nor", "nor": "nor",
    "da": "dan", "dan": "dan",
    "fi": "fin", "fin": "fin",
    "pl": "pol", "pol": "pol",
    "tr": "tur", "tur": "tur",
    "th": "tha", "tha": "tha",
    "vi": "vie", "vie": "vie",
    "id": "ind", "ind": "ind",
    "ms": "may", "msa": "may",
    "hi": "hin", "hin": "hin",
    "bn": "ben", "ben": "ben",
}


class ExternalSubDetector(SubtitleDetector):
    """Detects external (sidecar) subtitle files next to the video.

    Searches the video's parent directory for files with the same stem
    and a recognised subtitle extension. Attempts to infer language from
    filename patterns like ``movie.en.srt``.
    """

    @property
    def detection_type(self) -> SubtitleType:
        return SubtitleType.EXTERNAL

    def detect(self, video_info: VideoInfo, job: ExtractionJob) -> list[SubtitleTrack]:
        parent = video_info.path.parent
        stem = video_info.stem
        tracks: list[SubtitleTrack] = []

        for ext, codec in _SIDECAR_EXTS.items():
            # Match: movie.srt, movie.en.srt, movie.eng.srt, etc.
            pattern = f"{stem}*{ext}"
            for match in sorted(parent.glob(pattern)):
                relative = match.relative_to(parent)
                language = self._infer_language(match, stem, ext)
                tracks.append(SubtitleTrack(
                    index=-1,  # External tracks have no stream index
                    codec=codec,
                    language=language,
                    title=str(relative),
                    type=SubtitleType.EXTERNAL,
                ))

        logger.info(
            "External subtitle detector: %d sidecar file(s) found for %s",
            len(tracks), video_info.path.name,
        )
        return tracks

    def _infer_language(self, sidecar_path: Path, stem: str, ext: str) -> str | None:
        """Try to extract a language code from the filename.

        Examples:
            movie.en.srt      -> 'eng'
            movie.zh-Hans.ass -> 'chi'
            movie.srt         -> None
        """
        name = sidecar_path.name
        # Remove the stem and the final extension
        suffix_part = name[len(stem):]  # e.g., ".en.srt" or ".srt"

        if not suffix_part or suffix_part == ext:
            return None  # exactly "movie.srt" — no language tag

        # Remove the final extension to get the middle part
        middle = suffix_part[: -len(ext)] if suffix_part.endswith(ext) else suffix_part
        # Remove leading "." or "_"
        middle = middle.lstrip("._")

        if not middle:
            return None

        # Normalize to lowercase and map via aliases
        key = middle.lower()

        # Check alias map first
        if key in _LANG_ALIASES:
            return _LANG_ALIASES[key]

        # Handle language tags with region codes: "zh-Hans" → "chi", "pt-BR" → "por"
        if "-" in key:
            base = key.split("-")[0]
            if base in _LANG_ALIASES:
                return _LANG_ALIASES[base]

        # Standalone 2-3 char code (e.g. "en", "eng", "fr")
        if 2 <= len(key) <= 3 and key.isalpha():
            return _LANG_ALIASES.get(key, key)

        return None
