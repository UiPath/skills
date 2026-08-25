#!/usr/bin/env python3
"""C4 (correct SDK import path) anti-pattern check.

Asserts the wrong import has been removed and the correct one is in
place. Importantly, both regexes are line-anchored and require the
imported name to be exactly `UiPath` so a member-list import like
`from uipath.platform import UiPath, foo` still passes while
`from uipath import UiPath` is rejected.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "bad-import"
MAIN = ROOT / "main.py"

WRONG = re.compile(r"^\s*from\s+uipath\s+import\s+(?:[^,\n]*,\s*)*UiPath(?:\s*,|$)", re.M)
RIGHT = re.compile(r"^\s*from\s+uipath\.platform\s+import\s+(?:[^,\n]*,\s*)*UiPath\b", re.M)


def main() -> None:
    if not MAIN.is_file():
        sys.exit(f"FAIL: missing {MAIN}")
    text = MAIN.read_text(encoding="utf-8")
    if WRONG.search(text):
        sys.exit(
            "FAIL: main.py still has `from uipath import UiPath`. "
            "Critical Rule C4: the correct import is `from uipath.platform "
            "import UiPath`."
        )
    if not RIGHT.search(text):
        sys.exit(
            "FAIL: main.py does not import UiPath from `uipath.platform`. "
            "Add `from uipath.platform import UiPath`."
        )
    print("OK: main.py imports UiPath from `uipath.platform` (no `from uipath import UiPath`)")


if __name__ == "__main__":
    main()
