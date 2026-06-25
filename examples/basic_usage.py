#!/usr/bin/env python3
"""Basic usage example for Sub Extractor.

Run this script to see how to use Sub Extractor programmatically.
"""

import sys
from pathlib import Path

# Allow running from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sub_extractor.models import ExtractionJob
from sub_extractor.pipeline import Pipeline


def main():
    # Path to your video file
    video_path = Path("path/to/your/movie.mkv")

    # Output directory for subtitles and clean video
    output_dir = Path("./subtitles")

    if not video_path.exists():
        print(f"Video not found: {video_path}")
        print("This is a demo script. Replace the path with an actual video file.")
        print()
        print("Usage from the command line:")
        print(f"  sub-extractor extract {video_path} -o {output_dir}")
        return

    # Create the extraction job
    job = ExtractionJob(
        input_video=video_path,
        output_dir=output_dir,
        keep_video=True,                # Also produce clean video
        preferred_sub_format="srt",     # Output format
        include_external=True,          # Find sidecar files too
    )

    # Run the pipeline
    pipeline = Pipeline()
    job = pipeline.run(job)

    # Print results
    print(f"\n--- Results ---")
    print(f"Success: {job.success}")
    print(f"Extracted subtitles ({len(job.extracted_subtitles)}):")
    for p in job.extracted_subtitles:
        print(f"  - {p}")
    if job.output_video:
        print(f"Clean video: {job.output_video}")
    if job.errors:
        print(f"Errors ({len(job.errors)}):")
        for e in job.errors:
            print(f"  ! {e}")
    if job.warnings:
        print(f"Warnings ({len(job.warnings)}):")
        for w in job.warnings:
            print(f"  ? {w}")


if __name__ == "__main__":
    main()
