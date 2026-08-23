#!/usr/bin/env python3
"""Repository entry point for the SVG visual-audit builder."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from dreamhouse.svg.audit import main  # noqa: E402


if __name__ == "__main__":
    main()
