"""Enumerations used throughout the Sub Extractor pipeline."""

from enum import Enum, auto


class SubtitleType(Enum):
    """Classification of subtitle presence in a video."""

    SOFT = auto()      # Embedded as a separate track in the container (mkv/mp4)
    HARD = auto()      # Burned into video pixel data (requires OCR - future)
    EXTERNAL = auto()  # Sidecar file alongside the video (srt/ass/vtt)


class VideoFormat(Enum):
    """Supported video container formats."""

    MP4 = "mp4"
    MKV = "mkv"
    AVI = "avi"
    MOV = "mov"
    WEBM = "webm"
    TS = "ts"
    FLV = "flv"
    WMV = "wmv"
    M4V = "m4v"
    OGV = "ogv"


class PipelineStage(Enum):
    """Stages of the extraction pipeline, used for progress reporting and error attribution."""

    INPUT = "input"
    DETECTION = "detection"
    EXTRACTION = "extraction"
    PROCESSING = "processing"
    OUTPUT = "output"
