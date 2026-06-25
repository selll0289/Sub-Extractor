"""Custom exception hierarchy for Sub Extractor."""


class SubExtractorError(Exception):
    """Base exception for all Sub Extractor errors."""
    pass


class FFmpegNotFoundError(SubExtractorError):
    """ffmpeg or ffprobe not found on the system PATH or common install locations."""

    def __init__(self, message: str = None):
        super().__init__(
            message or "ffmpeg/ffprobe not found. Please install ffmpeg and ensure it is on your PATH.\n"
            "  Download: https://ffmpeg.org/download.html\n"
            "  Windows: `winget install ffmpeg` or `choco install ffmpeg`"
        )


class FFmpegExecutionError(SubExtractorError):
    """ffmpeg/ffprobe command failed during execution."""

    def __init__(self, message: str, stderr: str = "", returncode: int = None):
        self.stderr = stderr
        self.returncode = returncode
        full_msg = message
        if stderr:
            full_msg += f"\n--- stderr ---\n{stderr.strip()}"
        if returncode is not None:
            full_msg += f"\nReturn code: {returncode}"
        super().__init__(full_msg)


class InvalidVideoError(SubExtractorError):
    """The input file is not a valid, playable video."""
    pass


class UnsupportedFormatError(SubExtractorError):
    """The video format is not supported by any registered handler."""
    pass


class ExtractionError(SubExtractorError):
    """A subtitle track could not be extracted."""

    def __init__(self, message: str, track_index: int = None):
        self.track_index = track_index
        super().__init__(message)


class ProcessingError(SubExtractorError):
    """Video processing (remux/clean) failed."""
    pass


class NoSubtitlesFoundError(SubExtractorError):
    """No subtitles of any kind were detected for this video."""
    pass


class OutputError(SubExtractorError):
    """Failed to write output files."""
    pass


class ConfigError(SubExtractorError):
    """Configuration is invalid."""
    pass
