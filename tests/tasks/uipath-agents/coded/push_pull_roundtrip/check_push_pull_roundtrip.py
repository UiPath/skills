#!/usr/bin/env python3
"""Push/pull roundtrip check.

Asserts:
  1. The local edit landed in `roundtrip-agent/main.py` (output prefix `echo: `).
  2. `.env` still has a `UIPATH_PROJECT_ID=` line (auto-sync identity preserved).
  3. The pulled sibling directory exists and contains the same source files.
  4. The pulled `main.py` carries the same edit (proves push went up before pull came down).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

CWD = Path(os.getcwd())
LOCAL = CWD / "roundtrip-agent"
PULLED = CWD / "roundtrip-agent-pulled"
LOCAL_MAIN = LOCAL / "main.py"
PULLED_MAIN = PULLED / "main.py"
LOCAL_ENV = LOCAL / ".env"

EDIT_MARKER = "echo: "
EXPECTED_PROJECT_ID = "89852b5d-8559-4c57-b752-0e2b500902fc"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    if not LOCAL_MAIN.is_file():
        fail(f"missing {LOCAL_MAIN}")
    local_text = LOCAL_MAIN.read_text(encoding="utf-8")
    if EDIT_MARKER not in local_text:
        fail(
            f"local main.py does not contain the requested edit marker '{EDIT_MARKER}'. "
            "The agent never applied the local change before pushing."
        )
    print("OK: local main.py carries the requested edit")

    if not LOCAL_ENV.is_file():
        fail(f"missing {LOCAL_ENV} — push/pull anti-pattern: do not delete .env")
    env_text = LOCAL_ENV.read_text(encoding="utf-8")
    if not re.search(
        rf"^UIPATH_PROJECT_ID={re.escape(EXPECTED_PROJECT_ID)}\s*$",
        env_text,
        re.M,
    ):
        fail(
            f".env no longer carries `UIPATH_PROJECT_ID={EXPECTED_PROJECT_ID}` — "
            "sync identity must be preserved (changing this id breaks the link "
            "between the local folder and its Studio Web project)."
        )
    print(f"OK: .env still pins UIPATH_PROJECT_ID={EXPECTED_PROJECT_ID}")

    if not PULLED.is_dir():
        fail(f"missing pulled sibling directory {PULLED} — agent did not pull a fresh copy")
    if not PULLED_MAIN.is_file():
        fail(f"missing {PULLED_MAIN} — pulled copy is incomplete")
    pulled_text = PULLED_MAIN.read_text(encoding="utf-8")
    if EDIT_MARKER not in pulled_text:
        fail(
            f"pulled main.py does not contain '{EDIT_MARKER}' — either the push did not land "
            "on the remote before the pull, or push/pull operated on different projects"
        )
    print("OK: pulled main.py reflects the pushed edit (round-trip closed)")

    print("OK: push/pull roundtrip completed and .env identity preserved")


if __name__ == "__main__":
    main()
