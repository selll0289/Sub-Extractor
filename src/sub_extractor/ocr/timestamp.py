"""Timestamp conversion utilities for subtitle generation.

Converts between frame indices and time values, and formats time values
for SRT and ASS subtitle file formats.

SRT timestamps:  HH:MM:SS,mmm  (e.g., "01:23:45,678")
ASS timestamps:  H:MM:SS.cc    (e.g., "1:23:45.67")
"""

from __future__ import annotations


def frame_index_to_time(frame_index: int, fps: float) -> float:
    """Convert a 0-based frame index to seconds.

    Args:
        frame_index: 0-based frame number.
        fps: Frames per second.

    Returns:
        Time in seconds.
    """
    if fps <= 0:
        return 0.0
    return frame_index / fps


def format_srt_timestamp(seconds: float) -> str:
    """Format a time in seconds as an SRT timestamp: HH:MM:SS,mmm.

    Args:
        seconds: Time in seconds (can be fractional).

    Returns:
        SRT-formatted timestamp string.

    Example:
        >>> format_srt_timestamp(3661.5)
        '01:01:01,500'
    """
    # Clamp negative values to 0
    if seconds < 0:
        seconds = 0.0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))

    # Handle rounding overflow (e.g., 0.9995 → 1000ms)
    if millis >= 1000:
        millis -= 1000
        secs += 1
    if secs >= 60:
        secs -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        hours += 1

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_ass_timestamp(seconds: float) -> str:
    """Format a time in seconds as an ASS timestamp: H:MM:SS.cc.

    ASS uses centiseconds (1/100s) instead of milliseconds.

    Args:
        seconds: Time in seconds.

    Returns:
        ASS-formatted timestamp string.

    Example:
        >>> format_ass_timestamp(3661.5)
        '1:01:01.50'
    """
    if seconds < 0:
        seconds = 0.0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))

    if centis >= 100:
        centis -= 100
        secs += 1
    if secs >= 60:
        secs -= 60
        minutes += 1
    if minutes >= 60:
        minutes -= 60
        hours += 1

    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"
