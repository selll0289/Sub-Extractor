"""Unit tests for data models."""

import pytest
from pathlib import Path

from sub_extractor.enums import SubtitleType, VideoFormat, PipelineStage
from sub_extractor.models import (
    AudioTrack,
    ExtractionJob,
    SubtitleTrack,
    VideoInfo,
)


class TestSubtitleTrack:
    def test_construction_defaults(self):
        track = SubtitleTrack(index=2, codec="subrip")
        assert track.index == 2
        assert track.codec == "subrip"
        assert track.language is None
        assert track.title is None
        assert track.is_forced is False
        assert track.is_default is False
        assert track.is_hearing_impaired is False
        assert track.type == SubtitleType.SOFT

    def test_external_type(self):
        track = SubtitleTrack(index=-1, codec="subrip", type=SubtitleType.EXTERNAL)
        assert track.type == SubtitleType.EXTERNAL

    def test_frozen_prevents_mutation(self):
        track = SubtitleTrack(index=0, codec="subrip", language="eng")
        with pytest.raises(Exception):
            track.language = "chi"  # type: ignore


class TestVideoInfo:
    def test_construction(self):
        info = VideoInfo(
            path=Path("/test.mkv"),
            format=VideoFormat.MKV,
            duration_seconds=120.5,
            video_codec="h264",
            width=1920,
            height=1080,
        )
        assert info.format == VideoFormat.MKV
        assert info.duration_seconds == 120.5
        assert info.subtitle_count == 0

    def test_has_soft_subtitles(self):
        track = SubtitleTrack(index=2, codec="subrip", type=SubtitleType.SOFT)
        info = VideoInfo(
            path=Path("/test.mkv"),
            format=VideoFormat.MKV,
            duration_seconds=60.0,
            video_codec="h264",
            width=1920,
            height=1080,
            subtitle_tracks=[track],
        )
        assert info.has_soft_subtitles is True
        assert info.subtitle_count == 1

    def test_stem(self):
        info = VideoInfo(
            path=Path("/videos/movie.mkv"),
            format=VideoFormat.MKV,
            duration_seconds=60.0,
            video_codec="h264",
            width=1920,
            height=1080,
        )
        assert info.stem == "movie"


class TestExtractionJob:
    def test_construction(self):
        job = ExtractionJob(
            input_video=Path("/videos/movie.mkv"),
            output_dir=Path("/tmp/out"),
        )
        assert job.keep_video is True
        assert job.include_external is True
        assert job.preferred_sub_format == "srt"
        assert job.video_info is None
        assert job.extracted_subtitles == []
        assert job.success is True
        assert job.total_output_files == 0

    def test_success_with_errors(self):
        job = ExtractionJob(
            input_video=Path("/videos/movie.mkv"),
            output_dir=Path("/tmp/out"),
        )
        job.errors.append("Something went wrong")
        assert job.success is False

    def test_total_output_files(self):
        job = ExtractionJob(
            input_video=Path("/videos/movie.mkv"),
            output_dir=Path("/tmp/out"),
        )
        job.extracted_subtitles = [Path("a.srt"), Path("b.srt")]
        job.output_video = Path("clean.mkv")
        assert job.total_output_files == 3
