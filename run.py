#!/usr/bin/env python3
"""Red Thread AI Detective - single entry point.

    python run.py            interactive terminal
    python run.py --help     all options

This file is deliberately thin: orchestration lives in src/application.py, component initialisation in
src/bootstrap.py, and the terminal interface in src/terminal.py. Game logic stays in the member modules.
"""
import sys
from pathlib import Path

if sys.version_info < (3, 11):
    sys.exit("Red Thread requires Python 3.11 or newer.")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.terminal import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
