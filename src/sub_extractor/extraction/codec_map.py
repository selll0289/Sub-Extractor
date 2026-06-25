"""Mapping from ffprobe codec names to file extensions and ffmpeg encoders.

Used by the FFmpegExtractor to determine output formats and whether
transcoding is needed.
"""

# codec_name (from ffprobe) → file extension (without dot)
CODEC_TO_EXT: dict[str, str] = {
    # Text subtitles — direct extraction possible
    "subrip":            "srt",
    "srt":               "srt",
    "ass":               "ass",
    "ssa":               "ssa",
    "webvtt":            "vtt",
    "vtt":               "vtt",
    "mov_text":          "srt",   # MP4 tx3g/mov_text → best extracted via ffmpeg to SRT
    "tx3g":              "srt",
    "dvb_subtitle":      "srt",   # DVB bitmap → ffmpeg can OCR or extract as text
    "microdvd":          "sub",
    "subviewer":         "sub",
    "subviewer1":        "sub",
    "jacosub":           "jss",
    "realtext":          "rt",
    "sami":              "smi",
    "stl":               "stl",
    # Bitmap subtitles — extract as-is (v2: OCR)
    "dvd_subtitle":      "sub",   # VobSub .sub/.idx pair
    "hdmv_pgs_subtitle": "sup",
    "pgs":               "sup",
    "xsub":              "sub",
}

# Format conversion: target extension → ffmpeg encoder name
EXT_TO_FFMPEG_ENCODER: dict[str, str] = {
    "srt": "subrip",
    "ass": "ass",
    "ssa": "ssa",
    "vtt": "webvtt",
}


def get_ffmpeg_encoder(ext: str) -> str:
    """Return the ffmpeg encoder name for a target subtitle extension.

    Falls back to 'subrip' for unknown extensions.
    """
    return EXT_TO_FFMPEG_ENCODER.get(ext.lstrip("."), "subrip")


def get_extension(codec: str) -> str:
    """Return the file extension for a subtitle codec.

    Falls back to 'srt' for unknown codecs.
    """
    codec_lower = codec.lower()
    return CODEC_TO_EXT.get(codec_lower, "srt")
