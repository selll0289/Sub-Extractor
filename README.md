# Sub Extractor

Extract subtitles from video files with ease. Supports mainstream video formats, bitmap subtitles (PGS/VobSub), and hardcoded subtitle OCR.

[中文文档 (Chinese README)](README_zh.md)

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Standalone Executable (Windows)](#standalone-executable-windows)
- [User Manual](#user-manual)
  - [Workflow 1: Extract Soft Subtitles](#workflow-1-extract-soft-subtitles)
  - [Workflow 2: Extract Bitmap (PGS/VobSub) Subtitles](#workflow-2-extract-bitmap-pgsvobsub-subtitles)
  - [Workflow 3: OCR Hardcoded Subtitles](#workflow-3-ocr-hardcoded-subtitles)
  - [Workflow 4: Language-Filtered Extraction](#workflow-4-language-filtered-extraction)
  - [Workflow 5: Batch Processing via Script](#workflow-5-batch-processing-via-script)
- [OCR Language Codes Reference](#ocr-language-codes-reference)
- [Supported Video Formats](#supported-video-formats)
- [Supported Subtitle Types](#supported-subtitle-types)
- [Command Reference](#command-reference)
- [GUI](#gui)
- [Output Structure](#output-structure)
- [Architecture](#architecture)
- [Performance Tuning](#performance-tuning)
- [Troubleshooting](#troubleshooting)
- [Reference Projects](#reference-projects)
- [Roadmap](#roadmap)
- [License](#license)

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

- **Python 3.10+** (only if running from source)
- **ffmpeg** (required — download from [ffmpeg.org](https://ffmpeg.org/download.html))

### Installing ffmpeg

| Platform | Command |
|----------|---------|
| **Windows** | `winget install ffmpeg` or `choco install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Linux (Debian/Ubuntu)** | `sudo apt install ffmpeg` |
| **Linux (Fedora)** | `sudo dnf install ffmpeg` |

> **Note:** ffmpeg must be on your system PATH. Verify with `ffmpeg -version`.

## Installation

### CLI Only

```bash
pip install -e .
```

### With GUI

```bash
pip install -e ".[gui]"
```

Launch the GUI:

```bash
sub-extractor-gui
# or
python -m sub_extractor --gui
```

### With OCR Support

```bash
# Recommended: EasyOCR (simple install, 80+ languages)
pip install -e ".[gui,ocr-easyocr]"

# Alternative: PaddleOCR (superior Chinese recognition)
pip install -e ".[gui,ocr-paddleocr]"
```

### From Source

```bash
git clone https://github.com/Sub-Extractor/Sub-Extractor.git
cd Sub-Extractor
pip install -e ".[gui,ocr]"
```

## Quick Start

```bash
# Check if dependencies are available
sub-extractor check

# View video info and subtitle tracks
sub-extractor info movie.mkv

# Extract all subtitles and produce clean video
sub-extractor extract movie.mkv -o ./subtitles

# Extract only English subtitles, no clean video
sub-extractor extract movie.mp4 -o ./out --languages eng --no-video

# Extract specific tracks, convert to ASS format
sub-extractor extract movie.mkv -o ./out --tracks 0,2 --sub-format ass

# OCR extract hardcoded (burned-in) subtitles
sub-extractor extract movie.mp4 -o ./out --ocr --ocr-language ch_sim

# Preview without executing
sub-extractor extract movie.mkv -o ./out --dry-run
```

## Standalone Executable (Windows)

A pre-built standalone `.exe` is available for Windows users. **No Python installation required.**

### Download & Use

1. Download `SubExtractor.exe` from the [Releases page](https://github.com/Sub-Extractor/Sub-Extractor/releases)
2. Install **ffmpeg** separately (required):
   ```powershell
   winget install ffmpeg
   ```
3. Double-click `SubExtractor.exe` to launch the GUI

> **Note:** ffmpeg is NOT bundled in the exe. The **Check** tab verifies if ffmpeg is properly installed.

### Build from Source

To build the exe yourself:

```bash
pip install -e ".[build]"
pyinstaller --clean --noconfirm pyinstaller-gui.spec
# Output: dist/SubExtractor.exe (~100 MB, includes Python + PySide6 + numpy + OpenCV)
```

---

## User Manual

### Workflow 1: Extract Soft Subtitles

**Scenario:** You have an MKV/MP4 file with embedded subtitle tracks (the most common case).

**Steps:**

```bash
# Step 1: Check what's inside the video
sub-extractor info video.mkv
```
Example output shows subtitle tracks with language, codec, and flags.

```bash
# Step 2: Extract all subtitles
sub-extractor extract video.mkv -o ./subtitles
```
This produces:
- `subtitles/video.eng.srt` — English subtitles
- `subtitles/video.chi.srt` — Chinese subtitles  
- `subtitles/video_clean.mkv` — Video without subtitle tracks

```bash
# Step 3 (optional): Extract only specific tracks
sub-extractor extract video.mkv -o ./subtitles --tracks 0,2 --sub-format ass
```

**GUI Method:**  
Select file → Choose output directory → Set format → Click "Extract Subtitles"

---

### Workflow 2: Extract Bitmap (PGS/VobSub) Subtitles

**Scenario:** You have a Blu-ray rip or DVD with PGS or VobSub bitmap subtitles.

**Steps:**

```bash
# Step 1: Check what tracks are available
sub-extractor info bluray_rip.mkv
# Look for codec: "hdmv_pgs_subtitle" (PGS) or "dvd_subtitle" (VobSub)

# Step 2: Extract PGS as .sup file
sub-extractor extract bluray_rip.mkv -o ./subtitles --sub-format sup

# Step 3: Extract VobSub as .sub/.idx pair
sub-extractor extract dvd_rip.mkv -o ./subtitles --sub-format sub
```

> **Note:** Bitmap subtitles cannot be directly converted to text SRT. To get text from bitmap subtitles, use the OCR workflow below.

---

### Workflow 3: OCR Hardcoded Subtitles

**Scenario:** The subtitles are "burned into" the video image (common in fan-subbed anime, Chinese drama rips). There are no separate subtitle tracks.

**Prerequisites:**
```bash
# Install OCR dependencies
pip install "sub-extractor[ocr-easyocr]"
```

**Steps:**

```bash
# Step 1: Verify OCR is available
sub-extractor check
# Should show: "Optional: OCR available (easyocr)"

# Step 2: Run OCR extraction
sub-extractor extract video.mp4 -o ./subtitles --ocr --ocr-language ch_sim -v
```

**Tuning OCR Quality:**

| Parameter | Effect | Recommended |
|-----------|--------|-------------|
| `--ocr-interval` | Smaller = more frames = more accurate timing but slower | 0.5–2.0 seconds |
| `--ocr-confidence` | Higher = stricter filtering = fewer false positives | 0.6–0.8 |
| `--ocr-language` | Match the subtitle language | `ch_sim` (Simplified Chinese), `en` (English), `ja` (Japanese) |

```bash
# High-quality extraction (slower but more accurate)
sub-extractor extract video.mp4 -o ./subtitles --ocr --ocr-language ch_sim \
    --ocr-interval 0.5 --ocr-confidence 0.8 -v

# Fast preview scan (quick check of what OCR can find)
sub-extractor extract video.mp4 -o ./subtitles --ocr --ocr-language ch_sim \
    --ocr-interval 5.0 --ocr-confidence 0.5 --no-video
```

**OCR Processing Time Estimates (CPU, EasyOCR):**

| Video Length | Interval | Frames | Estimated Time |
|-------------|----------|--------|----------------|
| 30 min | 1.0s | ~1,800 | 2–5 minutes |
| 1 hour | 1.0s | ~3,600 | 5–10 minutes |
| 2 hours | 1.0s | ~7,200 | 10–20 minutes |
| 2 hours | 0.5s | ~14,400 | 20–40 minutes |

> **Tip:** Use `--dry-run` first to check video info without running OCR.

---

### Workflow 4: Language-Filtered Extraction

**Scenario:** A multi-language video (e.g., anime with Japanese, English, Chinese subs) — extract only what you need.

```bash
# Extract only English and Chinese soft subs
sub-extractor extract anime.mkv -o ./out --languages eng,chi

# Combine with OCR for hardcoded Chinese subs
sub-extractor extract anime.mkv -o ./out --languages eng --ocr --ocr-language ch_sim
```

**Common Language Codes:**

| Language | ISO 639-2 Code |
|----------|---------------|
| English | `eng` |
| Chinese | `chi` |
| Japanese | `jpn` |
| Korean | `kor` |
| French | `fre` |
| German | `ger` |
| Spanish | `spa` |
| Russian | `rus` |
| Arabic | `ara` |

---

### Workflow 5: Batch Processing via Script

**Scenario:** Process multiple video files in a folder.

**Windows PowerShell:**
```powershell
Get-ChildItem *.mkv | ForEach-Object {
    sub-extractor extract $_ -o ".\subtitles\$($_.BaseName)" --no-video
}
```

**Linux/macOS Bash:**
```bash
for f in *.mkv; do
    sub-extractor extract "$f" -o "./subtitles/$(basename "$f" .mkv)" --no-video
done
```

**With OCR:**
```bash
for f in *.mp4; do
    sub-extractor extract "$f" -o "./subtitles/$(basename "$f" .mp4)" --ocr --ocr-language ch_sim --no-video
done
```

---

## OCR Language Codes Reference

### EasyOCR Language Codes

| Language | Code |
|----------|------|
| Simplified Chinese | `ch_sim` |
| Traditional Chinese | `ch_tra` |
| English | `en` |
| Japanese | `ja` |
| Korean | `ko` |
| French | `fr` |
| German | `de` |
| Spanish | `es` |
| Portuguese | `pt` |
| Italian | `it` |
| Russian | `ru` |
| Arabic | `ar` |
| Thai | `th` |
| Vietnamese | `vi` |
| Multiple languages | `ch_sim+en` (combined with `+`) |

### PaddleOCR Language Codes

| Language | Code |
|----------|------|
| Simplified Chinese | `ch` |
| English | `en` |
| French | `fr` |
| German | `german` |
| Japanese | `japan` |
| Korean | `korean` |

---

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

### Soft Subtitles (Embedded)
- **Text formats**: SRT, ASS/SSA, WebVTT, mov_text, DVB Subtitle, SAMI, etc.
- **Bitmap formats**: PGS (Blu-ray .sup), VobSub (DVD .sub/.idx), XSub

### External Subtitles (Sidecar Files)
- `.srt`, `.ass`, `.ssa`, `.vtt`, `.sub`

### Hardcoded Subtitles (OCR)
- Burned into the video image, extracted via EasyOCR or PaddleOCR
- Configurable frame interval, confidence threshold, subtitle region

## Command Reference

### `extract` — Extract subtitles from a video

```
sub-extractor extract INPUT -o OUTPUT [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output PATH` | Output directory | **Required** |
| `--keep-video / --no-video` | Produce clean video copy | `--keep-video` |
| `--sub-format FMT` | Output format: `srt`, `ass`, `ssa`, `vtt`, `sup`, `sub` | `srt` |
| `--languages TEXT` | Comma-separated language codes (e.g., `eng,chi`) | All languages |
| `--tracks TEXT` | Comma-separated track indices (e.g., `0,2`) | All tracks |
| `--no-external` | Skip sidecar subtitle files | Include |
| `--dry-run` | Preview without writing files | Off |
| `--ocr / --no-ocr` | Enable hardcoded subtitle OCR | `--no-ocr` |
| `--ocr-engine ENGINE` | `easyocr` or `paddleocr` | `easyocr` |
| `--ocr-language TEXT` | OCR language code | `ch_sim` |
| `--ocr-interval FLOAT` | Seconds between analyzed frames | `1.0` |
| `--ocr-confidence FLOAT` | Minimum confidence (0.0–1.0) | `0.7` |
| `-v, --verbose` | Enable debug logging | Off |

### `info` — Show video information

```
sub-extractor info INPUT
```

Displays: container format, video codec, resolution, duration, bit rate, audio tracks, subtitle tracks, and external subtitle files.

### `check` — Verify system dependencies

```
sub-extractor check
```

Checks: ffmpeg, ffprobe, mkvtoolnix (optional), OCR engines (optional).

## GUI

Sub Extractor includes a PySide6 graphical interface with three tabs:

### Extract Tab
Full extraction workflow with:
- File picker (supports all 10 video formats)
- Output directory picker
- Subtitle format selector (SRT/ASS/SSA/VTT/SUP/SUB)
- Language and track filtering
- **OCR settings panel:**
  - Enable/disable OCR checkbox
  - Engine selector (EasyOCR / PaddleOCR)
  - Language code input
  - Frame interval selector (0.5s – 5.0s)
  - Confidence threshold selector (0.5 – 0.9)
  - Subtitle region selector (bottom / top / full)
- Keep video / include external / dry run checkboxes
- Progress bar with status updates
- Results table showing all output files with warnings/errors log

### Info Tab
- Load video metadata on a background thread (UI stays responsive)
- Video information: file, format, codec, resolution, duration, bit rate
- Audio tracks table: index, codec, language, channels, title
- Embedded subtitle tracks table: index, codec, language, flags, title
- External subtitle files table: codec, language, filename

### Check Tab
- Auto-runs on tab activation
- Dependency status table: ffmpeg, ffprobe, mkvtoolnix, OCR engines
- Installation instructions shown when dependencies are missing
- Re-run button for re-checking after installing dependencies

Launch:
```bash
sub-extractor-gui
```

## Output Structure

For a video `movie.mkv` with multiple subtitle sources:

```
subtitles/
├── movie.eng.srt          # Extracted English soft subtitle
├── movie.chi.srt          # Extracted Chinese soft subtitle
├── movie.eng.sup          # Extracted English PGS bitmap subtitle
├── movie.ch_sim.ocr.srt   # OCR-extracted hardcoded Chinese subtitle
├── movie_clean.mkv        # Video with all subtitle tracks removed
└── (external .srt/.ass)   # Copied sidecar files (if found)
```

## Architecture

Sub Extractor uses a **five-layer pipeline architecture** with the **Strategy pattern**:

```
Input → Detection → Extraction → Processing → Output
  ↓         ↓            ↓           ↓          ↓
VideoInfo  Tracks     .srt/.ass   Clean video   Write to disk
```

Adding support for a new format or subtitle type requires only writing a new handler class — zero changes to the pipeline core.

```
sub_extractor/
├── input/             # File validation & ffprobe probing
├── detection/         # Soft/external/hard subtitle discovery
│   ├── soft_sub_detector.py       # Embedded track detection
│   ├── external_sub_detector.py   # Sidecar file discovery
│   └── hard_sub_detector.py       # OCR trigger track
├── extraction/        # Subtitle demuxing & conversion
│   ├── ffmpeg_extractor.py        # Text subtitle extraction
│   ├── bitmap_extractor.py        # PGS/VobSub/DVB extraction
│   └── ocr_extractor.py           # Hardcoded subtitle OCR
├── ocr/               # OCR pipeline sub-package
│   ├── frame_extractor.py         # ffmpeg pipe frame streaming
│   ├── preprocessor.py            # OpenCV image preprocessing
│   ├── engine.py                  # OCR engine abstraction layer
│   ├── deduplicator.py            # Inter-frame text dedup & merge
│   ├── timestamp.py               # SRT/ASS time formatting
│   └── formatter.py               # SRT/ASS file generation
├── processing/        # Video remuxing (subtitle removal)
└── output/            # File system output handler
```

### OCR Pipeline Detail

```
Video file → FrameExtractor → Preprocessor → OCREngine → Deduplicator → Formatter
                ↓                ↓              ↓            ↓              ↓
           ffmpeg pipe     grayscale       EasyOCR/     merge similar   .srt/.ass
           zero disk I/O   threshold       PaddleOCR    frames across   file output
                           denoise                      time ranges
                           region detect                confidence filter
```

The OCR pipeline uses constant memory (generator pattern) — a video of any length can be processed without loading all frames into RAM.

## Performance Tuning

### OCR Speed vs. Accuracy

| Setting | Fast | Balanced | Accurate |
|---------|------|----------|----------|
| `--ocr-interval` | 5.0s | 1.0s | 0.5s |
| `--ocr-confidence` | 0.5 | 0.7 | 0.8 |
| Processing time (2h video) | ~5 min | ~15 min | ~30 min |

### Memory Usage
- OCR extraction uses a streaming pipeline (generator pattern)
- Each frame is processed and discarded before the next one arrives
- Memory usage is constant regardless of video length (~200-500 MB for OCR models + one frame buffer)

### GPU Acceleration
- EasyOCR: Set `gpu=True` (auto-detected, falls back to CPU gracefully)
- PaddleOCR: Install GPU version of PaddlePaddle
- GPU can provide 3-5x speedup for OCR processing

## Troubleshooting

### ffmpeg not found

```
Error: ffmpeg/ffprobe not found.
```

**Fix:** Install ffmpeg and ensure it's on your PATH.
- Windows: `winget install ffmpeg` → restart terminal
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`
- Verify: `ffmpeg -version`

### OCR dependencies missing

```
Error: OCR engine 'easyocr' is not available.
```

**Fix:**
```bash
pip install "sub-extractor[ocr-easyocr]"
# First run will download models (~100-500 MB, cached for future use)
```

### "No subtitles found"

- The video may not have embedded subtitle tracks
- Try `--ocr` if subtitles are burned into the video
- Check with `sub-extractor info video.mkv` to see available tracks

### OCR results are poor quality

- **Wrong language**: Ensure `--ocr-language` matches the subtitle language
- **Subtitle region**: Try `bottom`, `top`, or `full` (via GUI or config)
- **Frame interval**: Decrease `--ocr-interval` to 0.5 for better timing
- **Confidence**: Lower `--ocr-confidence` to 0.5 to catch more text (may include noise)
- **Subtitle style**: Highly stylized subs (colored outlines, unusual fonts) are harder to OCR

### File format not supported

```
Error: Unsupported format '.xxx'
```

- The file extension is not recognized. Supported: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.ts`, `.flv`, `.wmv`, `.m4v`, `.ogv`
- If the video plays in a media player, try remuxing it to MKV first:
  ```bash
  ffmpeg -i video.xxx -c copy video.mkv
  ```

### Empty output files

- The subtitle track may be empty or corrupted
- For bitmap subtitles: the track may require OCR (use `--ocr`)
- For OCR: try lowering `--ocr-confidence` to 0.5

## Reference Projects

Sub Extractor's design references these excellent open-source projects:

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
- [x] Standalone Windows executable
- [x] Mainstream format expansion (AVI/MOV/WebM/TS/FLV/WMV/M4V/OGV)
- [x] Bitmap subtitle support (PGS/VobSub/DVB/XSub)
- [x] Hardcoded subtitle OCR (EasyOCR + PaddleOCR)
- [ ] Batch processing (built-in multi-file queue)
- [ ] Subtitle synchronization tools (shift, stretch)
- [ ] Auto-detect hard-sub presence before full OCR
- [ ] GPU-accelerated OCR with progress feedback
- [ ] Subtitle edit/preview panel in GUI
- [ ] macOS/Linux standalone builds

## License

MIT License — see [LICENSE](LICENSE) file for details.
