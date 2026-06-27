"""Command-line interface for Sub Extractor.

Built with Click for argument parsing and Rich for terminal output.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

# Fix Unicode encoding issues on Windows terminals (GBK, etc.)
if os.name == "nt":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

from . import __version__
from .enums import PipelineStage
from .exceptions import FFmpegNotFoundError, SubExtractorError
from .ffmpeg import check_ffmpeg_available
from .models import ExtractionJob
from .pipeline import Pipeline

# ---------------------------------------------------------------------------
# Rich console & logging setup
# ---------------------------------------------------------------------------

console = Console()


def _setup_logging(verbose: bool) -> logging.Logger:
    """Configure logging with Rich handler for pretty terminal output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_time=False)],
    )
    return logging.getLogger("sub_extractor")


# ---------------------------------------------------------------------------
# Click CLI group
# ---------------------------------------------------------------------------


@click.group()
@click.version_option(version=__version__, prog_name="sub-extractor")
@click.pass_context
def main(ctx: click.Context) -> None:
    """Sub Extractor — Extract subtitles from video files.

    Supports MP4, MKV, AVI, MOV, WebM, TS, FLV, WMV, M4V, OGV containers.
    Extracts embedded soft subtitles, bitmap (PGS/VobSub) subtitles,
    discovers sidecar files, and OCR hardcoded subtitles.

    Examples:

        sub-extractor extract movie.mkv -o ./subtitles

        sub-extractor extract movie.mp4 -o ./out --languages eng,chi --no-video

        sub-extractor extract movie.mkv -o ./out --ocr --ocr-language ch_sim

        sub-extractor info movie.mkv

        sub-extractor check
    """
    ctx.ensure_object(dict)


# ---------------------------------------------------------------------------
# extract command
# ---------------------------------------------------------------------------


@main.command()
@click.argument("input", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    required=True,
    help="Output directory for subtitles and clean video.",
)
@click.option(
    "--keep-video/--no-video",
    default=True,
    help="Keep a copy of the video without subtitle tracks (default: --keep-video).",
)
@click.option(
    "--sub-format",
    type=click.Choice(["srt", "ass", "ssa", "vtt", "sup", "sub"], case_sensitive=False),
    default="srt",
    help="Preferred subtitle output format (default: srt).",
)
@click.option(
    "--languages",
    type=str,
    default=None,
    help="Comma-separated language codes to extract (e.g., 'eng,chi').",
)
@click.option(
    "--tracks",
    type=str,
    default=None,
    help="Comma-separated track indices to extract (e.g., '0,2').",
)
@click.option(
    "--no-external",
    is_flag=True,
    default=False,
    help="Skip external (sidecar) subtitle files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be extracted without executing.",
)
@click.option(
    "--ocr/--no-ocr",
    default=False,
    help="Enable OCR extraction for hardcoded (burned-in) subtitles.",
)
@click.option(
    "--ocr-engine",
    type=click.Choice(["easyocr", "paddleocr"], case_sensitive=False),
    default="easyocr",
    help="OCR engine for hardcoded subtitle extraction (default: easyocr).",
)
@click.option(
    "--ocr-language",
    type=str,
    default="ch_sim",
    help="OCR language code (e.g., 'ch_sim', 'en', 'ch_sim+en').",
)
@click.option(
    "--ocr-interval",
    type=float,
    default=1.0,
    help="Seconds between analyzed frames for OCR (default: 1.0).",
)
@click.option(
    "--ocr-confidence",
    type=float,
    default=0.7,
    help="Minimum OCR confidence threshold 0.0-1.0 (default: 0.7).",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    default=False,
    help="Enable debug logging.",
)
@click.pass_context
def extract(
    ctx: click.Context,
    input: Path,
    output: Path,
    keep_video: bool,
    sub_format: str,
    languages: Optional[str],
    tracks: Optional[str],
    no_external: bool,
    dry_run: bool,
    ocr: bool,
    ocr_engine: str,
    ocr_language: str,
    ocr_interval: float,
    ocr_confidence: float,
    verbose: bool,
) -> None:
    """Extract subtitles from a video file.

    INPUT is the path to a video file (.mp4, .mkv).
    """
    logger = _setup_logging(verbose)

    # --- Banner ---
    console.print()
    console.print(
        Panel.fit(
            f"[bold bright_cyan]Sub Extractor[/] [dim]v{__version__}[/]",
            border_style="bright_cyan",
        )
    )
    console.print(f"  [dim]Input:[/]  [bold]{input}[/]")
    console.print(f"  [dim]Output:[/] [bold]{output}[/]")
    console.print()

    # --- Build job ---
    job = ExtractionJob(
        input_video=input.resolve(),
        output_dir=output.resolve(),
        keep_video=keep_video,
        target_languages=_parse_comma_list(languages),
        target_track_indices=_parse_int_list(tracks),
        include_external=not no_external,
        preferred_sub_format=sub_format,
        enable_hard_sub_ocr=ocr,
        ocr_engine=ocr_engine,
        ocr_language=ocr_language,
        ocr_frame_interval=ocr_interval,
        ocr_confidence_threshold=ocr_confidence,
    )

    # --- Dry run ---
    if dry_run:
        _do_dry_run(job)
        return

    # --- Run pipeline with Rich progress ---
    pipeline = Pipeline()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[dim]{task.fields[step]}[/]"),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task(
            "[cyan]Processing",
            total=100,
            step="",
        )

        def on_progress(stage: PipelineStage, message: str, fraction: float) -> None:
            pct = int(fraction * 100)
            progress.update(
                task_id,
                completed=pct,
                step=f"[{stage.value}] {message}",
            )

        pipeline.on_progress = on_progress

        try:
            job = pipeline.run(job)
        except FFmpegNotFoundError as exc:
            console.print(f"\n[red]Error:[/] {exc}")
            console.print(
                "\n[yellow]ffmpeg is required but was not found on your system.[/]\n"
                "Install ffmpeg:\n"
                "  Windows: [bold]winget install ffmpeg[/] or [bold]choco install ffmpeg[/]\n"
                "  macOS:   [bold]brew install ffmpeg[/]\n"
                "  Linux:   [bold]sudo apt install ffmpeg[/]\n"
            )
            sys.exit(1)
        except SubExtractorError as exc:
            console.print(f"\n[red]Error:[/] {exc}")
            sys.exit(1)

    # --- Print results ---
    _print_results(job)


# ---------------------------------------------------------------------------
# info command
# ---------------------------------------------------------------------------


@main.command()
@click.argument("input", type=click.Path(exists=True, path_type=Path))
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable debug logging.")
def info(input: Path, verbose: bool) -> None:
    """Show information about a video file and its subtitle tracks."""
    _setup_logging(verbose)

    console.print()
    console.print(
        Panel.fit(
            f"[bold bright_cyan]Sub Extractor[/] [dim]v{__version__}[/]",
            border_style="bright_cyan",
        )
    )

    # Use the pipeline's input stage to probe
    pipeline = Pipeline()
    try:
        handler = pipeline._find_input_handler(input)
        video_info = handler.process(input)
    except SubExtractorError as exc:
        console.print(f"\n[red]Error:[/] {exc}")
        sys.exit(1)

    # --- General info ---
    general = Table(title="Video Information", expand=False)
    general.add_column("Property", style="dim cyan")
    general.add_column("Value", style="bold")
    general.add_row("File", str(video_info.path.name))
    general.add_row("Format", video_info.format.value.upper())
    general.add_row("Codec", video_info.video_codec)
    general.add_row("Resolution", f"{video_info.width}x{video_info.height}")
    general.add_row("Duration", _format_duration(video_info.duration_seconds))
    if video_info.bit_rate:
        general.add_row("Bit rate", f"{video_info.bit_rate / 1000:.0f} kbps")
    console.print(general)

    # --- Audio tracks ---
    if video_info.audio_tracks:
        atable = Table(title="Audio Tracks")
        atable.add_column("#", style="dim")
        atable.add_column("Codec", style="cyan")
        atable.add_column("Language", style="green")
        atable.add_column("Channels", style="dim")
        atable.add_column("Title")
        for a in video_info.audio_tracks:
            atable.add_row(
                str(a.index), a.codec,
                a.language or "—",
                str(a.channels),
                a.title or "—",
            )
        console.print(atable)

    # --- Subtitle tracks ---
    if video_info.subtitle_tracks:
        stable = Table(title="Subtitle Tracks (Embedded)")
        stable.add_column("#", style="dim")
        stable.add_column("Codec", style="cyan")
        stable.add_column("Language", style="green")
        stable.add_column("Flags", style="yellow")
        stable.add_column("Title")
        for s in video_info.subtitle_tracks:
            flags = []
            if s.is_default:
                flags.append("default")
            if s.is_forced:
                flags.append("forced")
            if s.is_hearing_impaired:
                flags.append("SDH")
            stable.add_row(
                str(s.index), s.codec,
                s.language or "—",
                ", ".join(flags) if flags else "—",
                s.title or "—",
            )
        console.print(stable)

    # --- External subtitles ---
    from .detection.external_sub_detector import ExternalSubDetector
    from .models import ExtractionJob
    detector = ExternalSubDetector()
    external = detector.detect(
        video_info,
        ExtractionJob(input_video=input, output_dir=Path(".")),
    )
    if external:
        etable = Table(title="External Subtitle Files")
        etable.add_column("Codec", style="cyan")
        etable.add_column("Language", style="green")
        etable.add_column("File", style="bold")
        for e in external:
            etable.add_row(e.codec, e.language or "—", e.title or "—")
        console.print(etable)
    elif not video_info.subtitle_tracks:
        console.print("\n[yellow]No subtitles detected for this video.[/]")

    console.print()


# ---------------------------------------------------------------------------
# check command
# ---------------------------------------------------------------------------


@main.command()
def check() -> None:
    """Verify that required external tools (ffmpeg/ffprobe) are available."""
    console.print()
    console.print(
        Panel.fit(
            "[bold bright_cyan]Sub Extractor[/] [dim]— System Check[/]",
            border_style="bright_cyan",
        )
    )
    console.print()

    ok, ffmpeg_ver, ffprobe_ver = check_ffmpeg_available()

    table = Table(title="Dependency Check")
    table.add_column("Tool", style="bold")
    table.add_column("Status")
    table.add_column("Version", style="dim")

    ffmpeg_status = "[green][OK][/]" if ok else "[red][MISSING][/]"
    table.add_row("ffmpeg", ffmpeg_status, ffmpeg_ver)

    ffprobe_status = "[green][OK][/]" if ffprobe_ver != "not found" else "[red][MISSING][/]"
    table.add_row("ffprobe", ffprobe_status, ffprobe_ver)

    console.print(table)
    console.print()

    if not ok:
        console.print(
            "[yellow]ffmpeg is required. Install it:[/]\n"
            "  Windows: [bold]winget install ffmpeg[/] or [bold]choco install ffmpeg[/]\n"
            "  macOS:   [bold]brew install ffmpeg[/]\n"
            "  Linux:   [bold]sudo apt install ffmpeg[/]"
        )
    else:
        console.print("[green]All dependencies are available.[/]")

    console.print()

    # Check mkvtoolnix (optional, for enhanced MKV support)
    import shutil
    if shutil.which("mkvextract"):
        console.print("[dim]Optional: mkvtoolnix (mkvextract) found — enhanced MKV support available.[/]")
    else:
        console.print("[dim]Optional: mkvtoolnix not found. MKV extraction will use ffmpeg (works fine).[/]")
    console.print()

    # Check OCR (optional, for hardcoded subtitle extraction)
    from .ocr import OCR_AVAILABLE as ocr_ok, get_available_engines
    engines = get_available_engines()
    if engines:
        console.print(f"[green]Optional: OCR available ({', '.join(engines)}) — hardcoded subtitle extraction enabled.[/]")
    else:
        console.print(
            "[dim]Optional: OCR not installed. "
            "For hardcoded subtitle extraction, install: "
            "pip install sub-extractor[ocr-easyocr][/]"
        )
    console.print()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _parse_comma_list(value: Optional[str]) -> Optional[List[str]]:
    """Parse 'eng,chi,jpn' → ['eng', 'chi', 'jpn']."""
    if not value:
        return None
    return [s.strip().lower() for s in value.split(",") if s.strip()]


def _parse_int_list(value: Optional[str]) -> Optional[List[int]]:
    """Parse '0,2,3' → [0, 2, 3]."""
    if not value:
        return None
    result = []
    for s in value.split(","):
        s = s.strip()
        if s:
            try:
                result.append(int(s))
            except ValueError:
                raise click.BadParameter(f"Invalid track index: '{s}' (must be an integer)")
    return result or None


def _format_duration(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _do_dry_run(job: ExtractionJob) -> None:
    """Print a dry-run summary of what would happen."""
    console.print("[bold yellow]DRY RUN[/] — no files will be modified\n")

    try:
        pipeline = Pipeline()
        handler = pipeline._find_input_handler(job.input_video)
        job.video_info = handler.process(job.input_video)
    except SubExtractorError as exc:
        console.print(f"[red]Error:[/] {exc}")
        return

    vi = job.video_info

    table = Table(title="Plan")
    table.add_column("Action", style="bold")
    table.add_column("Details")

    table.add_row("Input", str(vi.path.name))
    table.add_row("Format", f"{vi.format.value.upper()} — {vi.video_codec} {vi.width}x{vi.height}")
    table.add_row("Duration", _format_duration(vi.duration_seconds))

    if vi.subtitle_tracks:
        for s in vi.subtitle_tracks:
            lang = s.language or "unknown"
            table.add_row(
                "Extract soft sub",
                f"Track {s.index}: [{s.codec}] {lang}"
                + (" (forced)" if s.is_forced else "")
                + (" (default)" if s.is_default else ""),
            )
    else:
        table.add_row("Subtitles", "[dim]No embedded subtitle tracks detected[/]")

    if job.enable_hard_sub_ocr:
        table.add_row(
            "OCR hard subs",
            f"Engine: {job.ocr_engine}, "
            f"Language: {job.ocr_language}, "
            f"Interval: {job.ocr_frame_interval}s",
        )

    if job.keep_video:
        table.add_row("Clean video", f"{job.input_video.stem}_clean{job.input_video.suffix}")
    else:
        table.add_row("Clean video", "[dim]Skipped (--no-video)[/]")

    table.add_row("Output directory", str(job.output_dir))

    console.print(table)
    console.print()


def _print_results(job: ExtractionJob) -> None:
    """Print extraction results summary."""
    console.print()
    if job.success and not job.has_warnings:
        panel = Panel(
            f"[bold green][OK] Complete![/] {job.total_output_files} file(s) written to:\n"
            f"[bold]{job.output_dir}[/]",
            border_style="green",
        )
        console.print(panel)
    elif job.success and job.has_warnings:
        panel = Panel(
            f"[bold yellow][WARN] Complete with warnings[/]\n"
            + "\n".join(f"  - {w}" for w in job.warnings),
            border_style="yellow",
        )
        console.print(panel)
    else:
        panel = Panel(
            f"[bold red][ERROR] Completed with errors[/]\n"
            + "\n".join(f"  - {e}" for e in job.errors),
            border_style="red",
        )
        console.print(panel)

    # List output files
    if job.extracted_subtitles or job.output_video:
        console.print("\n[bold]Output files:[/]")
        for p in job.extracted_subtitles:
            console.print(f"  [green]>[/] {p.name}")
        if job.output_video:
            console.print(f"  [green]>[/] {job.output_video.name}")
    console.print()
