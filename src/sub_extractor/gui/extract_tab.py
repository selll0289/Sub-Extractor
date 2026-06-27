"""Extract tab — main subtitle extraction workflow with progress tracking."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from sub_extractor.enums import PipelineStage
from sub_extractor.gui.pipeline_worker import PipelineWorker
from sub_extractor.gui.widgets import FilePicker, OutputDirPicker
from sub_extractor.models import ExtractionJob


class ExtractTab(QWidget):
    """Tab for the subtitle extraction workflow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None
        self._running = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # ── Input ────────────────────────────────────────────
        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)

        input_layout.addWidget(QLabel("Video File:"))
        self._file_picker = FilePicker()
        self._file_picker.file_selected.connect(self._on_input_changed)
        input_layout.addWidget(self._file_picker)

        input_layout.addWidget(QLabel("Output Directory:"))
        self._output_picker = OutputDirPicker()
        self._output_picker.directory_selected.connect(self._on_input_changed)
        input_layout.addWidget(self._output_picker)

        layout.addWidget(input_group)

        # ── Options ──────────────────────────────────────────
        opt_group = QGroupBox("Options")
        opt_layout = QVBoxLayout(opt_group)

        # Format
        fmt_row = QWidget()
        fmt_layout = QHBoxLayout(fmt_row)
        fmt_layout.setContentsMargins(0, 0, 0, 0)
        fmt_layout.addWidget(QLabel("Subtitle Format:"))
        self._format_combo = QComboBox()
        self._format_combo.addItems(["srt", "ass", "ssa", "vtt", "sup", "sub"])
        self._format_combo.setCurrentText("srt")
        fmt_layout.addWidget(self._format_combo)
        fmt_layout.addStretch()
        opt_layout.addWidget(fmt_row)

        # Languages
        lang_row = QWidget()
        lang_layout = QHBoxLayout(lang_row)
        lang_layout.setContentsMargins(0, 0, 0, 0)
        lang_layout.addWidget(QLabel("Languages:"))
        self._languages_edit = QLineEdit()
        self._languages_edit.setPlaceholderText("eng,chi — leave empty for all")
        self._languages_edit.setMaximumWidth(300)
        lang_layout.addWidget(self._languages_edit)
        lang_layout.addStretch()
        opt_layout.addWidget(lang_row)

        # Tracks
        track_row = QWidget()
        track_layout = QHBoxLayout(track_row)
        track_layout.setContentsMargins(0, 0, 0, 0)
        track_layout.addWidget(QLabel("Tracks:"))
        self._tracks_edit = QLineEdit()
        self._tracks_edit.setPlaceholderText("0,2 — leave empty for all")
        self._tracks_edit.setMaximumWidth(300)
        track_layout.addWidget(self._tracks_edit)
        track_layout.addStretch()
        opt_layout.addWidget(track_row)

        # Checkboxes
        self._keep_video_cb = QCheckBox("Keep clean video copy")
        self._keep_video_cb.setChecked(True)
        opt_layout.addWidget(self._keep_video_cb)

        self._external_cb = QCheckBox("Include external (sidecar) subtitles")
        self._external_cb.setChecked(True)
        opt_layout.addWidget(self._external_cb)

        self._dry_run_cb = QCheckBox("Dry run (preview only, no files written)")
        opt_layout.addWidget(self._dry_run_cb)

        layout.addWidget(opt_group)

        # ── OCR Options ────────────────────────────────────────
        ocr_group = QGroupBox("Hardcoded Subtitle OCR")
        ocr_layout = QVBoxLayout(ocr_group)

        self._ocr_enabled_cb = QCheckBox(
            "Enable OCR for burned-in (hardcoded) subtitles"
        )
        self._ocr_enabled_cb.setToolTip(
            "Extract subtitles burned into the video image via OCR. "
            "Requires: pip install sub-extractor[ocr-easyocr]"
        )
        ocr_layout.addWidget(self._ocr_enabled_cb)

        ocr_row1 = QWidget()
        ocr_row1_layout = QHBoxLayout(ocr_row1)
        ocr_row1_layout.setContentsMargins(0, 0, 0, 0)
        ocr_row1_layout.addWidget(QLabel("Engine:"))
        self._ocr_engine_combo = QComboBox()
        self._ocr_engine_combo.addItems(["easyocr", "paddleocr"])
        ocr_row1_layout.addWidget(self._ocr_engine_combo)
        ocr_row1_layout.addWidget(QLabel("Language:"))
        self._ocr_lang_edit = QLineEdit()
        self._ocr_lang_edit.setPlaceholderText("ch_sim")
        self._ocr_lang_edit.setMaximumWidth(120)
        ocr_row1_layout.addWidget(self._ocr_lang_edit)
        ocr_row1_layout.addStretch()
        ocr_layout.addWidget(ocr_row1)

        ocr_row2 = QWidget()
        ocr_row2_layout = QHBoxLayout(ocr_row2)
        ocr_row2_layout.setContentsMargins(0, 0, 0, 0)
        ocr_row2_layout.addWidget(QLabel("Frame Interval (seconds):"))
        self._ocr_interval_spin = QComboBox()
        self._ocr_interval_spin.addItems(
            ["0.5", "1.0", "1.5", "2.0", "3.0", "5.0"]
        )
        self._ocr_interval_spin.setCurrentText("1.0")
        self._ocr_interval_spin.setEditable(True)
        ocr_row2_layout.addWidget(self._ocr_interval_spin)
        ocr_row2_layout.addWidget(QLabel("Confidence:"))
        self._ocr_confidence_spin = QComboBox()
        self._ocr_confidence_spin.addItems(
            ["0.5", "0.6", "0.7", "0.8", "0.9"]
        )
        self._ocr_confidence_spin.setCurrentText("0.7")
        self._ocr_confidence_spin.setEditable(True)
        ocr_row2_layout.addWidget(self._ocr_confidence_spin)
        ocr_row2_layout.addStretch()
        ocr_layout.addWidget(ocr_row2)

        ocr_row3 = QWidget()
        ocr_row3_layout = QHBoxLayout(ocr_row3)
        ocr_row3_layout.setContentsMargins(0, 0, 0, 0)
        ocr_row3_layout.addWidget(QLabel("Subtitle Region:"))
        self._ocr_region_combo = QComboBox()
        self._ocr_region_combo.addItems(["bottom", "top", "full"])
        ocr_row3_layout.addWidget(self._ocr_region_combo)
        ocr_row3_layout.addStretch()
        ocr_layout.addWidget(ocr_row3)

        layout.addWidget(ocr_group)

        # ── Extract button ───────────────────────────────────
        self._extract_btn = QPushButton("Extract Subtitles")
        self._extract_btn.setMinimumHeight(40)
        self._extract_btn.setStyleSheet(
            "QPushButton { font-size: 14px; font-weight: bold; "
            "background-color: #1976D2; color: white; border-radius: 4px; }"
            "QPushButton:hover { background-color: #1565C0; }"
            "QPushButton:disabled { background-color: #BDBDBD; }"
        )
        self._extract_btn.clicked.connect(self._on_extract)
        self._extract_btn.setEnabled(False)
        layout.addWidget(self._extract_btn)

        # ── Progress ─────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        layout.addWidget(self._progress_bar)

        self._progress_label = QLabel()
        self._progress_label.setStyleSheet("color: #555;")
        self._progress_label.setVisible(False)
        layout.addWidget(self._progress_label)

        # ── Results ──────────────────────────────────────────
        self._results_group = QGroupBox("Results")
        self._results_group.setVisible(False)
        results_layout = QVBoxLayout(self._results_group)

        self._results_summary = QLabel()
        self._results_summary.setWordWrap(True)
        results_layout.addWidget(self._results_summary)

        self._results_table = QTableWidget(0, 2)
        self._results_table.setHorizontalHeaderLabels(["Type", "File"])
        self._results_table.horizontalHeader().setStretchLastSection(True)
        self._results_table.verticalHeader().setVisible(False)
        self._results_table.setEditTriggers(QTableWidget.NoEditTriggers)
        results_layout.addWidget(self._results_table)

        self._results_log = QTextEdit()
        self._results_log.setReadOnly(True)
        self._results_log.setMaximumHeight(120)
        self._results_log.setVisible(False)
        results_layout.addWidget(self._results_log)

        layout.addWidget(self._results_group)
        layout.addStretch()

    def _on_input_changed(self) -> None:
        """Enable extract button only when both input and output are set."""
        has_input = bool(self._file_picker.path())
        has_output = bool(self._output_picker.path())
        self._extract_btn.setEnabled(has_input and has_output and not self._running)

    def _on_extract(self) -> None:
        """Validate inputs and start extraction on a background thread."""
        input_path = self._file_picker.path()
        output_path = self._output_picker.path()

        if not input_path or not output_path:
            return

        # Build job from widget values
        job = ExtractionJob(
            input_video=Path(input_path),
            output_dir=Path(output_path),
            keep_video=self._keep_video_cb.isChecked(),
            preferred_sub_format=self._format_combo.currentText(),
            target_languages=self._parse_comma_list(self._languages_edit.text()),
            target_track_indices=self._parse_int_list(self._tracks_edit.text()),
            include_external=self._external_cb.isChecked(),
            enable_hard_sub_ocr=self._ocr_enabled_cb.isChecked(),
            ocr_engine=self._ocr_engine_combo.currentText(),
            ocr_language=self._ocr_lang_edit.text().strip() or "ch_sim",
            ocr_frame_interval=float(
                self._ocr_interval_spin.currentText() or "1.0"
            ),
            ocr_confidence_threshold=float(
                self._ocr_confidence_spin.currentText() or "0.7"
            ),
            ocr_subtitle_region=self._ocr_region_combo.currentText(),
        )

        # Dry run
        if self._dry_run_cb.isChecked():
            self._do_dry_run(job)
            return

        # Start extraction
        self._running = True
        self._extract_btn.setEnabled(False)
        self._extract_btn.setText("Extracting...")
        self._progress_bar.setVisible(True)
        self._progress_bar.setValue(0)
        self._progress_label.setVisible(True)
        self._results_group.setVisible(False)
        self._results_log.setVisible(False)

        self._thread = QThread()
        self._worker = PipelineWorker()
        self._worker.set_job(job)
        self._worker.set_mode("extract")
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress_updated.connect(self._on_progress)
        self._worker.extraction_finished.connect(self._on_finished)
        self._worker.extraction_error.connect(self._on_extract_error)
        self._worker.extraction_finished.connect(self._thread.quit)
        self._worker.extraction_error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_progress(self, stage: PipelineStage, message: str, fraction: float) -> None:
        """Update progress bar and status label."""
        pct = int(fraction * 100)
        self._progress_bar.setValue(pct)
        self._progress_label.setText(f"[{stage.value}] {message}")

    def _on_finished(self, job: ExtractionJob) -> None:
        """Show extraction results."""
        self._running = False
        self._extract_btn.setEnabled(True)
        self._extract_btn.setText("Extract Subtitles")
        self._progress_bar.setVisible(False)
        self._progress_label.setVisible(False)

        self._results_group.setVisible(True)

        if job.success and not job.has_warnings:
            self._results_summary.setText(
                f"✔ Extraction complete! "
                f"{job.total_output_files} file(s) written to:\n"
                f"<b>{job.output_dir}</b>"
            )
            self._results_summary.setStyleSheet("color: green;")
        elif job.success and job.has_warnings:
            self._results_summary.setText(
                f"⚠ Complete with {len(job.warnings)} warning(s).\n"
                f"<b>{job.output_dir}</b>"
            )
            self._results_summary.setStyleSheet("color: #E65100;")
        else:
            self._results_summary.setText(
                f"✖ Completed with {len(job.errors)} error(s)."
            )
            self._results_summary.setStyleSheet("color: red;")

        # Populate results table
        self._results_table.setRowCount(0)
        for p in job.extracted_subtitles:
            row = self._results_table.rowCount()
            self._results_table.insertRow(row)
            self._results_table.setItem(row, 0, QTableWidgetItem("Subtitle"))
            self._results_table.setItem(row, 1, QTableWidgetItem(p.name))
        if job.output_video:
            row = self._results_table.rowCount()
            self._results_table.insertRow(row)
            self._results_table.setItem(row, 0, QTableWidgetItem("Clean video"))
            self._results_table.setItem(row, 1, QTableWidgetItem(job.output_video.name))

        # Warnings/errors log
        msgs = []
        for w in job.warnings:
            msgs.append(f"[WARN] {w}")
        for e in job.errors:
            msgs.append(f"[ERROR] {e}")
        if msgs:
            self._results_log.setVisible(True)
            self._results_log.setPlainText("\n".join(msgs))
        else:
            self._results_log.setVisible(False)

    def _on_extract_error(self, message: str) -> None:
        """Handle pipeline-level exceptions."""
        self._running = False
        self._extract_btn.setEnabled(True)
        self._extract_btn.setText("Extract Subtitles")
        self._progress_bar.setVisible(False)
        self._progress_label.setVisible(False)

        QMessageBox.critical(self, "Extraction Error", message)

    def _do_dry_run(self, job: ExtractionJob) -> None:
        """Preview what would be extracted without running the full pipeline."""
        from sub_extractor.pipeline import Pipeline
        from sub_extractor.exceptions import SubExtractorError

        try:
            pipeline = Pipeline()
            handler = pipeline._find_input_handler(job.input_video)
            job.video_info = handler.process(job.input_video)
        except SubExtractorError as exc:
            QMessageBox.warning(self, "Error", f"Cannot probe video:\n\n{exc}")
            return

        vi = job.video_info
        if not vi:
            return

        lines = [
            f"<b>Input:</b> {vi.path.name}",
            f"<b>Format:</b> {vi.format.value.upper()} &mdash; "
            f"{vi.video_codec} {vi.width}x{vi.height}",
            f"<b>Duration:</b> {self._fmt_duration(vi.duration_seconds)}",
            f"<b>Embedded subtitle tracks:</b> {len(vi.subtitle_tracks)}",
        ]

        for s in vi.subtitle_tracks:
            lang = s.language or "unknown"
            flags = []
            if s.is_forced:
                flags.append("forced")
            if s.is_default:
                flags.append("default")
            flag_str = f" ({', '.join(flags)})" if flags else ""
            lines.append(
                f"  &bull; Track {s.index}: [{s.codec}] {lang}{flag_str}"
            )

        if job.keep_video:
            clean_name = f"{job.input_video.stem}_clean{job.input_video.suffix}"
            lines.append(f"<b>Clean video:</b> {clean_name}")
        else:
            lines.append("<b>Clean video:</b> <i>skipped (--no-video)</i>")

        lines.append(f"<b>Output directory:</b> {job.output_dir}")

        self._results_group.setVisible(True)
        self._results_summary.setText(
            "<b>DRY RUN</b> &mdash; no files will be modified<br><br>"
            + "<br>".join(lines)
        )
        self._results_summary.setStyleSheet("color: #2196F3;")
        self._results_table.setRowCount(0)
        self._results_log.setVisible(False)

    # ── helpers ──────────────────────────────────────────────

    @staticmethod
    def _parse_comma_list(value: str):
        """Parse 'eng,chi' -> ['eng', 'chi']."""
        if not value.strip():
            return None
        return [s.strip().lower() for s in value.split(",") if s.strip()]

    @staticmethod
    def _parse_int_list(value: str):
        """Parse '0,2' -> [0, 2]."""
        if not value.strip():
            return None
        result = []
        for s in value.split(","):
            s = s.strip()
            if s:
                try:
                    result.append(int(s))
                except ValueError:
                    return None
        return result or None

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        """Format seconds as H:MM:SS or M:SS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
