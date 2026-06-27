"""Main window for the Sub Extractor GUI.

A QMainWindow with a tabbed interface: Extract | Info | Check.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from sub_extractor import __version__
from sub_extractor.gui.check_tab import CheckTab
from sub_extractor.gui.extract_tab import ExtractTab
from sub_extractor.gui.info_tab import InfoTab


class MainWindow(QMainWindow):
    """Application main window with tabbed interface."""

    MIN_WIDTH = 900
    MIN_HEIGHT = 620

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"Sub Extractor v{__version__}")
        self.setMinimumSize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        central_layout = QVBoxLayout(central)
        central_layout.setContentsMargins(8, 8, 8, 8)

        # Tab widget
        self._tabs = QTabWidget()
        self._extract_tab = ExtractTab()
        self._info_tab = InfoTab()
        self._check_tab = CheckTab()

        self._tabs.addTab(self._extract_tab, "  Extract  ")
        self._tabs.addTab(self._info_tab, "  Info  ")
        self._tabs.addTab(self._check_tab, "  Check  ")

        central_layout.addWidget(self._tabs)

        # Menu bar
        self._setup_menubar()

        # Status bar
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

        # Connect tab changes to update status
        self._tabs.currentChanged.connect(self._on_tab_changed)

    def _setup_menubar(self) -> None:
        """Create the menu bar with File, Tools, and Help menus."""
        menubar: QMenuBar = self.menuBar()

        # ── File ─────────────────────────────────────────────
        file_menu = menubar.addMenu("&File")

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # ── Help ─────────────────────────────────────────────
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _on_tab_changed(self, index: int) -> None:
        """Update status bar when tabs change."""
        tab_names = ["Extract subtitles", "View video info", "System check"]
        if 0 <= index < len(tab_names):
            self._status.showMessage(tab_names[index])

    def _show_about(self) -> None:
        """Show the About dialog."""
        QMessageBox.about(
            self,
            "About Sub Extractor",
            f"<h3>Sub Extractor v{__version__}</h3>"
            "<p>Extract subtitles from video files with ease.</p>"
            "<p>Supports MP4 and MKV containers. Extracts soft subtitles, "
            "discovers sidecar subtitle files, and produces clean video output.</p>"
            "<p><b>License:</b> MIT</p>"
            "<p><i>Requires ffmpeg and ffprobe installed on your system.</i></p>",
        )

    def closeEvent(self, event) -> None:
        """Warn if extraction is in progress."""
        if self._extract_tab._running:
            reply = QMessageBox.question(
                self,
                "Extraction in Progress",
                "An extraction is currently running. Cancel and exit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
        event.accept()
