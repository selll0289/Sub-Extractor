"""ffmpeg/ffprobe interface for Sub Extractor.

Cross-cutting module used by Input, Detection, Extraction, and Processing layers.
Provides ffmpeg binary discovery, subprocess execution, and ffprobe JSON parsing.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from .exceptions import FFmpegExecutionError, FFmpegNotFoundError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Binary discovery
# ---------------------------------------------------------------------------

# Common Windows install locations to search in addition to PATH
_WINDOWS_FFMPEG_DIRS: list[str] = [
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Program Files (x86)\ffmpeg\bin",
    r"C:\tools\ffmpeg\bin",
]


def _find_exe(name: str) -> Optional[str]:
    """Find an executable by name on PATH or common install locations.

    Args:
        name: Base name without extension (e.g., 'ffmpeg', 'ffprobe').

    Returns:
        Absolute path to the executable, or None if not found.
    """
    if os.name == "nt":
        name += ".exe"

    # 1. Check PATH via shutil.which (also respects PATHEXT on Windows)
    found = shutil.which(name)
    if found:
        return found

    # 2. Check common Windows install locations
    if os.name == "nt":
        for base_dir in _WINDOWS_FFMPEG_DIRS:
            candidate = os.path.join(base_dir, name)
            if os.path.isfile(candidate):
                return candidate

    return None


def find_ffmpeg() -> str:
    """Locate the ffmpeg executable.

    Returns:
        Absolute path to ffmpeg.

    Raises:
        FFmpegNotFoundError: If ffmpeg cannot be found.
    """
    path = _find_exe("ffmpeg")
    if path is None:
        raise FFmpegNotFoundError()
    return path


def find_ffprobe() -> str:
    """Locate the ffprobe executable.

    Returns:
        Absolute path to ffprobe.

    Raises:
        FFmpegNotFoundError: If ffprobe cannot be found.
    """
    path = _find_exe("ffprobe")
    if path is None:
        raise FFmpegNotFoundError()
    return path


def check_ffmpeg_available() -> tuple[bool, str, str]:
    """Check if ffmpeg and ffprobe are available and return their versions.

    Returns:
        Tuple of (available: bool, ffmpeg_version: str, ffprobe_version: str).
    """
    try:
        ffmpeg_path = find_ffmpeg()
        result = subprocess.run(
            [ffmpeg_path, "-version"], capture_output=True, encoding="utf-8", errors="replace", timeout=10
        )
        ffmpeg_ver = result.stdout.splitlines()[0] if result.stdout else "unknown"
    except (FFmpegNotFoundError, Exception):
        return False, "not found", "not found"

    try:
        ffprobe_path = find_ffprobe()
        result = subprocess.run(
            [ffprobe_path, "-version"], capture_output=True, encoding="utf-8", errors="replace", timeout=10
        )
        ffprobe_ver = result.stdout.splitlines()[0] if result.stdout else "unknown"
    except (FFmpegNotFoundError, Exception):
        return True, ffmpeg_ver, "not found"

    return True, ffmpeg_ver, ffprobe_ver


# ---------------------------------------------------------------------------
# ffprobe JSON probing
# ---------------------------------------------------------------------------


def ffprobe_json(file_path: Path) -> Dict[str, Any]:
    """Run ffprobe on a video file and return parsed JSON.

    Args:
        file_path: Path to the video file.

    Returns:
        Parsed JSON dictionary with 'format' and 'streams' keys.

    Raises:
        FFmpegExecutionError: If ffprobe fails.
    """
    ffprobe_path = find_ffprobe()
    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace", timeout=60)
    except subprocess.TimeoutExpired as exc:
        raise FFmpegExecutionError(
            f"ffprobe timed out probing: {file_path}", stderr="", returncode=None
        ) from exc
    except OSError as exc:
        raise FFmpegExecutionError(
            f"Failed to launch ffprobe: {exc}", stderr="", returncode=None
        ) from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise FFmpegExecutionError(
            f"ffprobe failed on: {file_path}",
            stderr=stderr,
            returncode=result.returncode,
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise FFmpegExecutionError(
            f"ffprobe returned invalid JSON for: {file_path}",
            stderr=result.stdout[:500],
            returncode=result.returncode,
        ) from exc


# ---------------------------------------------------------------------------
# ffmpeg subprocess runner
# ---------------------------------------------------------------------------


class FFmpegRunner:
    """Convenience wrapper around subprocess for ffmpeg commands.

    Handles path resolution, common error formatting, and logging.
    """

    def __init__(self) -> None:
        self._ffmpeg_path: Optional[str] = None

    @property
    def ffmpeg_path(self) -> str:
        """Lazy-resolve ffmpeg path on first use."""
        if self._ffmpeg_path is None:
            self._ffmpeg_path = find_ffmpeg()
        return self._ffmpeg_path

    def run(
        self,
        args: list[str],
        *,
        timeout: int = 300,
        capture: bool = True,
        description: str = "ffmpeg",
    ) -> subprocess.CompletedProcess:
        """Run an ffmpeg command with consistent error handling.

        Args:
            args: ffmpeg arguments (without the 'ffmpeg' prefix).
            timeout: Maximum seconds to wait.
            capture: If True, capture stdout/stderr.
            description: Human label for error messages.

        Returns:
            CompletedProcess with stdout/stderr.

        Raises:
            FFmpegExecutionError: If the command fails.
        """
        cmd = [self.ffmpeg_path] + args
        logger.debug("Running: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise FFmpegExecutionError(
                f"{description} timed out after {timeout}s",
                stderr="",
                returncode=None,
            ) from exc

        if result.returncode != 0:
            raise FFmpegExecutionError(
                f"{description} failed",
                stderr=result.stderr if capture else "",
                returncode=result.returncode,
            )

        return result
