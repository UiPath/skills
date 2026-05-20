#!/usr/bin/env python3
"""Existing-coded project resume check.

The seed left a half-finished LangGraph project on disk:
  - has_venv == false, has_entry_points == false, scaffolding done.

A correct resume:
  - prepares the missing `.venv/`
  - regenerates `entry-points.json` from the (edited) code
  - preserves the original `mood` field in `main.py`
  - adds the new `confidence` field to the output

Asserts:
  1. `mood-meter/.venv/` exists (the missing venv was prepped).
  2. `mood-meter/entry-points.json` exists and advertises BOTH `mood`
     and `confidence` as output fields.
  3. `main.py` still defines a `mood` field (original logic kept).
  4. `main.py` now defines a `confidence` field (new feature landed).
  5. `main.py` still exports a top-level `graph =` variable
     (LangGraph entrypoint preserved).
  6. `pyproject.toml` still has no `[build-system]` section
     (Critical Rule C1 — the resume must not introduce one).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "mood-meter"
MAIN = ROOT / "main.py"
ENTRY_POINTS = ROOT / "entry-points.json"
PYPROJECT = ROOT / "pyproject.toml"
VENV = ROOT / ".venv"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    if not ROOT.is_dir():
        fail(f"missing project directory {ROOT}")

    if not VENV.is_dir():
        fail(
            f"{VENV} does not exist. The seed had no `.venv/` (has_venv == false); "
            "the skill must prep the missing venv on resume."
        )
    print("OK: .venv was prepped (has_venv flipped to true)")

    if not ENTRY_POINTS.is_file():
        fail(
            f"{ENTRY_POINTS} missing. The seed had no `entry-points.json` "
            "(has_entry_points == false); the skill must regenerate the schema "
            "via `uip codedagent init` on resume."
        )
    try:
        ep_payload = json.loads(ENTRY_POINTS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"entry-points.json is not valid JSON: {exc}")
    serialized = json.dumps(ep_payload)
    if "mood" not in serialized:
        fail("entry-points.json does not advertise the original `mood` field — schema may have been clobbered")
    if "confidence" not in serialized:
        fail(
            "entry-points.json does not advertise the new `confidence` field. "
            "Either the edit was missing, or `uip codedagent init` was not re-run "
            "after the edit to pick up the new output."
        )
    print("OK: entry-points.json advertises both `mood` and `confidence`")

    if not MAIN.is_file():
        fail(f"missing {MAIN}")
    main_text = MAIN.read_text(encoding="utf-8")
    if "mood" not in main_text:
        fail(
            "main.py no longer mentions `mood`. The resume must edit IN PLACE; "
            "the original feature must survive."
        )
    print("OK: main.py preserves the original `mood` field")

    if "confidence" not in main_text:
        fail("main.py does not contain the new `confidence` field — the feature was not added")
    print("OK: main.py adds the new `confidence` field")

    if not re.search(r"^\s*graph\s*=\s*", main_text, re.M):
        fail("main.py no longer exports a top-level `graph =` variable — LangGraph entrypoint broken")
    print("OK: top-level `graph` variable still exported")

    if not PYPROJECT.is_file():
        fail(f"missing {PYPROJECT}")
    if re.search(r"^\s*\[build-system\]", PYPROJECT.read_text(encoding="utf-8"), re.M):
        fail("pyproject.toml gained a [build-system] section — Critical Rule C1 violation")
    print("OK: pyproject.toml still has no [build-system] section")

    print("OK: existing-coded resume completed without clobbering")


if __name__ == "__main__":
    main()
