"""Subtitle deduplication and merging across consecutive frames.

When OCR runs on sequential video frames, the same subtitle text may
appear across dozens of frames (e.g., a subtitle line displayed for 3
seconds at 30 fps appears in ~90 frames).

The deduplicator merges consecutive frames with the same (or very similar)
text into a single subtitle entry with start_time and end_time spanning
the entire duration the text was visible.

Reference approach:
    Based on the inter-frame text similarity strategy used in
    video-subtitle-extractor (YaoFANGUK) and VideoSubFinder.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import List


@dataclass
class SubtitleEntry:
    """A single subtitle line with timing and confidence.

    Attributes:
        text: The subtitle text.
        start_time: Start time in seconds.
        end_time: End time in seconds.
        confidence: Average OCR confidence across all constituent frames.
    """

    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0


class SubtitleDeduplicator:
    """Merge consecutive OCR results into subtitle entries.

    Usage::

        dedup = SubtitleDeduplicator(confidence_threshold=0.7)
        for frame_idx, timestamp, text, conf in ocr_results:
            dedup.add(frame_idx, timestamp, text, conf)
        entries = dedup.finalize()
    """

    def __init__(
        self,
        confidence_threshold: float = 0.7,
        similarity_threshold: float = 0.85,
        min_duration: float = 0.3,
        max_gap: float = 0.5,
    ) -> None:
        self._confidence_threshold = confidence_threshold
        self._similarity_threshold = similarity_threshold
        self._min_duration = min_duration
        self._max_gap = max_gap

        # Internal accumulation buffer
        self._current_text: str = ""
        self._current_start: float = 0.0
        self._current_end: float = 0.0
        self._current_confidences: List[float] = []
        self._entries: List[SubtitleEntry] = []

    # --- Public API ----------------------------------------------------------

    def add(
        self,
        frame_index: int,
        timestamp: float,
        text: str,
        confidence: float,
    ) -> None:
        """Add one frame's OCR result to the accumulator.

        Args:
            frame_index: Frame number (for diagnostics only).
            timestamp: Time in seconds of this frame.
            text: Recognized text (may be empty string).
            confidence: OCR confidence score (0.0–1.0).
        """
        # Skip low-confidence results
        if confidence < self._confidence_threshold:
            return

        # Skip empty or whitespace-only text
        cleaned = text.strip()
        if not cleaned:
            return

        if not self._current_text:
            # First entry
            self._current_text = cleaned
            self._current_start = timestamp
            self._current_end = timestamp
            self._current_confidences = [confidence]
        elif self._is_similar(cleaned, self._current_text):
            # Same subtitle — extend the end time
            self._current_end = timestamp
            self._current_confidences.append(confidence)
            # Keep the longer/more confident text variant
            if confidence > max(self._current_confidences[:-1], default=0):
                if len(cleaned) >= len(self._current_text):
                    self._current_text = cleaned
        else:
            # Different text — flush current and start new
            self._flush_current()
            self._current_text = cleaned
            self._current_start = timestamp
            self._current_end = timestamp
            self._current_confidences = [confidence]

    def finalize(self) -> List[SubtitleEntry]:
        """Flush any remaining entry and return the complete list.

        Applies post-processing:
        - Filters entries below minimum duration.
        - Merges adjacent entries separated by very short gaps.
        - Sorts by start time.

        Returns:
            Sorted list of SubtitleEntry objects.
        """
        self._flush_current()

        # Filter by minimum duration
        self._entries = [
            e for e in self._entries
            if (e.end_time - e.start_time) >= self._min_duration
        ]

        # Merge entries separated by short gaps with identical text
        merged = self._merge_adjacent(self._entries)

        # Sort by start time
        merged.sort(key=lambda e: e.start_time)

        # Re-index (not needed for SRT — formatter handles numbering)
        return merged

    # --- Internal helpers ----------------------------------------------------

    def _flush_current(self) -> None:
        """Move the current accumulated entry into the entry list."""
        if not self._current_text:
            return

        duration = self._current_end - self._current_start
        if duration >= self._min_duration:
            avg_confidence = (
                sum(self._current_confidences) / len(self._current_confidences)
                if self._current_confidences
                else 0.0
            )
            self._entries.append(SubtitleEntry(
                text=self._current_text,
                start_time=self._current_start,
                end_time=self._current_end,
                confidence=avg_confidence,
            ))

        self._current_text = ""
        self._current_start = 0.0
        self._current_end = 0.0
        self._current_confidences = []

    def _is_similar(self, text_a: str, text_b: str) -> bool:
        """Return True if two text strings are similar enough to merge.

        Uses SequenceMatcher ratio (0.0–1.0) for fuzzy comparison.
        Short strings are compared exactly.
        """
        if text_a == text_b:
            return True

        # Short texts: exact match only
        if len(text_a) < 4 or len(text_b) < 4:
            return text_a == text_b

        # Longer texts: allow small differences (OCR errors)
        ratio = difflib.SequenceMatcher(None, text_a, text_b).ratio()
        return ratio >= self._similarity_threshold

    def _merge_adjacent(
        self, entries: List[SubtitleEntry]
    ) -> List[SubtitleEntry]:
        """Merge entries that are the same text with only a small time gap."""
        if not entries:
            return []

        merged: List[SubtitleEntry] = [entries[0]]
        for current in entries[1:]:
            prev = merged[-1]
            gap = current.start_time - prev.end_time
            if (
                gap <= self._max_gap
                and current.text == prev.text
            ):
                # Merge: extend the previous entry
                prev.end_time = current.end_time
                prev.confidence = max(prev.confidence, current.confidence)
            else:
                merged.append(current)

        return merged
