"""Check tab — verifies ffmpeg/ffprobe/mkvtoolnix availability."""

from __future__ import annotations

import shutil

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from sub_extractor.ffmpeg import check_ffmpeg_available
from sub_extractor.ocr import OCR_AVAILABLE, get_available_engines


class CheckTab(QWidget):
    """Tab that checks for required external tools (ffmpeg, ffprobe, mkvtoolnix)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # --- Heading ---
        heading = QLabel("Dependency Check")
        heading.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(heading)

        desc = QLabel(
            "Sub Extractor requires ffmpeg and ffprobe to process video files. "
            "mkvtoolnix (mkvextract) is optional and enables enhanced MKV support."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # --- Check button ---
        btn_row = QWidget()
        btn_layout = QVBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)

        self._check_btn = QPushButton("Run System Check")
        self._check_btn.setMinimumHeight(36)
        self._check_btn.clicked.connect(self._run_check)
        btn_layout.addWidget(self._check_btn)
        layout.addWidget(btn_row)

        # --- Results table ---
        self._table = QTableWidget(4, 3)
        self._table.setHorizontalHeaderLabels(["Tool", "Status", "Version"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)

        # Set row labels
        for row, name in enumerate(["ffmpeg", "ffprobe", "mkvtoolnix", "OCR (EasyOCR/PaddleOCR)"]):
            item = QTableWidgetItem(name)
            item.setFont(item.font())  # keep default
            self._table.setItem(row, 0, item)
            self._table.setItem(row, 1, QTableWidgetItem("—"))
            self._table.setItem(row, 2, QTableWidgetItem("—"))

        layout.addWidget(self._table)

        # --- Install instructions ---
        self._instructions = QLabel()
        self._instructions.setWordWrap(True)
        self._instructions.setVisible(False)
        self._instructions.setStyleSheet(
            "background-color: #fff3cd; border: 1px solid #ffc107; "
            "border-radius: 4px; padding: 12px;"
        )
        layout.addWidget(self._instructions)

        # --- Separator ---
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # --- Hint ---
        hint = QLabel(
            "ℹ Sub Extractor does not bundle ffmpeg. Please install it separately "
            "using your system package manager."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(hint)

        layout.addStretch()

    def showEvent(self, event) -> None:
        """Auto-run check when the tab becomes visible."""
        super().showEvent(event)
        self._run_check()

    def _run_check(self) -> None:
        """Execute the dependency check and populate the table."""
        self._check_btn.setEnabled(False)
        self._check_btn.setText("Checking...")

        ok, ffmpeg_ver, ffprobe_ver = check_ffmpeg_available()

        # ffmpeg
        self._set_row(0, ok, ffmpeg_ver)

        # ffprobe
        ffprobe_ok = ffprobe_ver != "not found"
        self._set_row(1, ffprobe_ok, ffprobe_ver)

        # mkvtoolnix
        mkv_path = shutil.which("mkvextract")
        mkv_ok = mkv_path is not None
        mkv_ver = mkv_path if mkv_ok else "not found"
        self._set_row(2, mkv_ok, mkv_ver, required=False)

        # OCR
        engines = get_available_engines()
        if engines:
            self._set_row(3, True, ", ".join(engines), required=False)
        else:
            self._set_row(
                3, False,
                "not installed (pip install sub-extractor[ocr-easyocr])",
                required=False,
            )

        # Show instructions if ffmpeg is missing
        if not ok:
            self._instructions.setText(
                "<b>ffmpeg is required but was not found.</b><br><br>"
                "<b>Windows:</b> <code>winget install ffmpeg</code> or "
                "<code>choco install ffmpeg</code><br>"
                "<b>macOS:</b> <code>brew install ffmpeg</code><br>"
                "<b>Linux (Debian/Ubuntu):</b> <code>sudo apt install ffmpeg</code><br>"
                "<b>Linux (Fedora):</b> <code>sudo dnf install ffmpeg</code><br><br>"
                "After installing, restart Sub Extractor."
            )
            self._instructions.setVisible(True)
        else:
            self._instructions.setVisible(False)

        self._check_btn.setEnabled(True)
        self._check_btn.setText("Re-run System Check")

    def _set_row(self, row: int, ok: bool, version: str, required: bool = True) -> None:
        """Set status and version for a table row."""
        if ok:
            status_item = QTableWidgetItem("✓ Available")
            status_item.setForeground(Qt.darkGreen)
        elif required:
            status_item = QTableWidgetItem("✗ Missing")
            status_item.setForeground(Qt.red)
        else:
            status_item = QTableWidgetItem("— Not installed")
            status_item.setForeground(Qt.gray)

        self._table.setItem(row, 1, status_item)
        self._table.setItem(row, 2, QTableWidgetItem(version))
