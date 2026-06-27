"""Unit tests for the input layer video handler."""

import json
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from sub_extractor.enums import VideoFormat, SubtitleType
from sub_extractor.exceptions import InvalidVideoError, UnsupportedFormatError
from sub_extractor.input.video_input import VideoInputHandler


class TestVideoInputCanHandle:
    def test_handles_mp4(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.mp4"
        p.touch()
        assert handler.can_handle(p) is True

    def test_handles_mkv(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.mkv"
        p.touch()
        assert handler.can_handle(p) is True

    def test_rejects_unsupported(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.rmvb"
        p.touch()
        assert handler.can_handle(p) is False

    def test_handles_avi(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.avi"
        p.touch()
        assert handler.can_handle(p) is True

    def test_handles_mov(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.mov"
        p.touch()
        assert handler.can_handle(p) is True

    def test_handles_webm(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.webm"
        p.touch()
        assert handler.can_handle(p) is True

    def test_handles_ts(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.ts"
        p.touch()
        assert handler.can_handle(p) is True

    def test_handles_flv(self, tmp_path):
        handler = VideoInputHandler()
        p = tmp_path / "video.flv"
        p.touch()
        assert handler.can_handle(p) is True

    def test_rejects_nonexistent(self):
        handler = VideoInputHandler()
        assert handler.can_handle(Path("/nonexistent/video.mp4")) is False

    def test_rejects_directory(self, tmp_path):
        handler = VideoInputHandler()
        d = tmp_path / "dir.mp4"
        d.mkdir()
        assert handler.can_handle(d) is False


class TestVideoInputProcess:
    @patch.object(Path, "is_file", return_value=True)
    def test_process_mkv_with_subs(self, mock_is_file, ffprobe_mkv_soft_subs):
        handler = VideoInputHandler()
        with patch("sub_extractor.input.video_input.ffprobe_json", return_value=ffprobe_mkv_soft_subs):
            info = handler.process(Path("/test/test.mkv"))

        assert info.format == VideoFormat.MKV
        assert info.width == 1920
        assert info.height == 1080
        assert info.duration_seconds == 120.5
        assert info.video_codec == "h264"
        assert len(info.audio_tracks) == 1
        assert info.audio_tracks[0].language == "eng"
        assert len(info.subtitle_tracks) == 2
        assert info.subtitle_tracks[0].codec == "subrip"
        assert info.subtitle_tracks[0].language == "eng"
        assert info.subtitle_tracks[0].is_hearing_impaired is True
        assert info.subtitle_tracks[1].codec == "ass"
        assert info.subtitle_tracks[1].language == "chi"
        assert info.has_soft_subtitles is True

    @patch.object(Path, "is_file", return_value=True)
    def test_process_mp4_no_subs(self, mock_is_file, ffprobe_mp4_no_subs):
        handler = VideoInputHandler()
        with patch("sub_extractor.input.video_input.ffprobe_json", return_value=ffprobe_mp4_no_subs):
            info = handler.process(Path("/test/test.mp4"))

        assert info.format == VideoFormat.MP4
        assert len(info.subtitle_tracks) == 0
        assert info.has_soft_subtitles is False

    def test_process_unsupported_format(self):
        handler = VideoInputHandler()
        with pytest.raises(UnsupportedFormatError):
            handler.process(Path("/test/test.rmvb"))

    @patch.object(Path, "is_file", return_value=True)
    def test_process_no_streams(self, mock_is_file):
        handler = VideoInputHandler()
        probe = {"streams": [], "format": {}}
        with patch("sub_extractor.input.video_input.ffprobe_json", return_value=probe):
            with pytest.raises(InvalidVideoError, match="No streams"):
                handler.process(Path("/test/test.mp4"))

    @patch.object(Path, "is_file", return_value=True)
    def test_process_mov_text_sub(self, mock_is_file, ffprobe_mov_text):
        handler = VideoInputHandler()
        with patch("sub_extractor.input.video_input.ffprobe_json", return_value=ffprobe_mov_text):
            info = handler.process(Path("/test/test.mp4"))

        assert len(info.subtitle_tracks) == 1
        track = info.subtitle_tracks[0]
        assert track.codec == "mov_text"
        assert track.is_forced is True
