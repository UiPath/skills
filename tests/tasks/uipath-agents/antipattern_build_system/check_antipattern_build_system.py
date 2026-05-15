#!/usr/bin/env python3
"""C1 anti-pattern check — `[build-system]` must be gone after the fix."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "legacy-port"
PYPROJECT = ROOT / "pyproject.toml"


def main() -> None:
    if not PYPROJECT.is_file():
        sys.exit(f"FAIL: missing {PYPROJECT}")
    text = PYPROJECT.read_text(encoding="utf-8")
    # `[build-system]` must be removed entirely. A line-anchored regex is the
    # right precision — substring search would false-flag a comment.
    if re.search(r"^\s*\[build-system\]", text, re.M):
        sys.exit(
            "FAIL: pyproject.toml still has a [build-system] section. "
            "Critical Rule C1: UiPath coded agents do not use a build "
            "system; remove the section entirely."
        )
    # Sanity: `[project]` survived the edit.
    if not re.search(r"^\s*\[project\]", text, re.M):
        sys.exit(
            "FAIL: pyproject.toml lost its [project] section while removing "
            "[build-system]. Only the build-system block should be removed."
        )
    print("OK: pyproject.toml has [project] and no [build-system] section")


if __name__ == "__main__":
    main()
