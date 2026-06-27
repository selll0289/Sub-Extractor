"""Entry point for `python -m sub_extractor`.

Usage:
    python -m sub_extractor [cli args...]   # CLI mode (default)
    python -m sub_extractor --gui           # GUI mode
"""

import sys

if __name__ == "__main__":
    if "--gui" in sys.argv:
        sys.argv.remove("--gui")
        from sub_extractor.gui import launch_gui
        sys.exit(launch_gui())
    else:
        from sub_extractor.cli import main
        main()
