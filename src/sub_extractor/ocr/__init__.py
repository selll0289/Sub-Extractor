"""OCR subpackage for hardcoded (burned-in) subtitle extraction.

Provides a complete pipeline for detecting and extracting burned-in subtitles
from video frames using OCR (Optical Character Recognition).

Pipeline stages:
    1. Frame extraction  (frame_extractor.py)
    2. Image preprocessing (preprocessor.py)
    3. Text recognition    (engine.py)
    4. Deduplication       (deduplicator.py)
    5. Timestamp assignment (timestamp.py)
    6. Output formatting   (formatter.py)

Usage::

    from sub_extractor.ocr import run_ocr_pipeline

    entries = run_ocr_pipeline(
        video_path=Path("movie.mkv"),
        engine="easyocr",
        language="ch_sim",
        frame_interval=1.0,
        confidence_threshold=0.7,
        progress_callback=my_callback,
    )

Dependencies:
    - opencv-python (required for preprocessing)
    - easyocr or paddleocr (required for text recognition)

References:
    - VideoSubFinder: https://sourceforge.net/projects/videosubfinder/
    - video-subtitle-extractor: https://github.com/YaoFANGUK/video-subtitle-extractor
"""

from __future__ import annotations

__all__ = [
    "OCR_AVAILABLE",
    "get_available_engines",
    "run_ocr_pipeline",
    "OCREngine",
    "OCRResult",
    "SubtitleEntry",
    "FrameExtractor",
    "SubtitleDeduplicator",
]

# ---------------------------------------------------------------------------
# Graceful degradation — check if OCR dependencies are installed
# ---------------------------------------------------------------------------

try:
    import cv2  # noqa: F401
    _OPENCV_AVAILABLE = True
except ImportError:
    _OPENCV_AVAILABLE = False

try:
    import easyocr  # noqa: F401
    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False

try:
    import paddleocr  # noqa: F401
    _PADDLEOCR_AVAILABLE = True
except ImportError:
    _PADDLEOCR_AVAILABLE = False

OCR_AVAILABLE = _OPENCV_AVAILABLE and (_EASYOCR_AVAILABLE or _PADDLEOCR_AVAILABLE)


def get_available_engines() -> list[str]:
    """Return a list of OCR engine names that are installed and ready to use.

    Returns:
        List of engine names, e.g. ``['easyocr', 'paddleocr']`` or ``[]``.
    """
    engines: list[str] = []
    if _OPENCV_AVAILABLE:
        if _EASYOCR_AVAILABLE:
            engines.append("easyocr")
        if _PADDLEOCR_AVAILABLE:
            engines.append("paddleocr")
    return engines


# ---------------------------------------------------------------------------
# Lazy imports to avoid circular dependency and allow graceful degradation
# ---------------------------------------------------------------------------


def run_ocr_pipeline(
    video_path,
    *,
    engine: str = "easyocr",
    language: str = "ch_sim",
    frame_interval: float = 1.0,
    confidence_threshold: float = 0.7,
    subtitle_region: str = "bottom",
    output_format: str = "srt",
    progress_callback=None,
    video_fps: float | None = None,
    video_width: int = 0,
    video_height: int = 0,
):
    """Run the complete OCR pipeline on a video file.

    This is the main entry point. It orchestrates all stages from frame
    extraction through final formatting.

    Args:
        video_path: Path to the video file.
        engine: OCR engine name ('easyocr' or 'paddleocr').
        language: OCR language code (e.g., 'ch_sim', 'en', 'ch_sim+en').
        frame_interval: Seconds between analyzed frames.
        confidence_threshold: Minimum OCR confidence (0.0–1.0).
        subtitle_region: Where to look for subs ('bottom', 'top', 'full').
        output_format: Output subtitle format ('srt' or 'ass').
        progress_callback: Optional callable(stage, message, fraction).
        video_fps: Frames per second (auto-detected if None).
        video_width: Video frame width in pixels.
        video_height: Video frame height in pixels.

    Returns:
        List of SubtitleEntry objects.

    Raises:
        ImportError: If required OCR dependencies are not installed.
    """
    from .engine import create_engine
    from .frame_extractor import FrameExtractor
    from .preprocessor import preprocess, detect_subtitle_region
    from .deduplicator import SubtitleDeduplicator
    from .timestamp import frame_index_to_time
    from .formatter import to_srt, to_ass

    if not OCR_AVAILABLE:
        raise ImportError(
            "OCR support requires additional dependencies. "
            "Install with: pip install sub-extractor[ocr-easyocr]"
        )

    # 1. Create OCR engine
    if progress_callback:
        progress_callback("ocr_init", "Initializing OCR engine...", 0.05)
    ocr_engine = create_engine(engine, [language])

    # 2. Set up frame extraction
    extractor = FrameExtractor(video_path)
    actual_fps = video_fps or extractor.fps
    region = None

    if subtitle_region != "full":
        # Infer crop region from first frame
        if progress_callback:
            progress_callback("ocr_init", "Detecting subtitle region...", 0.1)
        first_frame = extractor.read_one_frame(60)  # ~1 second in
        if first_frame is not None:
            region = detect_subtitle_region(
                first_frame, region_hint=subtitle_region
            )

    # 3. Extract and process frames
    if progress_callback:
        progress_callback("ocr_extract", "Extracting frames for OCR...", 0.15)

    dedup = SubtitleDeduplicator(
        confidence_threshold=confidence_threshold,
        similarity_threshold=0.85,
    )

    frame_count = 0
    estimated_total = int(extractor.duration / frame_interval) if extractor.duration else 0

    for frame_idx, frame in extractor.iter_frames(frame_interval, crop_region=region):
        # Preprocess
        processed = preprocess(frame)

        # OCR
        results = ocr_engine.recognize(processed)
        frame_time = frame_index_to_time(frame_idx, actual_fps)

        # Deduplicate
        if results:
            text = " ".join(r.text for r in results)
            confidence = sum(r.confidence for r in results) / len(results)
            dedup.add(frame_idx, frame_time, text, confidence)

        frame_count += 1
        if progress_callback and estimated_total and frame_count % 50 == 0:
            fraction = 0.15 + 0.6 * (frame_count / max(estimated_total, 1))
            progress_callback(
                "ocr_extract",
                f"OCR: {frame_count}/{estimated_total} frames",
                min(fraction, 0.75),
            )

    # 4. Finalize deduplication
    if progress_callback:
        progress_callback("ocr_dedup", "Deduplicating results...", 0.8)
    entries = dedup.finalize()

    if progress_callback:
        progress_callback("ocr_done", f"Detected {len(entries)} subtitle lines", 1.0)

    return entries
