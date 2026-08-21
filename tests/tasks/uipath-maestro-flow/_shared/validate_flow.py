#!/usr/bin/env python3
"""Locate emitted ``.flow`` files and run ``uip maestro flow validate``.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-maestro-flow/_shared/validate_flow.py

Why this exists — a hardcoded ``<Name>/<Name>/<Name>.flow`` path in a success
criterion is brittle: ``uip maestro flow init <Name>`` scaffolds a
``<Name>Solution/`` wrapper directory, so the real path is
``<Name>Solution/<Name>/<Name>.flow`` — not ``<Name>/<Name>/<Name>.flow``.
The hardcoded command then fails with "File not found" even though the flow
itself is valid (observed on skill-flow-loop-multiply: criterion scored 0.0
purely on the path, while the flow validated fine when addressed correctly).

Discovery prefers the lone ``project.uiproj`` whose manifest declares
``ProjectType="Flow"`` and validates every flow under it. If no project exists,
it accepts one unambiguous root-level SDK emit instead. Exit 0 iff every selected
file validates; otherwise propagate the failing exit code.
"""

from __future__ import annotations

import subprocess
import sys

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from flow_check import find_flow_files  # noqa: E402


def main() -> int:
    flows = find_flow_files()

    rc = 0
    for flow in flows:
        print(f"Validating {flow}")
        result = subprocess.run(
            ["uip", "maestro", "flow", "validate", flow, "--output", "json"],
            capture_output=True,
            text=True,
        )
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        if result.returncode != 0:
            rc = result.returncode or 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
