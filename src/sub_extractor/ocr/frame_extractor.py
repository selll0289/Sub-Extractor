"""Extract frames from video files via ffmpeg pipe.

Uses ffmpeg's ``image2pipe`` protocol to stream decoded frames directly
into memory as numpy arrays — zero disk I/O, constant memory usage.

Reference:
    ffmpeg pipe protocol: https://ffmpeg.org/ffmpeg-protocols.html#pipe
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Generator, Optional, Tuple

import numpy as np

from ..exceptions import FFmpegExecutionError
from ..ffmpeg import find_ffmpeg, find_ffprobe

logger = logging.getLogger(__name__)


class FrameExtractor:
    """Extract video frames as numpy arrays via ffmpeg subprocess pipe.

    Usage::

        extractor = FrameExtractor(Path("movie.mkv"))
        for frame_idx, frame in extractor.iter_frames(1.0):
            process(frame)  # frame is an H×W×3 BGR numpy array
    """

    def __init__(self, video_path: Path) -> None:
        self._video_path = video_path
        self._ffmpeg_path = find_ffmpeg()
        self._width: int = 0
        self._height: int = 0
        self._fps: float = 0.0
        self._duration: float = 0.0
        self._probed = False

    # --- Properties (lazy probed) -------------------------------------------

    @property
    def fps(self) -> float:
        """Frames per second of the video."""
        if not self._probed:
            self._probe_video()
        return self._fps

    @property
    def width(self) -> int:
        """Video width in pixels."""
        if not self._probed:
            self._probe_video()
        return self._width

    @property
    def height(self) -> int:
        """Video height in pixels."""
        if not self._probed:
            self._probe_video()
        return self._height

    @property
    def duration(self) -> float:
        """Video duration in seconds."""
        if not self._probed:
            self._probe_video()
        return self._duration

    # --- Public API ----------------------------------------------------------

    def iter_frames(
        self,
        interval_seconds: float = 1.0,
        *,
        crop_region: Optional[Tuple[int, int, int, int]] = None,
        start_time: float = 0.0,
        end_time: Optional[float] = None,
    ) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Yield (frame_index, frame_array) tuples at the given interval.

        Args:
            interval_seconds: Time between extracted frames.
            crop_region: Optional (x, y, w, h) crop rectangle.
            start_time: Begin extraction at this timestamp (seconds).
            end_time: End extraction at this timestamp (seconds), or None for EOF.

        Yields:
            Tuple of (frame_index, BGR image as numpy array).
        """
        fps = self.fps
        if fps <= 0:
            raise FFmpegExecutionError("Cannot determine video FPS")

        frame_step = max(1, int(fps * interval_seconds))
        cmd = self._build_command(
            frame_step, crop_region, start_time, end_time
        )

        frame_width = crop_region[2] if crop_region else self.width
        frame_height = crop_region[3] if crop_region else self.height
        frame_size = frame_width * frame_height * 3  # BGR = 3 bytes/pixel

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=frame_size * 2,
        )

        frame_idx = int(start_time * fps) if start_time > 0 else 0
        try:
            while True:
                raw = proc.stdout.read(frame_size)
                if not raw or len(raw) < frame_size:
                    break
                frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                    frame_height, frame_width, 3
                )
                yield frame_idx, frame
                frame_idx += frame_step
        finally:
            proc.stdout.close()
            proc.wait()

    def read_one_frame(
        self, frame_number: int, crop_region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[np.ndarray]:
        """Read a single frame by its index (0-based).

        Returns None if the frame number exceeds video duration.
        """
        fps = self.fps
        if fps <= 0:
            return None

        seek_time = frame_number / fps
        cmd = self._build_single_frame_command(seek_time, crop_region)

        frame_width = crop_region[2] if crop_region else self.width
        frame_height = crop_region[3] if crop_region else self.height
        frame_size = frame_width * frame_height * 3

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        raw = proc.stdout.read(frame_size)
        proc.stdout.close()
        proc.wait()

        if not raw or len(raw) < frame_size:
            return None
        return np.frombuffer(raw, dtype=np.uint8).reshape(
            frame_height, frame_width, 3
        )

    # --- Internal ------------------------------------------------------------

    def _probe_video(self) -> None:
        """Extract FPS, resolution, and duration from ffprobe."""
        ffprobe_path = find_ffprobe()
        cmd = [
            ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(self._video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            raise FFmpegExecutionError(f"ffprobe failed: {result.stderr}")

        import json
        probe = json.loads(result.stdout)
        streams = probe.get("streams", [])
        fmt = probe.get("format", {})

        # Find video stream
        for s in streams:
            if s.get("codec_type") == "video":
                self._width = int(s.get("width", 0))
                self._height = int(s.get("height", 0))
                # Parse FPS from r_frame_rate (e.g., "24000/1001" or "30/1")
                fps_str = s.get("r_frame_rate", "0/1")
                num, den = fps_str.split("/")
                self._fps = float(num) / float(den) if int(den) != 0 else 0.0
                break

        self._duration = float(fmt.get("duration", 0))
        self._probed = True

    def _build_command(
        self,
        frame_step: int,
        crop_region: Optional[Tuple[int, int, int, int]],
        start_time: float,
        end_time: Optional[float],
    ) -> list[str]:
        """Build the ffmpeg command for frame extraction via pipe."""
        vf_parts = [f"select=not(mod(n\\,{frame_step}))"]

        if crop_region:
            x, y, w, h = crop_region
            vf_parts.append(f"crop={w}:{h}:{x}:{y}")

        cmd = [self._ffmpeg_path]

        if start_time > 0:
            cmd += ["-ss", str(start_time)]
        if end_time is not None:
            cmd += ["-to", str(end_time)]

        cmd += [
            "-i", str(self._video_path),
            "-an",              # No audio
            "-loglevel", "error",
            "-vf", ",".join(vf_parts),
            "-vsync", "0",      # No frame duplication
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-",
        ]
        return cmd

    def _build_single_frame_command(
        self,
        seek_time: float,
        crop_region: Optional[Tuple[int, int, int, int]],
    ) -> list[str]:
        """Build ffmpeg command to read a single frame at a given timestamp."""
        vf_parts: list[str] = []
        if crop_region:
            x, y, w, h = crop_region
            vf_parts.append(f"crop={w}:{h}:{x}:{y}")

        cmd = [
            self._ffmpeg_path,
            "-ss", str(seek_time),
            "-i", str(self._video_path),
            "-vframes", "1",
            "-an",
            "-loglevel", "error",
        ]
        if vf_parts:
            cmd += ["-vf", ",".join(vf_parts)]

        cmd += [
            "-vsync", "0",
            "-f", "image2pipe",
            "-pix_fmt", "bgr24",
            "-vcodec", "rawvideo",
            "-",
        ]
        return cmd
