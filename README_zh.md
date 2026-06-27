# Sub Extractor（字幕提取器）

从视频文件中轻松提取字幕。支持市面主流视频格式、图形字幕（PGS/VobSub）、硬字幕 OCR 识别。

[English README](README.md)

## 目录

- [功能特性](#功能特性)
- [环境要求](#环境要求)
- [安装](#安装)
- [快速开始](#快速开始)
- [Windows 独立可执行文件](#windows-独立可执行文件)
- [用户操作手册](#用户操作手册)
  - [场景一：提取软字幕](#场景一提取软字幕)
  - [场景二：提取图形字幕 PGSVobSub](#场景二提取图形字幕-pgsvobsub)
  - [场景三：OCR 识别硬字幕](#场景三ocr-识别硬字幕烧录字幕)
  - [场景四：按语言过滤提取](#场景四按语言过滤提取)
  - [场景五：批量脚本处理](#场景五批量脚本处理)
- [OCR 语言代码参考](#ocr-语言代码参考)
- [支持的视频格式](#支持的视频格式)
- [支持的字幕类型](#支持的字幕类型)
- [命令参考](#命令参考)
- [GUI 图形界面](#gui-图形界面)
- [输出结构](#输出结构)
- [架构设计](#架构设计)
- [性能调优](#性能调优)
- [常见问题排查](#常见问题排查)
- [参考的开源项目](#参考的开源项目)
- [路线图](#路线图)
- [开源协议](#开源协议)

## 功能特性

- **软字幕提取** — 提取视频容器中嵌入的字幕轨道（SRT、ASS、VTT 等）
- **图形字幕提取** — 提取 PGS（蓝光）、VobSub（DVD）、DVB、XSub 等位图字幕
- **硬字幕 OCR 识别** — 通过 AI 图像识别提取烧录在视频画面中的字幕（EasyOCR / PaddleOCR）
- **外部字幕发现** — 自动查找并复制视频旁的同名字幕文件（.srt、.ass、.vtt）
- **清洁视频输出** — 生成去除所有字幕轨道的清洁视频副本
- **格式转换** — 将提取的字幕转换为偏好格式（SRT、ASS、SSA、VTT、SUP、SUB）
- **语言过滤** — 仅提取指定语言的字幕
- **可扩展架构** — 清晰的 Pipeline 设计，轻松添加新格式和新功能
- **图形界面** — 基于 PySide6 的三标签页 GUI，支持进度追踪
- **跨平台** — 支持 Windows、macOS、Linux

## 环境要求

- **Python 3.10+**（仅源码运行需要）
- **ffmpeg**（必需 — 从 [ffmpeg.org](https://ffmpeg.org/download.html) 下载）

### 安装 ffmpeg

| 平台 | 命令 |
|------|------|
| **Windows** | `winget install ffmpeg` 或 `choco install ffmpeg` |
| **macOS** | `brew install ffmpeg` |
| **Linux (Debian/Ubuntu)** | `sudo apt install ffmpeg` |
| **Linux (Fedora)** | `sudo dnf install ffmpeg` |

> **注意：** ffmpeg 必须在系统 PATH 中。用 `ffmpeg -version` 验证安装。

### 安装 OCR 依赖（可选）

OCR 功能用于提取烧录在视频画面中的硬字幕：

```bash
# 推荐：EasyOCR（安装简单，支持 80+ 种语言）
pip install -e ".[gui,ocr-easyocr]"

# 备选：PaddleOCR（中文识别精度更高）
pip install -e ".[gui,ocr-paddleocr]"
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

启动 GUI：

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

## 快速开始

```bash
# 检查依赖是否可用
sub-extractor check

# 查看视频信息和字幕轨道
sub-extractor info movie.mkv

# 提取所有字幕并生成清洁视频
sub-extractor extract movie.mkv -o ./subtitles

# 仅提取英文字幕，不生成清洁视频
sub-extractor extract movie.mp4 -o ./out --languages eng --no-video

# 提取指定轨道，转换为 ASS 格式
sub-extractor extract movie.mkv -o ./out --tracks 0,2 --sub-format ass

# OCR 识别硬字幕（烧录字幕）
sub-extractor extract movie.mp4 -o ./out --ocr --ocr-language ch_sim

# 预览而不执行
sub-extractor extract movie.mkv -o ./out --dry-run
```

## Windows 独立可执行文件

为 Windows 用户提供预构建的独立 `.exe` 文件。**无需安装 Python。**

### 下载使用

1. 从 [Releases 页面](https://github.com/Sub-Extractor/Sub-Extractor/releases) 下载 `SubExtractor.exe`
2. 单独安装 **ffmpeg**（必需）：
   ```powershell
   winget install ffmpeg
   ```
3. 双击 `SubExtractor.exe` 启动 GUI

> **注意：** ffmpeg 不打包在 exe 中。使用 **Check（检测）** 标签页验证 ffmpeg 是否安装正确。

### 自行构建

```bash
pip install -e ".[build]"
pyinstaller --clean --noconfirm pyinstaller-gui.spec
# 输出：dist/SubExtractor.exe（约 100 MB，包含 Python + PySide6 + numpy + OpenCV）
```

---

## 用户操作手册

### 场景一：提取软字幕

**适用情况：** MKV/MP4 文件中包含嵌入的字幕轨道（最常见的情况）。

**操作步骤：**

```bash
# 第一步：查看视频内含有什么
sub-extractor info video.mkv
```
示例输出会显示字幕轨道及其语言、编码格式和标记信息。

```bash
# 第二步：提取全部字幕
sub-extractor extract video.mkv -o ./subtitles
```
生成文件：
- `subtitles/video.eng.srt` — 英文字幕
- `subtitles/video.chi.srt` — 中文字幕
- `subtitles/video_clean.mkv` — 去除字幕后的清洁视频

```bash
# 第三步（可选）：仅提取指定轨道
sub-extractor extract video.mkv -o ./subtitles --tracks 0,2 --sub-format ass
```

**GUI 操作：**  
选择文件 → 选择输出目录 → 设置格式 → 点击「Extract Subtitles」

---

### 场景二：提取图形字幕（PGS/VobSub）

**适用情况：** 蓝光原盘或 DVD 中的 PGS 或 VobSub 位图字幕。

**操作步骤：**

```bash
# 第一步：查看有哪些字幕轨道
sub-extractor info bluray_rip.mkv
# 查看 codec 字段：hdmv_pgs_subtitle（PGS）或 dvd_subtitle（VobSub）

# 第二步：提取 PGS 为 .sup 文件
sub-extractor extract bluray_rip.mkv -o ./subtitles --sub-format sup

# 第三步：提取 VobSub 为 .sub/.idx 对
sub-extractor extract dvd_rip.mkv -o ./subtitles --sub-format sub
```

> **注意：** 位图字幕不能直接转为文本 SRT。如需文本，请使用下面的 OCR 流程。

---

### 场景三：OCR 识别硬字幕（烧录字幕）

**适用情况：** 字幕直接"烧录"在视频画面中（常见于字幕组压制视频、电视剧录制版）。没有独立的字幕轨道。

**准备工作：**
```bash
# 安装 OCR 依赖
pip install "sub-extractor[ocr-easyocr]"
```

**操作步骤：**

```bash
# 第一步：确认 OCR 可用
sub-extractor check
# 应显示：「Optional: OCR available (easyocr)」

# 第二步：运行 OCR 提取
sub-extractor extract video.mp4 -o ./subtitles --ocr --ocr-language ch_sim -v
```

**OCR 质量调优：**

| 参数 | 作用 | 推荐值 |
|------|------|--------|
| `--ocr-interval` | 越小 = 帧越多 = 时间轴越准但越慢 | 0.5–2.0 秒 |
| `--ocr-confidence` | 越高 = 过滤越严格 = 越少误识别 | 0.6–0.8 |
| `--ocr-language` | 匹配字幕语言 | `ch_sim`（简体中文）、`en`（英文）、`ja`（日文） |

```bash
# 高质量提取（较慢但准确）
sub-extractor extract video.mp4 -o ./subtitles --ocr --ocr-language ch_sim \
    --ocr-interval 0.5 --ocr-confidence 0.8 -v

# 快速预览扫描（快速查看 OCR 能识别到什么）
sub-extractor extract video.mp4 -o ./subtitles --ocr --ocr-language ch_sim \
    --ocr-interval 5.0 --ocr-confidence 0.5 --no-video
```

**OCR 处理时间估算（CPU 模式，EasyOCR）：**

| 视频时长 | 帧间隔 | 帧数 | 预计时间 |
|----------|--------|------|----------|
| 30 分钟 | 1.0s | ~1,800 | 2–5 分钟 |
| 1 小时 | 1.0s | ~3,600 | 5–10 分钟 |
| 2 小时 | 1.0s | ~7,200 | 10–20 分钟 |
| 2 小时 | 0.5s | ~14,400 | 20–40 分钟 |

> **提示：** 先用 `--dry-run` 查看视频信息，不实际运行 OCR。

---

### 场景四：按语言过滤提取

**适用情况：** 多语言视频（如动漫含日/英/中多语字幕），仅提取需要的语言。

```bash
# 仅提取英文和中文软字幕
sub-extractor extract anime.mkv -o ./out --languages eng,chi

# 结合 OCR 提取中文硬字幕
sub-extractor extract anime.mkv -o ./out --languages eng --ocr --ocr-language ch_sim
```

**常用语言代码：**

| 语言 | ISO 639-2 代码 |
|------|---------------|
| 英语 | `eng` |
| 中文 | `chi` |
| 日语 | `jpn` |
| 韩语 | `kor` |
| 法语 | `fre` |
| 德语 | `ger` |
| 西班牙语 | `spa` |
| 俄语 | `rus` |
| 阿拉伯语 | `ara` |

---

### 场景五：批量脚本处理

**适用情况：** 处理文件夹中的多个视频文件。

**Windows PowerShell：**
```powershell
Get-ChildItem *.mkv | ForEach-Object {
    sub-extractor extract $_ -o ".\subtitles\$($_.BaseName)" --no-video
}
```

**Linux/macOS Bash：**
```bash
for f in *.mkv; do
    sub-extractor extract "$f" -o "./subtitles/$(basename "$f" .mkv)" --no-video
done
```

**含 OCR 批量处理：**
```bash
for f in *.mp4; do
    sub-extractor extract "$f" -o "./subtitles/$(basename "$f" .mp4)" --ocr --ocr-language ch_sim --no-video
done
```

---

## OCR 语言代码参考

### EasyOCR 语言代码

| 语言 | 代码 |
|------|------|
| 简体中文 | `ch_sim` |
| 繁体中文 | `ch_tra` |
| 英语 | `en` |
| 日语 | `ja` |
| 韩语 | `ko` |
| 法语 | `fr` |
| 德语 | `de` |
| 西班牙语 | `es` |
| 葡萄牙语 | `pt` |
| 意大利语 | `it` |
| 俄语 | `ru` |
| 阿拉伯语 | `ar` |
| 泰语 | `th` |
| 越南语 | `vi` |
| 多语言混合 | `ch_sim+en`（用 `+` 组合） |

### PaddleOCR 语言代码

| 语言 | 代码 |
|------|------|
| 简体中文 | `ch` |
| 英语 | `en` |
| 法语 | `fr` |
| 德语 | `german` |
| 日语 | `japan` |
| 韩语 | `korean` |

---

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

### 软字幕（内嵌轨道）
- **文本格式**：SRT、ASS/SSA、WebVTT、mov_text、DVB Subtitle、SAMI 等
- **位图格式**：PGS（蓝光 .sup）、VobSub（DVD .sub/.idx）、XSub

### 外部字幕（同名字幕文件）
- `.srt`、`.ass`、`.ssa`、`.vtt`、`.sub`

### 硬字幕（烧录字幕 — OCR 识别）
- 烧录在视频画面中，通过 EasyOCR 或 PaddleOCR 提取
- 可配置帧间隔、置信度阈值、字幕区域

## 命令参考

### `extract` — 从视频提取字幕

```
sub-extractor extract INPUT -o OUTPUT [选项]
```

| 选项 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output PATH` | 输出目录 | **必需** |
| `--keep-video / --no-video` | 是否生成清洁视频 | `--keep-video` |
| `--sub-format FMT` | 输出格式：`srt`、`ass`、`ssa`、`vtt`、`sup`、`sub` | `srt` |
| `--languages TEXT` | 逗号分隔语言代码（如 `eng,chi`） | 全部语言 |
| `--tracks TEXT` | 逗号分隔轨道索引（如 `0,2`） | 全部轨道 |
| `--no-external` | 跳过外部字幕文件 | 包含 |
| `--dry-run` | 预览而不写入文件 | 关 |
| `--ocr / --no-ocr` | 启用 OCR 识别硬字幕 | `--no-ocr` |
| `--ocr-engine ENGINE` | OCR 引擎：`easyocr` 或 `paddleocr` | `easyocr` |
| `--ocr-language TEXT` | OCR 语言代码 | `ch_sim` |
| `--ocr-interval FLOAT` | 帧分析间隔秒数 | `1.0` |
| `--ocr-confidence FLOAT` | 最低置信度（0.0–1.0） | `0.7` |
| `-v, --verbose` | 启用调试日志 | 关 |

### `info` — 查看视频信息

```
sub-extractor info INPUT
```

显示：容器格式、视频编码、分辨率、时长、码率、音频轨道、字幕轨道和外部字幕文件。

### `check` — 检测系统依赖

```
sub-extractor check
```

检测：ffmpeg、ffprobe、mkvtoolnix（可选）、OCR 引擎（可选）。

## GUI 图形界面

Sub Extractor 包含一个基于 PySide6 的三标签页图形界面：

### Extract（提取）标签页
完整的字幕提取工作流：
- 文件选择器（支持全部 10 种视频格式）
- 输出目录选择器
- 字幕格式选择器（SRT/ASS/SSA/VTT/SUP/SUB）
- 语言和轨道过滤
- **OCR 设置面板：**
  - OCR 启用复选框
  - 引擎选择（EasyOCR / PaddleOCR）
  - 语言代码输入
  - 帧间隔选择（0.5s – 5.0s）
  - 置信度阈值选择（0.5 – 0.9）
  - 字幕区域选择（底部 / 顶部 / 全屏）
- 保留视频 / 包含外部字幕 / 预览复选框
- 进度条和状态更新
- 结果表格显示所有输出文件及警告/错误日志

### Info（信息）标签页
- 后台线程加载视频元数据（UI 不卡顿）
- 视频信息：文件名、格式、编码、分辨率、时长、码率
- 音频轨道表格：编号、编码、语言、声道、标题
- 内嵌字幕轨道表格：编号、编码、语言、标记、标题
- 外部字幕文件表格：编码、语言、文件名

### Check（检测）标签页
- 标签页激活时自动运行检测
- 依赖状态表：ffmpeg、ffprobe、mkvtoolnix、OCR 引擎
- 缺少依赖时显示安装说明
- 重新检测按钮

启动 GUI：
```bash
sub-extractor-gui
```

## 输出结构

对于一个包含多种字幕源的视频 `movie.mkv`：

```
subtitles/
├── movie.eng.srt          # 提取的英文软字幕
├── movie.chi.srt          # 提取的中文软字幕
├── movie.eng.sup          # 提取的英文 PGS 图形字幕
├── movie.ch_sim.ocr.srt   # OCR 识别的中文硬字幕
├── movie_clean.mkv        # 去除所有字幕轨道的清洁视频
└── (外部 .srt/.ass)       # 复制的外部同名字幕文件（如存在）
```

## 架构设计

Sub Extractor 采用**五层 Pipeline 架构**，基于**策略模式（Strategy Pattern）**：

```
Input → Detection → Extraction → Processing → Output
  ↓         ↓            ↓           ↓          ↓
VideoInfo  Tracks     .srt/.ass   清洁视频   写入磁盘
```

新增格式或字幕类型只需编写新的 Handler 类 — **无需修改 Pipeline 核心代码**。

```
sub_extractor/
├── input/             # 文件验证 & ffprobe 探测
├── detection/         # 软字幕/外部/硬字幕发现
│   ├── soft_sub_detector.py       # 内嵌字幕检测
│   ├── external_sub_detector.py   # 同名字幕文件发现
│   └── hard_sub_detector.py       # OCR 触发轨道
├── extraction/        # 字幕提取 & 格式转换
│   ├── ffmpeg_extractor.py        # 文本字幕
│   ├── bitmap_extractor.py        # 图形字幕 (PGS/VobSub)
│   └── ocr_extractor.py           # 硬字幕 OCR
├── ocr/               # OCR 管道子包
│   ├── frame_extractor.py         # ffmpeg pipe 帧提取
│   ├── preprocessor.py            # OpenCV 图像预处理
│   ├── engine.py                  # OCR 引擎抽象层
│   ├── deduplicator.py            # 帧间文本去重合并
│   ├── timestamp.py               # 时间戳格式化
│   └── formatter.py               # SRT/ASS 生成
├── processing/        # 视频重新封装（去除字幕）
└── output/            # 文件系统输出
```

### OCR 管道详解

```
视频文件 → FrameExtractor → Preprocessor → OCREngine → Deduplicator → Formatter
              ↓                ↓              ↓            ↓              ↓
         ffmpeg pipe     灰度化         EasyOCR/     相邻帧合并     .srt/.ass
         零磁盘I/O        自适应阈值     PaddleOCR     时间范围      文件输出
                         降噪                         置信度过滤
                         区域检测
```

OCR 管道采用常量内存（生成器模式）— 任何时长的视频都可以处理，不会将全部帧加载到 RAM。

## 性能调优

### OCR 速度 vs. 精度

| 设置 | 快速 | 均衡 | 高精度 |
|------|------|------|--------|
| `--ocr-interval` | 5.0s | 1.0s | 0.5s |
| `--ocr-confidence` | 0.5 | 0.7 | 0.8 |
| 处理时间（2h 视频） | ~5 分钟 | ~15 分钟 | ~30 分钟 |

### 内存使用
- OCR 提取使用流式管道（生成器模式）
- 每帧处理完成后立即释放，然后读取下一帧
- 内存使用恒定，与视频长度无关（约 200-500 MB 用于 OCR 模型 + 单帧缓冲）

### GPU 加速
- EasyOCR：设置 `gpu=True`（自动检测，GPU 不可用时回退到 CPU）
- PaddleOCR：安装 GPU 版 PaddlePaddle
- GPU 可提供 3-5 倍的 OCR 处理加速

## 常见问题排查

### ffmpeg 未找到

```
Error: ffmpeg/ffprobe not found.
```

**解决方法：** 安装 ffmpeg 并确保它在系统 PATH 中。
- Windows：`winget install ffmpeg` → 重启终端
- macOS：`brew install ffmpeg`
- Linux：`sudo apt install ffmpeg`
- 验证：`ffmpeg -version`

### OCR 依赖缺失

```
Error: OCR engine 'easyocr' is not available.
```

**解决方法：**
```bash
pip install "sub-extractor[ocr-easyocr]"
# 首次运行会下载模型（约 100-500 MB，缓存以供后续使用）
```

### "未找到字幕"

- 视频可能没有内嵌字幕轨道
- 如果字幕烧录在画面中，请使用 `--ocr`
- 用 `sub-extractor info video.mkv` 查看可用轨道

### OCR 结果质量差

- **语言不匹配**：确保 `--ocr-language` 与字幕语言一致
- **字幕区域**：尝试 `bottom`（底部）、`top`（顶部）或 `full`（全屏）
- **帧间隔**：减小 `--ocr-interval` 至 0.5 以获得更精确的时间轴
- **置信度**：降低 `--ocr-confidence` 至 0.5 以捕获更多文本（可能包含噪音）
- **字幕样式**：高度风格化的字幕（彩色描边、特殊字体）OCR 识别难度较大

### 文件格式不支持

```
Error: Unsupported format '.xxx'
```

- 文件扩展名不被识别。支持的格式：`.mp4`、`.mkv`、`.avi`、`.mov`、`.webm`、`.ts`、`.flv`、`.wmv`、`.m4v`、`.ogv`
- 如果视频可以在播放器中播放，先重新封装为 MKV：
  ```bash
  ffmpeg -i video.xxx -c copy video.mkv
  ```

### 输出文件为空

- 字幕轨道可能为空或损坏
- 对于位图字幕：该轨道可能需要 OCR（使用 `--ocr`）
- 对于 OCR：尝试降低 `--ocr-confidence` 至 0.5

## 参考的开源项目

Sub Extractor 的设计参考了以下优秀开源项目：

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
- [x] Windows 独立可执行文件
- [x] 主流视频格式扩展（AVI/MOV/WebM/TS/FLV/WMV/M4V/OGV）
- [x] 图形字幕支持（PGS/VobSub/DVB/XSub）
- [x] 硬字幕 OCR 提取（EasyOCR + PaddleOCR）
- [ ] 内置批量处理（多文件队列）
- [ ] 字幕同步工具（时间偏移、拉伸）
- [ ] OCR 前自动检测视频中是否存在硬字幕
- [ ] GPU 加速 OCR 含进度反馈
- [ ] GUI 字幕编辑/预览面板
- [ ] macOS/Linux 独立构建

## 开源协议

MIT License — 详见 [LICENSE](LICENSE) 文件。
