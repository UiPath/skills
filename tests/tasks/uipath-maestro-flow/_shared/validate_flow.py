#!/usr/bin/env python3
"""Locate the Flow project's ``.flow`` file dynamically and run
``uip maestro flow validate`` on it.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-maestro-flow/_shared/validate_flow.py

Why this exists — a hardcoded ``<Name>/<Name>/<Name>.flow`` path in a success
criterion is brittle: ``uip maestro flow init <Name>`` scaffolds a
``<Name>Solution/`` wrapper directory, so the real path is
``<Name>Solution/<Name>/<Name>.flow`` — not ``<Name>/<Name>/<Name>.flow``.
The hardcoded command then fails with "File not found" even though the flow
itself is valid (observed on skill-flow-loop-multiply: criterion scored 0.0
purely on the path, while the flow validated fine when addressed correctly).

Discovery mirrors the ``check_*.py`` execution checks: find the lone
``project.uiproj`` whose manifest declares ``ProjectType="Flow"`` (via
:func:`flow_check.find_project_dir`), then validate every ``.flow`` file under
it. Exit 0 iff every file validates; otherwise propagate the failing exit code.
"""

from __future__ import annotations

import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import find_project_dir  # noqa: E402


def main() -> int:
    project_dir = find_project_dir()
    flows = sorted(glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True))
    if not flows:
        print(f"FAIL: No .flow file found under {project_dir}", file=sys.stderr)
        return 1

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
