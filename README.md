# Sub Extractor

Extract subtitles from video files with ease. Supports mainstream video formats, bitmap subtitles (PGS/VobSub), and hardcoded subtitle OCR.

## Features

- **Soft subtitle extraction** — Extract embedded subtitle tracks (SRT, ASS, VTT, etc.) from video containers
- **Bitmap subtitle extraction** — Extract PGS (Blu-ray), VobSub (DVD), DVB, and XSub bitmap subtitles
- **Hardcoded subtitle OCR** — Extract burned-in subtitles via AI-powered image recognition (EasyOCR / PaddleOCR)
- **External subtitle discovery** — Automatically find and copy sidecar subtitle files (.srt, .ass, .vtt)
- **Clean video output** — Produce a clean copy of your video with all subtitle tracks removed
- **Format conversion** — Convert extracted subtitles to your preferred format (SRT, ASS, SSA, VTT, SUP, SUB)
- **Language filtering** — Extract only subtitles in specific languages
- **Extensible architecture** — Clean pipeline design makes adding new formats and features easy
- **Graphical Interface** — PySide6-based GUI with progress tracking and three tabs
- **Cross-platform** — Works on Windows, macOS, Linux

## Requirements

- **Python 3.10+**
- **ffmpeg** (required — download from [ffmpeg.org](https://ffmpeg.org/download.html))
- **OCR dependencies** (optional — for hardcoded subtitle extraction)

### Installing ffmpeg

| Platform | Command |
|----------|---------|
| **Windows** | `winget install ffmpeg` or `choco install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Linux (Debian/Ubuntu)** | `sudo apt install ffmpeg` |
| **Linux (Fedora)** | `sudo dnf install ffmpeg` |

### Installing OCR Dependencies (Optional)

OCR enables extracting subtitles burned into the video image:

```bash
# Recommended: EasyOCR (simple install, 80+ languages)
pip install "sub-extractor[ocr-easyocr]"

# Alternative: PaddleOCR (superior Chinese recognition, faster batch)
pip install "sub-extractor[ocr-paddleocr]"

# One-click install recommended OCR backend
pip install "sub-extractor[ocr]"
```

## Installation

### CLI Only

```bash
pip install -e .
```

### With GUI

```bash
pip install -e ".[gui]"
```

This installs PySide6 alongside the CLI tool. You can then launch the GUI with:

```bash
sub-extractor-gui
# or
python -m sub_extractor --gui
```

### With OCR Support

```bash
pip install -e ".[gui,ocr]"
```

### From Source

```bash
git clone https://github.com/Sub-Extractor/Sub-Extractor.git
cd Sub-Extractor
pip install -e ".[gui,ocr]"
```

### Standalone Executable (Windows)

Build a single `.exe` file that runs without Python installed:

```bash
pip install -e ".[build]"
pyinstaller --clean --noconfirm pyinstaller-gui.spec
```

The executable will be at `dist/SubExtractor.exe`. ffmpeg is **not bundled** — users must install it separately (the Check tab verifies availability).

## Quick Start

```bash
# Check if ffmpeg is available
sub-extractor check

# View video info and subtitle tracks
sub-extractor info movie.mkv

# Extract all subtitles and produce clean video
sub-extractor extract movie.mkv -o ./subtitles

# Extract only English subtitles, no clean video
sub-extractor extract movie.mp4 -o ./out --languages eng --no-video

# Extract specific tracks, convert to ASS format
sub-extractor extract movie.mkv -o ./out --tracks 0,2 --sub-format ass

# Extract Blu-ray PGS bitmap subtitles
sub-extractor extract movie.mkv -o ./out --sub-format sup

# OCR extract hardcoded (burned-in) subtitles
sub-extractor extract movie.mp4 -o ./out --ocr --ocr-language ch_sim

# Use PaddleOCR engine with custom frame interval
sub-extractor extract movie.mkv -o ./out --ocr --ocr-engine paddleocr --ocr-language ch_sim --ocr-interval 0.5

# Preview what will happen without executing
sub-extractor extract movie.mkv -o ./out --dry-run
```

## Supported Video Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| MP4 | `.mp4` | Most universal format |
| MKV | `.mkv` | Best subtitle support, multi-track |
| AVI | `.avi` | Classic Windows format |
| MOV | `.mov` | Apple QuickTime format |
| WebM | `.webm` | Open web video format |
| TS | `.ts` | MPEG transport stream (recordings) |
| FLV | `.flv` | Flash video format |
| WMV | `.wmv` | Windows Media Video |
| M4V | `.m4v` | iTunes video format |
| OGV | `.ogv` | Ogg video format |

## Supported Subtitle Types

### Soft Subtitles
Embedded subtitle streams in the video container:
- **Text formats**: SRT, ASS/SSA, WebVTT, mov_text, DVB Subtitle, SAMI, etc.
- **Bitmap formats**: PGS (Blu-ray .sup), VobSub (DVD .sub/.idx), XSub

### External Subtitles
Sidecar subtitle files next to the video:
- `.srt`, `.ass`, `.ssa`, `.vtt`, `.sub`

### Hardcoded Subtitles
Burned into the video image, extracted via OCR:
- EasyOCR (80+ languages) and PaddleOCR engines
- Configurable frame interval, confidence threshold, subtitle region

## Output

For an input file `movie.mkv` with English and Chinese subtitle tracks:

```
subtitles/
├── movie.eng.srt         # Extracted English subtitles
├── movie.chi.srt         # Extracted Chinese subtitles
├── movie.eng.sup         # Extracted English PGS bitmap subtitles
├── movie.ch_sim.ocr.srt  # OCR-extracted hardcoded subtitles
└── movie_clean.mkv       # Video without subtitle tracks
```

## Commands

### `extract`

```
sub-extractor extract INPUT -o OUTPUT [OPTIONS]

Options:
  -o, --output PATH             Output directory [required]
  --keep-video / --no-video     Produce clean video (default: keep)
  --sub-format [srt|ass|ssa|vtt|sup|sub]  Preferred subtitle format (default: srt)
  --languages TEXT              Comma-separated language codes (e.g., "eng,chi")
  --tracks TEXT                 Comma-separated track indices (e.g., "0,2")
  --no-external                 Skip sidecar subtitle files
  --dry-run                     Preview without executing
  --ocr / --no-ocr              Enable OCR for hardcoded (burned-in) subtitles
  --ocr-engine [easyocr|paddleocr]  OCR engine (default: easyocr)
  --ocr-language TEXT           OCR language code (e.g., "ch_sim", "en")
  --ocr-interval FLOAT          Seconds between analyzed frames (default: 1.0)
  --ocr-confidence FLOAT        Minimum OCR confidence 0.0-1.0 (default: 0.7)
  -v, --verbose                 Enable debug output
```

### `info`

```
sub-extractor info INPUT

Shows: format, resolution, duration, audio tracks, subtitle tracks,
       external subtitle files found alongside the video.
```

### `check`

```
sub-extractor check

Verifies: ffmpeg version, ffprobe version, optional mkvtoolnix,
          OCR engine availability.
```

## GUI

Sub Extractor includes a graphical interface with three tabs:

- **Extract** — Full extraction workflow with progress tracking, dry-run preview, and all CLI options including OCR settings
- **Info** — View video metadata, audio tracks, subtitle tracks, and external subtitle files
- **Check** — Verify that ffmpeg, ffprobe, mkvtoolnix, and OCR engines are available

Launch the GUI:

```bash
sub-extractor-gui
```

## Architecture

Sub Extractor uses a **five-layer pipeline architecture** designed for extensibility:

```
Input → Detection → Extraction → Processing → Output
  ↓         ↓            ↓           ↓          ↓
VideoInfo  Tracks     .srt/.ass   Clean video   Write to disk
```

Each layer uses the **Strategy pattern** with abstract base classes. Adding support for a new video format, subtitle type, or output destination requires only writing a new handler class — no changes to existing code.

```
sub_extractor/
├── input/             # File validation & ffprobe probing
├── detection/         # Soft/external/hard subtitle discovery
├── extraction/        # Subtitle demuxing & format conversion
│   ├── ffmpeg_extractor.py   # Text subtitles
│   ├── bitmap_extractor.py   # Bitmap (PGS/VobSub) subtitles
│   └── ocr_extractor.py      # Hardcoded subtitle OCR
├── ocr/               # OCR pipeline sub-package
│   ├── frame_extractor.py    # ffmpeg frame extraction
│   ├── preprocessor.py       # OpenCV image preprocessing
│   ├── engine.py             # OCR engine abstraction
│   ├── deduplicator.py       # Inter-frame deduplication
│   ├── timestamp.py          # Timestamp formatting
│   └── formatter.py          # SRT/ASS output
├── processing/        # Video remuxing (subtitle removal)
└── output/            # File system / remote output handlers
```

### OCR Pipeline Detail

The hardcoded subtitle OCR flow:

```
Video file
  │
  ▼
FrameExtractor (ffmpeg pipe streaming, zero disk I/O)
  │
  ▼
Preprocessor (grayscale → adaptive threshold → denoise → region detection)
  │
  ▼
OCREngine (EasyOCR / PaddleOCR text recognition)
  │
  ▼
Deduplicator (merge similar text across frames → time ranges → confidence filter)
  │
  ▼
Formatter (SRT / ASS output)
```

## Reference Projects

The OCR hard-sub extraction design references these excellent open-source projects:

- [VideoSubFinder](https://sourceforge.net/projects/videosubfinder/) — Classic hard-sub detection tool (C++, Tesseract OCR)
- [video-subtitle-extractor](https://github.com/YaoFANGUK/video-subtitle-extractor) — PaddleOCR-based video hard-sub extractor (Python)
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — 80+ language OCR library
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — Baidu's OCR engine, state-of-the-art Chinese recognition
- [FFmpeg](https://ffmpeg.org/) — Core video processing engine
- [MKVToolNix](https://mkvtoolnix.download/) — Advanced MKV container tools

## Roadmap

- [x] MP4/MKV soft subtitle extraction
- [x] External subtitle file discovery
- [x] Format conversion (SRT/ASS/SSA/VTT)
- [x] Language filtering
- [x] Graphical user interface (GUI)
- [x] Mainstream format expansion (AVI/MOV/WebM/TS/FLV/WMV/M4V/OGV)
- [x] Bitmap subtitle support (PGS/VobSub/DVB/XSub)
- [x] Hardcoded subtitle OCR (EasyOCR + PaddleOCR)
- [ ] Batch processing
- [ ] Subtitle synchronization tools
- [ ] Auto-detect hard-sub presence in video
- [ ] GPU-accelerated OCR

## License

MIT
