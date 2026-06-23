#!/usr/bin/env python3
"""Local Workspace iteration check — preserve SW-owned files, edit the graph, run both branches.

Asserts:
  1. `.sw-path-marker` and `.local/folder.lock` are still present (untouched).
  2. `project.uiproj` still exists (Local Workspace anti-pattern: do not delete it).
  3. `main.py` declares a `category` field on the LangGraph output schema.
  4. `entry-points.json` advertises a `category` output (init regenerated the schema).
  5. `outputs.json` captured a `tiny` run for value=2 and a `huge` run for value=150.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "GateSol"
AGENT_DIR = ROOT / "gate-agent"
MAIN = AGENT_DIR / "main.py"
ENTRY_POINTS = AGENT_DIR / "entry-points.json"
PROJECT_UIPROJ = AGENT_DIR / "project.uiproj"
SW_MARKER = ROOT / ".sw-path-marker"
FOLDER_LOCK = ROOT / ".local" / "folder.lock"
OUTPUTS = AGENT_DIR / "outputs.json"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def main() -> None:
    # --- Studio Web ownership preserved ---
    if not SW_MARKER.is_file():
        fail(f"missing Studio Web detection marker {SW_MARKER} — Local Workspace identity lost")
    if not FOLDER_LOCK.is_file():
        fail(f"missing Studio Web folder lock {FOLDER_LOCK} — Local Workspace identity lost")
    if not PROJECT_UIPROJ.is_file():
        fail(f"{PROJECT_UIPROJ} missing — Local Workspace anti-pattern: do not delete project.uiproj")
    print("OK: Studio Web markers and project.uiproj are intact")

    # --- main.py has the edit ---
    if not MAIN.is_file():
        fail(f"missing {MAIN}")
    main_text = MAIN.read_text(encoding="utf-8")
    if "category" not in main_text:
        fail("main.py does not mention a `category` field — the requested behavior is missing")
    print("OK: main.py declares the `category` field")

    # --- entry-points.json regenerated to advertise the new output ---
    if not ENTRY_POINTS.is_file():
        fail(f"missing {ENTRY_POINTS}")
    try:
        ep_payload = json.loads(ENTRY_POINTS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"entry-points.json is not valid JSON: {exc}")
    serialized = json.dumps(ep_payload)
    if "category" not in serialized:
        fail(
            "entry-points.json does not advertise `category` — schema was not regenerated "
            "after the edit (run `uip codedagent init` to refresh it)"
        )
    print("OK: entry-points.json advertises the new `category` output")

    # --- outputs.json captured both edge-case runs ---
    if not OUTPUTS.is_file():
        fail(f"missing {OUTPUTS} — agent did not save the verification runs")
    try:
        outs = json.loads(OUTPUTS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"outputs.json is not valid JSON: {exc}")
    flat = json.dumps(outs).lower()
    if "tiny" not in flat:
        fail("outputs.json does not mention a `tiny` result — value=2 run not captured or wrong branch")
    if "huge" not in flat:
        fail("outputs.json does not mention a `huge` result — value=150 run not captured or wrong branch")
    print("OK: outputs.json captured both `tiny` and `huge` branches")

    print("OK: Local Workspace iteration completed without violating ownership invariants")


if __name__ == "__main__":
    main()
