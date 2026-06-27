"""Subtitle output formatters — SRT and ASS.

Converts a list of SubtitleEntry objects to well-formatted SRT or ASS
subtitle file content strings.

SRT format:
    1
    00:00:01,000 --> 00:00:04,000
    Hello world

ASS format:
    [Script Info]
    ...
    [Events]
    Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    Dialogue: 0,0:00:01.00,0:00:04.00,Default,,0,0,0,,Hello world
"""

from __future__ import annotations

from typing import List

from .deduplicator import SubtitleEntry
from .timestamp import format_ass_timestamp, format_srt_timestamp


def to_srt(entries: List[SubtitleEntry]) -> str:
    """Convert a list of SubtitleEntry to SRT format string.

    Args:
        entries: Subtitle entries sorted by start time.

    Returns:
        Complete SRT file content as a string.
    """
    lines: list[str] = []
    for i, entry in enumerate(entries, start=1):
        start = format_srt_timestamp(entry.start_time)
        end = format_srt_timestamp(entry.end_time)
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(entry.text)
        lines.append("")  # Blank line separator
    return "\n".join(lines)


def to_ass(
    entries: List[SubtitleEntry],
    *,
    video_width: int = 1920,
    video_height: int = 1080,
    font_name: str = "Arial",
    font_size: int = 48,
    title: str = "OCR Extracted Subtitles",
) -> str:
    """Convert a list of SubtitleEntry to ASS format string.

    Args:
        entries: Subtitle entries sorted by start time.
        video_width: Video width for PlayResX header.
        video_height: Video height for PlayResY header.
        font_name: Default font for the style.
        font_size: Default font size.
        title: Script title.

    Returns:
        Complete ASS file content as a string.
    """
    # Calculate sensible margin and alignment based on video size
    margin_v = video_height // 15  # ~10% from bottom for standard subs
    alignment = 2  # Bottom-center

    header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,{alignment},10,10,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"""

    dialogue_lines: list[str] = []
    for entry in entries:
        start = format_ass_timestamp(entry.start_time)
        end = format_ass_timestamp(entry.end_time)
        # Escape ASS special characters: newlines → \N
        text = entry.text.replace("\n", "\\N")
        dialogue_lines.append(
            f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"
        )

    return header + "\n" + "\n".join(dialogue_lines)
