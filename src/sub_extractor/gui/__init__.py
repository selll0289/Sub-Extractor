"""Graphical user interface for Sub Extractor.

Built with PySide6 (Qt for Python). Provides a three-tab interface:
- Extract: subtitle extraction with progress tracking
- Info: video metadata and track viewer
- Check: ffmpeg/ffprobe dependency verification

Usage::

    from sub_extractor.gui import launch_gui
    sys.exit(launch_gui())
"""

from __future__ import annotations

import sys


def launch_gui() -> int:
    """Create the QApplication, show the main window, and enter the event loop.

    Returns:
        The exit code from ``app.exec()`` (0 on clean exit).
    """
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
    except ImportError:
        print(
            "PySide6 is required for the GUI. Install it with:\n"
            "  pip install 'sub-extractor[gui]'\n"
            "  or: pip install PySide6",
            file=sys.stderr,
        )
        return 1

    from sub_extractor import __version__

    # Enable high-DPI scaling on Windows
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Sub Extractor")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("SubExtractor")

    from sub_extractor.gui.main_window import MainWindow

    window = MainWindow()
    window.show()

    return app.exec()
