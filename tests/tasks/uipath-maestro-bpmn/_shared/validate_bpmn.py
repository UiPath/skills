#!/usr/bin/env python3
"""Locate emitted ``.bpmn`` files and run ``uip maestro bpmn validate`` on every one.

Usage (from a task's run_command, cwd = sandbox root):

    python3 $REFERENCE_DIR/_shared/validate_bpmn.py

Plays the role ``uipath-maestro-flow/_shared/validate_flow.py`` plays for the
flow suite. Exit 0 iff at least one file was found and EVERY selected file
validates; otherwise exit 1 after naming the failing file.

Why not ``for f in $(find …); do validate && exit 0; done``: that loop passes
as soon as ANY file validates. ``uip maestro bpmn init`` leaves a valid
scaffold behind, so a sandbox holding a valid scaffold and an invalid real
process read as a pass (CI run 35501830119, devcon_expense_approval). Flow's
helper validates every flow under the project and fails on the first bad one;
this does the same.

Discovery: EVERY ``.bpmn`` under the sandbox (excluding ``node_modules`` and
tool caches). Not only project-registered files: on that same CI run the
agent's real process sat outside the initialised project while the valid
scaffold sat inside it, so a project-scoped rule still read as a pass.
``validate`` is offline, so one attempt per file with a fixed cap is enough.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PER_FILE_TIMEOUT = 120
SKIP_PARTS = {"node_modules", ".npm-prefix", ".venv"}


def _bpmn_files() -> list[Path]:
    root = Path.cwd()
    candidates = [
        p for p in root.rglob("*.bpmn") if not (SKIP_PARTS & set(p.parts))
    ]
    return sorted(candidates)


def main() -> int:
    files = _bpmn_files()
    if not files:
        print("FAIL: no .bpmn file found under the sandbox", file=sys.stderr)
        return 1
    rc = 0
    for path in files:
        print(f"Validating {path}", flush=True)
        try:
            proc = subprocess.run(
                ["uip", "maestro", "bpmn", "validate", str(path), "--output", "json"],
                capture_output=True,
                text=True,
                timeout=PER_FILE_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            print(f"FAIL: validate timed out after {PER_FILE_TIMEOUT}s: {path}", file=sys.stderr)
            rc = 1
            continue
        if proc.returncode != 0:
            tail = (proc.stdout or proc.stderr or "").strip()[-1500:]
            print(f"FAIL: validate failed for {path}\n{tail}", file=sys.stderr)
            rc = 1
    if rc == 0:
        print(f"OK: {len(files)} .bpmn file(s) validate")
    return rc


if __name__ == "__main__":
    sys.exit(main())
