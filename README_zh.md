# Sub Extractor（字幕提取器）

从视频文件中轻松提取字幕。支持市面主流视频格式、软字幕、图形字幕（PGS/VobSub）以及硬字幕 OCR 识别。

## 功能特性

- **软字幕提取** — 提取视频容器中嵌入的字幕轨道（SRT、ASS、VTT 等）
- **图形字幕提取** — 提取 PGS（蓝光）、VobSub（DVD）、DVB 等位图字幕
- **硬字幕 OCR 识别** — 通过图像识别提取烧录在视频画面中的字幕
- **外部字幕发现** — 自动查找并复制视频旁的同名字幕文件（.srt、.ass、.vtt）
- **清洁视频输出** — 生成去除所有字幕轨道的清洁视频副本
- **格式转换** — 将提取的字幕转换为偏好格式（SRT、ASS、SSA、VTT、SUP、SUB）
- **语言过滤** — 仅提取指定语言的字幕
- **可扩展架构** — 清晰的 Pipeline 设计，轻松添加新格式和新功能
- **图形界面** — 基于 PySide6 的三标签页 GUI，支持进度追踪
- **跨平台** — 支持 Windows、macOS、Linux

## 环境要求

- **Python 3.10+**
- **ffmpeg**（必需 — 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载）
- **OCR 依赖**（可选 — 用于硬字幕提取）

### 安装 ffmpeg

| 平台 | 命令 |
|------|------|
| **Windows** | `winget install ffmpeg` 或 `choco install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Linux (Debian/Ubuntu)** | `sudo apt install ffmpeg` |
| **Linux (Fedora)** | `sudo dnf install ffmpeg` |

### 安装 OCR 依赖（可选）

OCR 功能用于提取烧录在视频画面中的硬字幕（如中文字幕组的压制视频）：

```bash
# 推荐：EasyOCR（安装简单，支持 80+ 种语言）
pip install "sub-extractor[ocr-easyocr]"

# 备选：PaddleOCR（中文识别精度更高，适合批量处理）
pip install "sub-extractor[ocr-paddleocr]"

# 一键安装推荐 OCR 后端
pip install "sub-extractor[ocr]"
```

## 安装

### 仅命令行

```bash
pip install -e .
```

### 含 GUI

```bash
pip install -e ".[gui]"
```

安装后可通过以下方式启动 GUI：

```bash
sub-extractor-gui
# 或
python -m sub_extractor --gui
```

### 含 OCR 支持

```bash
pip install -e ".[gui,ocr]"
```

### 源码安装

```bash
git clone https://github.com/Sub-Extractor/Sub-Extractor.git
cd Sub-Extractor
pip install -e ".[gui,ocr]"
```

### 打包为独立可执行文件（Windows）

构建不需要 Python 环境的单个 `.exe` 文件：

```bash
pip install -e ".[build]"
pyinstaller --clean --noconfirm pyinstaller-gui.spec
```

可执行文件生成在 `dist/SubExtractor.exe`。ffmpeg **不会打包在内** — 用户需单独安装（Check 标签页可检测可用性）。

## 快速开始

```bash
# 检查 ffmpeg 是否可用
sub-extractor check

# 查看视频信息和字幕轨道
sub-extractor info movie.mkv

# 提取所有字幕并生成清洁视频
sub-extractor extract movie.mkv -o ./subtitles

# 仅提取英文字幕，不生成清洁视频
sub-extractor extract movie.mp4 -o ./out --languages eng --no-video

# 提取指定轨道，转换为 ASS 格式
sub-extractor extract movie.mkv -o ./out --tracks 0,2 --sub-format ass

# 提取蓝光 PGS 图形字幕
sub-extractor extract movie.mkv -o ./out --sub-format sup

# OCR 识别硬字幕（烧录字幕）
sub-extractor extract movie.mp4 -o ./out --ocr --ocr-language ch_sim

# 使用 PaddleOCR 引擎，调整帧间隔
sub-extractor extract movie.mkv -o ./out --ocr --ocr-engine paddleocr --ocr-language ch_sim --ocr-interval 0.5

# 预览操作（不实际执行）
sub-extractor extract movie.mkv -o ./out --dry-run
```

## 支持的视频格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| MP4 | `.mp4` | 最通用的视频格式 |
| MKV | `.mkv` | 多轨道容器，字幕支持最好 |
| AVI | `.avi` | 经典 Windows 格式 |
| MOV | `.mov` | Apple QuickTime 格式 |
| WebM | `.webm` | 开源 Web 视频格式 |
| TS | `.ts` | MPEG 传输流（录播视频常用） |
| FLV | `.flv` | Flash 视频格式 |
| WMV | `.wmv` | Windows Media 视频 |
| M4V | `.m4v` | iTunes 视频格式 |
| OGV | `.ogv` | Ogg 视频格式 |

## 支持的字幕类型

### 软字幕（Soft Subtitles）
嵌入在视频容器中的独立字幕流，可以直接提取和转换：
- **文本格式**：SRT、ASS/SSA、WebVTT、mov_text、DVB Subtitle、SAMI 等
- **图形格式**：PGS（蓝光 .sup）、VobSub（DVD .sub/.idx）、XSub

### 外部字幕（External Subtitles）
视频文件旁的同名字幕文件，自动发现并复制：
- `.srt`、`.ass`、`.ssa`、`.vtt`、`.sub`

### 硬字幕（Hardcoded Subtitles）
烧录在视频画面中的字幕，通过 OCR 图像识别提取：
- 支持 EasyOCR（80+ 种语言）和 PaddleOCR 两种引擎
- 可配置帧间隔、置信度阈值、字幕区域

## 输出示例

输入文件 `movie.mkv`，包含英文和中文字幕轨道：

```
subtitles/
├── movie.eng.srt         # 提取的英文字幕
├── movie.chi.srt         # 提取的中文字幕
├── movie.eng.sup         # 提取的英文 PGS 图形字幕
├── movie.ch_sim.ocr.srt  # OCR 识别的硬字幕
└── movie_clean.mkv       # 去除字幕后的清洁视频
```

## 命令参考

### `extract`

```
sub-extractor extract INPUT -o OUTPUT [选项]

选项：
  -o, --output PATH            输出目录 [必需]
  --keep-video / --no-video    是否生成清洁视频（默认：keep）
  --sub-format [srt|ass|ssa|vtt|sup|sub]  字幕输出格式（默认：srt）
  --languages TEXT             逗号分隔的语言代码（如 "eng,chi"）
  --tracks TEXT                逗号分隔的轨道索引（如 "0,2"）
  --no-external                跳过外部字幕文件
  --dry-run                    预览而不执行
  --ocr / --no-ocr             启用 OCR 识别硬字幕
  --ocr-engine [easyocr|paddleocr]  OCR 引擎（默认：easyocr）
  --ocr-language TEXT          OCR 语言代码（如 "ch_sim", "en", "ch_sim+en"）
  --ocr-interval FLOAT         帧分析间隔秒数（默认：1.0）
  --ocr-confidence FLOAT       最低置信度阈值 0.0-1.0（默认：0.7）
  -v, --verbose                启用调试日志
```

### `info`

```
sub-extractor info INPUT

显示：格式、分辨率、时长、音频轨道、字幕轨道、
      视频旁的外部字幕文件。
```

### `check`

```
sub-extractor check

验证：ffmpeg 版本、ffprobe 版本、可选 mkvtoolnix、
      OCR 引擎可用性。
```

## GUI 图形界面

Sub Extractor 包含一个三标签页的图形界面：

- **Extract（提取）** — 完整的字幕提取工作流，包含进度追踪、预览和所有命令行选项
- **Info（信息）** — 查看视频元数据、音频轨道、字幕轨道和外部字幕文件
- **Check（检测）** — 验证 ffmpeg/ffprobe 和 OCR 依赖是否可用

启动 GUI：

```bash
sub-extractor-gui
```

## 架构设计

Sub Extractor 采用**五层 Pipeline 架构**，基于策略模式（Strategy Pattern）设计，具有高度可扩展性：

```
Input → Detection → Extraction → Processing → Output
  ↓         ↓            ↓           ↓          ↓
VideoInfo  Tracks     .srt/.ass   清洁视频   写入磁盘
```

每一层使用抽象基类定义接口，通过注册新的 Handler 类即可扩展功能，**无需修改 Pipeline 核心代码**。

```
sub_extractor/
├── input/             # 文件验证 & ffprobe 探测
│   └── video_input.py
├── detection/         # 软字幕/外部/硬字幕发现
│   ├── soft_sub_detector.py
│   ├── external_sub_detector.py
│   └── hard_sub_detector.py
├── extraction/        # 字幕提取 & 格式转换
│   ├── ffmpeg_extractor.py      # 文本字幕
│   ├── bitmap_extractor.py      # 图形字幕 (PGS/VobSub)
│   └── ocr_extractor.py         # 硬字幕 OCR
├── ocr/               # OCR 管道子包
│   ├── frame_extractor.py       # ffmpeg 帧提取
│   ├── preprocessor.py          # OpenCV 图像预处理
│   ├── engine.py                # OCR 引擎抽象层
│   ├── deduplicator.py          # 相邻帧去重合并
│   ├── timestamp.py             # 时间戳格式化
│   └── formatter.py             # SRT/ASS 输出
├── processing/        # 视频重新封装（去除字幕）
│   └── ffmpeg_remuxer.py
└── output/            # 文件系统输出
    └── file_output.py
```

### OCR 管道详解

硬字幕 OCR 提取的内部流程：

```
视频文件
  │
  ▼
FrameExtractor (ffmpeg pipe 流式提取帧，零磁盘IO)
  │
  ▼
Preprocessor (灰度化 → 自适应阈值 → 降噪 → 字幕区域检测)
  │
  ▼
OCREngine (EasyOCR / PaddleOCR 文本识别)
  │
  ▼
Deduplicator (相邻帧相似文本去重 → 时间范围合并 → 置信度过滤)
  │
  ▼
Formatter (SRT / ASS 格式化输出)
```

## 参考的开源项目

本项目在 OCR 硬字幕提取功能的设计中参考了以下优秀开源项目：

- [VideoSubFinder](https://sourceforge.net/projects/videosubfinder/) — 经典的硬字幕检测工具（C++，Tesseract OCR）
- [video-subtitle-extractor](https://github.com/YaoFANGUK/video-subtitle-extractor) — 基于 PaddleOCR 的视频硬字幕提取（Python）
- [EasyOCR](https://github.com/JaidedAI/EasyOCR) — 支持 80+ 语言的 OCR 库
- [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) — 百度开源 OCR 引擎，中文识别精度领先
- [FFmpeg](https://ffmpeg.org/) — 底层视频处理核心
- [MKVToolNix](https://mkvtoolnix.download/) — MKV 容器高级操作工具

## 路线图

- [x] MP4/MKV 软字幕提取
- [x] 外部字幕文件发现
- [x] 格式转换（SRT/ASS/SSA/VTT）
- [x] 语言过滤
- [x] 图形用户界面（GUI）
- [x] 主流视频格式扩展（AVI/MOV/WebM/TS/FLV/WMV/M4V/OGV）
- [x] 图形字幕支持（PGS/VobSub/DVB/XSub）
- [x] 硬字幕 OCR 提取（EasyOCR + PaddleOCR）
- [ ] 批量处理
- [ ] 字幕同步工具
- [ ] 自动检测视频中是否存在硬字幕
- [ ] GPU 加速 OCR

## 开源协议

MIT License

---

**Sub Extractor v0.2.0** — 一个工具，提取所有字幕。
