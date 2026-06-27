"""Unit tests for the detection layer."""

from pathlib import Path

from sub_extractor.enums import SubtitleType, VideoFormat
from sub_extractor.models import ExtractionJob, SubtitleTrack, VideoInfo
from sub_extractor.detection.soft_sub_detector import SoftSubDetector
from sub_extractor.detection.external_sub_detector import ExternalSubDetector


def _make_job(input_video: Path) -> ExtractionJob:
    """Create a minimal ExtractionJob for detector tests."""
    return ExtractionJob(
        input_video=input_video,
        output_dir=Path("."),
    )


class TestSoftSubDetector:
    def test_detects_soft_tracks(self):
        detector = SoftSubDetector()
        info = VideoInfo(
            path=Path("/test.mkv"),
            format=VideoFormat.MKV,
            duration_seconds=60,
            video_codec="h264",
            width=1920,
            height=1080,
            subtitle_tracks=[
                SubtitleTrack(index=2, codec="subrip", language="eng", type=SubtitleType.SOFT),
                SubtitleTrack(index=3, codec="ass", language="chi", type=SubtitleType.SOFT),
            ],
        )
        tracks = detector.detect(info, _make_job(Path("/test.mkv")))
        assert len(tracks) == 2
        assert all(t.type == SubtitleType.SOFT for t in tracks)

    def test_no_tracks(self):
        detector = SoftSubDetector()
        info = VideoInfo(
            path=Path("/test.mp4"),
            format=VideoFormat.MP4,
            duration_seconds=60,
            video_codec="h264",
            width=1280,
            height=720,
            subtitle_tracks=[],
        )
        tracks = detector.detect(info, _make_job(Path("/test.mp4")))
        assert len(tracks) == 0

    def test_detection_type(self):
        detector = SoftSubDetector()
        assert detector.detection_type == SubtitleType.SOFT


class TestExternalSubDetector:
    def test_detects_srt_sidecar(self, tmp_path):
        # Create a video file and a matching .srt file
        video = tmp_path / "movie.mkv"
        video.touch()
        srt = tmp_path / "movie.en.srt"
        srt.touch()

        info = VideoInfo(
            path=video,
            format=VideoFormat.MKV,
            duration_seconds=60,
            video_codec="h264",
            width=1920,
            height=1080,
        )

        detector = ExternalSubDetector()
        tracks = detector.detect(info, _make_job(video))

        assert len(tracks) >= 1
        en_track = [t for t in tracks if t.language == "eng"]
        assert len(en_track) == 1
        assert en_track[0].codec == "subrip"
        assert en_track[0].type == SubtitleType.EXTERNAL

    def test_detects_ass_sidecar(self, tmp_path):
        video = tmp_path / "movie.mp4"
        video.touch()
        ass = tmp_path / "movie.zh-Hans.ass"
        ass.touch()

        info = VideoInfo(
            path=video,
            format=VideoFormat.MP4,
            duration_seconds=60,
            video_codec="h264",
            width=1280,
            height=720,
        )

        detector = ExternalSubDetector()
        tracks = detector.detect(info, _make_job(video))

        chi_tracks = [t for t in tracks if t.language == "chi"]
        assert len(chi_tracks) >= 1

    def test_no_sidecar(self, tmp_path):
        video = tmp_path / "movie.mkv"
        video.touch()
        # No matching subtitle files

        info = VideoInfo(
            path=video,
            format=VideoFormat.MKV,
            duration_seconds=60,
            video_codec="h264",
            width=1920,
            height=1080,
        )

        detector = ExternalSubDetector()
        tracks = detector.detect(info, _make_job(video))
        assert len(tracks) == 0

    def test_detection_type(self):
        detector = ExternalSubDetector()
        assert detector.detection_type == SubtitleType.EXTERNAL
