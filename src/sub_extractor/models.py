"""Core data models for the Sub Extractor pipeline.

All primary models use frozen dataclasses for immutability where possible.
The ExtractionJob is intentionally mutable - it acts as the shared pipeline context.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .enums import SubtitleType, VideoFormat


# ---------------------------------------------------------------------------
# Immutable descriptors (frozen dataclasses)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SubtitleTrack:
    """Descriptor for a single subtitle track.

    Immutable so downstream stages cannot accidentally mutate track metadata.
    """

    index: int                          # Stream index from ffprobe (0-based)
    codec: str                          # Codec name: 'subrip', 'ass', 'mov_text', etc.
    language: Optional[str] = None      # ISO 639-2/3 language code (e.g., 'eng', 'chi')
    title: Optional[str] = None         # Human-readable track title from container metadata
    is_forced: bool = False             # Disposition: forced subtitles
    is_default: bool = False            # Disposition: default track
    is_hearing_impaired: bool = False   # Disposition: hearing impaired
    type: SubtitleType = SubtitleType.SOFT


@dataclass(frozen=True)
class AudioTrack:
    """Descriptor for an audio stream (needed for remux and language matching)."""

    index: int
    codec: str                          # e.g., 'aac', 'mp3', 'flac', 'opus'
    language: Optional[str] = None
    channels: int = 2
    title: Optional[str] = None


@dataclass(frozen=True)
class VideoInfo:
    """Immutable snapshot of everything we know about a video file.

    Built once by the Input layer and then read by all downstream stages.
    """

    path: Path
    format: VideoFormat
    duration_seconds: float
    video_codec: str                    # e.g., 'h264', 'hevc', 'vp9'
    width: int
    height: int
    bit_rate: Optional[int] = None      # Overall bit rate in bits/sec
    audio_tracks: List[AudioTrack] = field(default_factory=list)
    subtitle_tracks: List[SubtitleTrack] = field(default_factory=list)

    @property
    def has_soft_subtitles(self) -> bool:
        """True if at least one soft subtitle track exists."""
        return any(t.type == SubtitleType.SOFT for t in self.subtitle_tracks)

    @property
    def subtitle_count(self) -> int:
        """Total number of subtitle tracks (all types)."""
        return len(self.subtitle_tracks)

    @property
    def stem(self) -> str:
        """File name without extension."""
        return self.path.stem


# ---------------------------------------------------------------------------
# Mutable pipeline job object
# ---------------------------------------------------------------------------

@dataclass
class ExtractionJob:
    """Mutable context object passed through every pipeline stage.

    The pipeline input layer populates initial fields. Each subsequent stage
    reads what it needs and writes its results back. This is the single
    shared state object for the entire extraction run.
    """

    # -- User-supplied settings ----------------------------------------------
    input_video: Path                           # Path to the input video file
    output_dir: Path                            # Directory to write results to
    keep_video: bool = True                     # Whether to produce clean video
    target_languages: Optional[List[str]] = None  # Filter: only these language codes
    target_track_indices: Optional[List[int]] = None  # Filter: only these track indices
    include_external: bool = True               # Also copy sidecar subtitle files
    preferred_sub_format: str = "srt"           # Convert subtitles to this format

    # -- Populated by pipeline stages ----------------------------------------
    video_info: Optional[VideoInfo] = None      # Set by Input stage
    extracted_subtitles: List[Path] = field(default_factory=list)  # Set by Extraction
    output_video: Optional[Path] = None         # Set by Processing
    errors: List[str] = field(default_factory=list)    # Non-fatal per-track errors
    warnings: List[str] = field(default_factory=list)  # Non-blocking warnings

    # -- Derived properties --------------------------------------------------
    @property
    def success(self) -> bool:
        """True if no errors occurred during the pipeline run."""
        return len(self.errors) == 0

    @property
    def has_warnings(self) -> bool:
        """True if warnings were recorded."""
        return len(self.warnings) > 0

    @property
    def total_output_files(self) -> int:
        """Count of all output files produced."""
        count = len(self.extracted_subtitles)
        if self.output_video is not None:
            count += 1
        return count
