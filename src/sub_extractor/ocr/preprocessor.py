"""Image preprocessing for OCR.

Applies grayscale conversion, adaptive thresholding, and morphological
operations to improve OCR accuracy on video frame text.

Reference:
    OpenCV image thresholding: https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html
    Subtitle region detection inspired by VideoSubFinder's approach.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np

# OpenCV is conditionally imported at call sites to allow graceful
# degradation when the package is not installed.


def preprocess(
    frame: np.ndarray,
    *,
    denoise: bool = True,
    dilate: bool = False,
) -> np.ndarray:
    """Preprocess a video frame for OCR.

    Steps:
        1. Convert BGR to grayscale.
        2. Apply Gaussian blur to reduce noise.
        3. Use adaptive Gaussian thresholding to binarize.
        4. Optionally denoise and dilate for broken/stroked text.

    Args:
        frame: BGR image as (H, W, 3) numpy array.
        denoise: Apply fastNlMeansDenoising.
        dilate: Apply morphological dilation (good for thin/stroked fonts).

    Returns:
        Binary (0/255) image ready for OCR. Single channel uint8.
    """
    import cv2

    # 1. Grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 2. Gaussian blur (reduce sensor noise, compression artifacts)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 3. Adaptive thresholding — handles varying lighting across the frame
    binary = cv2.adaptiveThreshold(
        blurred,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,   # Block size — must be odd
        2,    # Constant subtracted from mean
    )

    # 4. Optional denoising
    if denoise:
        binary = cv2.fastNlMeansDenoising(binary, None, 10, 7, 21)

    # 5. Optional dilation (connects broken strokes, thickens thin text)
    if dilate:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.dilate(binary, kernel, iterations=1)

    return binary


def detect_subtitle_region(
    frame: np.ndarray,
    *,
    region_hint: str = "bottom",
    bottom_fraction: float = 0.35,
    top_fraction: float = 0.20,
) -> Tuple[int, int, int, int]:
    """Detect the subtitle region in a video frame.

    Uses horizontal projection profile (sum of pixel intensities per row)
    to find rows with high text density. This heuristic works well for
    standard subtitle positioning.

    Args:
        frame: BGR image as (H, W, 3) numpy array.
        region_hint: Where to search — 'bottom', 'top', or 'full'.
        bottom_fraction: Fraction of frame height to scan from bottom.
        top_fraction: Fraction of frame height to scan from top.

    Returns:
        (x, y, width, height) crop rectangle for the subtitle area.
    """
    import cv2

    h, w = frame.shape[:2]

    # For "full", return the entire frame
    if region_hint == "full":
        return (0, 0, w, h)

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Edge detection — text regions have high edge density
    edges = cv2.Canny(gray, 50, 150)

    if region_hint == "bottom":
        # Analyze bottom portion
        start_row = int(h * (1.0 - bottom_fraction))
        roi = edges[start_row:, :]
        # Horizontal projection (sum per row)
        proj = np.sum(roi, axis=1).astype(np.float32)

        if proj.size == 0:
            return (0, start_row, w, h - start_row)

        # Smooth the projection and find peaks
        proj_smooth = cv2.GaussianBlur(proj.reshape(-1, 1), (5, 1), 0).flatten()
        threshold = np.mean(proj_smooth) * 1.5

        # Find first and last rows above threshold (text region)
        active_rows = np.where(proj_smooth > threshold)[0]
        if len(active_rows) == 0:
            # Fallback: return entire bottom portion
            return (0, start_row, w, h - start_row)

        top = start_row + active_rows[0]
        bottom = start_row + active_rows[-1] + 5  # small padding

        # Expand slightly for safety margin
        top = max(start_row - 5, 0)
        bottom = min(bottom + 10, h)

        return (0, top, w, bottom - top)

    elif region_hint == "top":
        # Analyze top portion
        end_row = int(h * top_fraction)
        roi = edges[:end_row, :]
        proj = np.sum(roi, axis=1).astype(np.float32)

        if proj.size == 0:
            return (0, 0, w, end_row)

        proj_smooth = cv2.GaussianBlur(proj.reshape(-1, 1), (5, 1), 0).flatten()
        threshold = np.mean(proj_smooth) * 1.5

        active_rows = np.where(proj_smooth > threshold)[0]
        if len(active_rows) == 0:
            return (0, 0, w, end_row)

        top = active_rows[0]
        bottom = active_rows[-1] + 5
        bottom = min(bottom + 10, end_row)

        return (0, max(top - 5, 0), w, bottom - top)

    else:
        # Unknown hint — return full frame
        return (0, 0, w, h)


def detect_text_mask(
    frame: np.ndarray,
    *,
    region: Tuple[int, int, int, int] | None = None,
) -> np.ndarray:
    """Create a binary mask highlighting text regions in a frame.

    This is a more sophisticated alternative to simple thresholding,
    using MSER (Maximally Stable Extremal Regions) or Canny edge density.

    Args:
        frame: BGR image as (H, W, 3) numpy array.
        region: Optional (x, y, w, h) to restrict detection.

    Returns:
        Binary mask (uint8, 0/255) where white = text.
    """
    import cv2

    if region:
        x, y, w, h = region
        frame = frame[y:y+h, x:x+w]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # MSER for text blob detection
    mser = cv2.MSER_create()
    regions, _ = mser.detectRegions(gray)

    mask = np.zeros_like(gray)
    for r in regions:
        mask[r[:, 1], r[:, 0]] = 255  # MSER returns (y, x) points

    if region:
        # Pad mask back to full frame size
        x, y, w, h = region
        full_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        full_mask[y:y+h, x:x+w] = mask
        mask = full_mask

    return mask
