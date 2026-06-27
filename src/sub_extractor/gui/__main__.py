"""Standalone entry point for PyInstaller-packaged GUI executable.

This file is the Analysis target in pyinstaller-gui.spec.
PyInstaller scans imports from here to collect all required modules.
"""

import sys

from sub_extractor.gui import launch_gui

if __name__ == "__main__":
    sys.exit(launch_gui())
