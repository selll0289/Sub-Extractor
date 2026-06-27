"""Reusable small widgets for the Sub Extractor GUI."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)


class FilePicker(QWidget):
    """A horizontal row: read-only line edit + Browse button → file dialog.

    Emits ``file_selected(str)`` when the user picks a file.
    """

    file_selected = Signal(str)

    def __init__(
        self,
        file_filter: str = (
            "Video files (*.mp4 *.mkv *.avi *.mov *.webm *.ts "
            "*.flv *.wmv *.m4v *.ogv);;All files (*.*)"
        ),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._filter = file_filter

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._line_edit = QLineEdit()
        self._line_edit.setReadOnly(True)
        self._line_edit.setPlaceholderText("Select a video file...")
        layout.addWidget(self._line_edit, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(browse_btn)

    def path(self) -> str:
        """Return the currently selected path (empty string if none)."""
        return self._line_edit.text()

    def set_path(self, path: str) -> None:
        """Programmatically set the file path."""
        self._line_edit.setText(path)
        self.file_selected.emit(path)

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", self._filter)
        if path:
            self._line_edit.setText(path)
            self.file_selected.emit(path)


class OutputDirPicker(QWidget):
    """A horizontal row: read-only line edit + Browse button → directory dialog.

    Emits ``directory_selected(str)`` when the user picks a directory.
    """

    directory_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._line_edit = QLineEdit()
        self._line_edit.setReadOnly(True)
        self._line_edit.setPlaceholderText("Select output directory...")
        layout.addWidget(self._line_edit, stretch=1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        layout.addWidget(browse_btn)

    def path(self) -> str:
        """Return the currently selected path (empty string if none)."""
        return self._line_edit.text()

    def set_path(self, path: str) -> None:
        """Programmatically set the directory path."""
        self._line_edit.setText(path)
        self.directory_selected.emit(path)

    def _on_browse(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if path:
            self._line_edit.setText(path)
            self.directory_selected.emit(path)
