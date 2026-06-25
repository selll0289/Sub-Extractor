"""Shared test fixtures for Sub Extractor tests."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def fixtures_dir() -> Path:
    """Path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


# ---------------------------------------------------------------------------
# Sample ffprobe JSON outputs
# ---------------------------------------------------------------------------

@pytest.fixture
def ffprobe_mkv_soft_subs() -> dict:
    """ffprobe JSON for an MKV with 2 soft subtitle tracks."""
    return {
        "streams": [
            {
                "index": 0,
                "codec_name": "h264",
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "duration": "120.5",
                "disposition": {"default": 1},
            },
            {
                "index": 1,
                "codec_name": "aac",
                "codec_type": "audio",
                "channels": 2,
                "tags": {"language": "eng", "title": "English"},
            },
            {
                "index": 2,
                "codec_name": "subrip",
                "codec_type": "subtitle",
                "tags": {"language": "eng", "title": "English SDH"},
                "disposition": {"default": 1, "forced": 0, "hearing_impaired": 1},
            },
            {
                "index": 3,
                "codec_name": "ass",
                "codec_type": "subtitle",
                "tags": {"language": "chi", "title": "Chinese Simplified"},
                "disposition": {"default": 0, "forced": 0},
            },
        ],
        "format": {
            "filename": "test.mkv",
            "duration": "120.500000",
            "bit_rate": "5000000",
        },
    }


@pytest.fixture
def ffprobe_mp4_no_subs() -> dict:
    """ffprobe JSON for an MP4 with no subtitle tracks."""
    return {
        "streams": [
            {
                "index": 0,
                "codec_name": "h264",
                "codec_type": "video",
                "width": 1280,
                "height": 720,
                "duration": "60.0",
            },
            {
                "index": 1,
                "codec_name": "aac",
                "codec_type": "audio",
                "channels": 2,
                "tags": {"language": "eng"},
            },
        ],
        "format": {
            "filename": "test.mp4",
            "duration": "60.000000",
        },
    }


@pytest.fixture
def ffprobe_mov_text() -> dict:
    """ffprobe JSON for MP4 with mov_text subtitle."""
    return {
        "streams": [
            {
                "index": 0,
                "codec_name": "h264",
                "codec_type": "video",
                "width": 1920,
                "height": 1080,
                "duration": "90.0",
            },
            {
                "index": 1,
                "codec_name": "aac",
                "codec_type": "audio",
                "channels": 2,
                "tags": {"language": "eng"},
            },
            {
                "index": 2,
                "codec_name": "mov_text",
                "codec_type": "subtitle",
                "tags": {"language": "eng"},
                "disposition": {"default": 0, "forced": 1},
            },
        ],
        "format": {
            "filename": "test.mp4",
            "duration": "90.000000",
        },
    }
