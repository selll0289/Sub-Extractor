"""Info tab — displays video metadata and subtitle track information."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from sub_extractor.gui.models import (
    AudioTrackTableModel,
    ExternalSubTableModel,
    SubtitleTrackTableModel,
)
from sub_extractor.gui.pipeline_worker import PipelineWorker
from sub_extractor.gui.widgets import FilePicker
from sub_extractor.models import ExtractionJob, VideoInfo


class InfoTab(QWidget):
    """Tab for viewing video file information and subtitle tracks."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: PipelineWorker | None = None

        self._audio_model = AudioTrackTableModel()
        self._sub_model = SubtitleTrackTableModel()
        self._external_model = ExternalSubTableModel()

        self._setup_ui()
        self._loading = False

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- File picker ---
        self._file_picker = FilePicker()
        self._file_picker.file_selected.connect(self._on_file_selected)
        layout.addWidget(self._file_picker)

        # --- Load button ---
        btn_row = QWidget()
        btn_layout = QVBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self._load_btn = QPushButton("Load Info")
        self._load_btn.setMinimumHeight(34)
        self._load_btn.clicked.connect(self._load_info)
        self._load_btn.setEnabled(False)
        btn_layout.addWidget(self._load_btn)
        layout.addWidget(btn_row)

        # --- Status ---
        self._status_label = QLabel("Select a video file and click Load Info.")
        self._status_label.setStyleSheet("color: #888;")
        layout.addWidget(self._status_label)

        # --- General info ---
        info_group = QGroupBox("Video Information")
        self._info_form = QFormLayout(info_group)
        self._info_labels: dict[str, QLabel] = {}
        for field in ["File", "Format", "Codec", "Resolution", "Duration", "Bit rate"]:
            label = QLabel("--")
            self._info_form.addRow(f"{field}:", label)
            self._info_labels[field] = label
        layout.addWidget(info_group)

        # --- Audio tracks ---
        audio_group = QGroupBox("Audio Tracks")
        audio_layout = QVBoxLayout(audio_group)
        audio_table = QTableView()
        audio_table.setModel(self._audio_model)
        audio_table.horizontalHeader().setStretchLastSection(True)
        audio_table.setSelectionBehavior(QTableView.SelectRows)
        audio_table.verticalHeader().setVisible(False)
        audio_layout.addWidget(audio_table)
        layout.addWidget(audio_group)

        # --- Subtitle tracks ---
        sub_group = QGroupBox("Subtitle Tracks (Embedded)")
        sub_layout = QVBoxLayout(sub_group)
        sub_table = QTableView()
        sub_table.setModel(self._sub_model)
        sub_table.horizontalHeader().setStretchLastSection(True)
        sub_table.setSelectionBehavior(QTableView.SelectRows)
        sub_table.verticalHeader().setVisible(False)
        sub_layout.addWidget(sub_table)
        layout.addWidget(sub_group)

        # --- External subs ---
        ext_group = QGroupBox("External Subtitles")
        ext_layout = QVBoxLayout(ext_group)
        ext_table = QTableView()
        ext_table.setModel(self._external_model)
        ext_table.horizontalHeader().setStretchLastSection(True)
        ext_table.setSelectionBehavior(QTableView.SelectRows)
        ext_table.verticalHeader().setVisible(False)
        ext_layout.addWidget(ext_table)
        layout.addWidget(ext_group)

    def _on_file_selected(self, path: str) -> None:
        """Enable the Load button when a file is selected."""
        self._load_btn.setEnabled(bool(path))

    def _load_info(self) -> None:
        """Start loading video info on a background thread."""
        path = self._file_picker.path()
        if not path:
            return

        self._loading = True
        self._load_btn.setEnabled(False)
        self._status_label.setText("Loading video information...")
        self._status_label.setStyleSheet("color: #2196F3;")

        # Build a minimal job for probing
        job = ExtractionJob(
            input_video=Path(path),
            output_dir=Path("."),
        )

        self._thread = QThread()
        self._worker = PipelineWorker()
        self._worker.set_job(job)
        self._worker.set_mode("info")
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.info_loaded.connect(self._on_info_loaded)
        self._worker.external_subs_loaded.connect(self._on_external_loaded)
        self._worker.extraction_error.connect(self._on_error)
        self._worker.info_loaded.connect(self._thread.quit)
        self._worker.extraction_error.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _on_info_loaded(self, video_info: VideoInfo) -> None:
        """Populate the UI with video information."""
        vi = video_info

        self._info_labels["File"].setText(vi.path.name)
        self._info_labels["Format"].setText(vi.format.value.upper())
        self._info_labels["Codec"].setText(vi.video_codec)
        self._info_labels["Resolution"].setText(f"{vi.width} x {vi.height}")
        self._info_labels["Duration"].setText(self._fmt_duration(vi.duration_seconds))
        if vi.bit_rate:
            self._info_labels["Bit rate"].setText(f"{vi.bit_rate / 1000:.0f} kbps")

        self._audio_model.set_tracks(vi.audio_tracks)
        self._sub_model.set_tracks(vi.subtitle_tracks)

        self._status_label.setText(f"Loaded: {vi.path.name}")
        self._status_label.setStyleSheet("color: green;")
        self._loading = False
        self._load_btn.setEnabled(True)

    def _on_external_loaded(self, tracks) -> None:
        """Populate external subtitle table."""
        self._external_model.set_tracks(tracks)

    def _on_error(self, message: str) -> None:
        """Show error message."""
        self._status_label.setText(f"Error: {message}")
        self._status_label.setStyleSheet("color: red;")
        self._loading = False
        self._load_btn.setEnabled(True)
        QMessageBox.warning(self, "Error", f"Failed to load video info:\n\n{message}")

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        """Format seconds as H:MM:SS or M:SS."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"
