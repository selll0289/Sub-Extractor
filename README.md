# Sub Extractor

Extract subtitles from video files with ease. Supports MP4 and MKV containers.

## Features

- **Soft subtitle extraction** — Extract embedded subtitle tracks (SRT, ASS, VTT, etc.) from video containers
- **External subtitle discovery** — Automatically find and copy sidecar subtitle files (.srt, .ass, .vtt)
- **Clean video output** — Produce a clean copy of your video with all subtitle tracks removed
- **Format conversion** — Convert extracted subtitles to your preferred format (SRT, ASS, SSA, VTT)
- **Language filtering** — Extract only subtitles in specific languages
- **Extensible architecture** — Clean pipeline design makes adding new formats and features easy

## Requirements

- **Python 3.10+**
- **ffmpeg** (required — download from [ffmpeg.org](https://ffmpeg.org/download.html))

### Installing ffmpeg

| Platform | Command |
|----------|---------|
| **Windows** | `winget install ffmpeg` or `choco install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Linux (Debian/Ubuntu)** | `sudo apt install ffmpeg` |
| **Linux (Fedora)** | `sudo dnf install ffmpeg` |

## Installation

```bash
pip install -e .
```

Or from source:

```bash
git clone https://github.com/<your-username>/Sub-Extractor.git
cd Sub-Extractor
pip install -e .
```

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

# Preview what will happen without executing
sub-extractor extract movie.mkv -o ./out --dry-run
```

## Output

For an input file `movie.mkv` with English and Chinese subtitle tracks:

```
subtitles/
├── movie.eng.srt       # Extracted English subtitles
├── movie.chi.srt       # Extracted Chinese subtitles
├── movie.jpn.srt       # External subtitle file (if found)
└── movie_clean.mkv     # Video without subtitle tracks
```

## Commands

### `extract`

```
sub-extractor extract INPUT -o OUTPUT [OPTIONS]

Options:
  -o, --output PATH        Output directory [required]
  --keep-video / --no-video  Produce clean video (default: keep)
  --sub-format [srt|ass|ssa|vtt]  Preferred subtitle format (default: srt)
  --languages TEXT         Comma-separated language codes (e.g., "eng,chi")
  --tracks TEXT            Comma-separated track indices (e.g., "0,2")
  --no-external            Skip sidecar subtitle files
  --dry-run                Preview without executing
  -v, --verbose            Enable debug output
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

Verifies: ffmpeg version, ffprobe version, optional mkvtoolnix.
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
├── input/          # File validation & ffprobe probing
├── detection/      # Soft/external/hard subtitle discovery
├── extraction/     # Subtitle demuxing & format conversion
├── processing/     # Video remuxing (subtitle removal)
└── output/         # File system / remote output handlers
```

See the [source code](src/sub_extractor/) for detailed documentation.

## Roadmap

- [x] MP4/MKV soft subtitle extraction
- [x] External subtitle file discovery
- [x] Format conversion (SRT/ASS/SSA/VTT)
- [x] Language filtering
- [ ] Hard (burned-in) subtitle OCR extraction
- [ ] Additional formats: AVI, MOV, WebM, TS
- [ ] Batch processing
- [ ] Graphical user interface (GUI)
- [ ] Subtitle synchronization tools

## License

MIT
