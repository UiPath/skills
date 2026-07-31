#!/usr/bin/env python3
"""Locate the Flow project's ``.flow`` file dynamically and assert its content.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $SKILLS_REPO_PATH/tests/tasks/uipath-maestro-flow/_shared/flow_contains.py
    python3 .../flow_contains.py '"uipath.human-in-the-loop.quick-form"' '"end"'

With no arguments this asserts only that a ``.flow`` file exists. Each argument
is a substring that must appear in at least one discovered ``.flow`` file.

Why this exists — the ``file_exists`` / ``file_contains`` criterion types take a
literal ``path`` with no glob support, so tasks hardcode
``<Name>/<Name>/<Name>.flow``. That path is brittle: ``uip maestro flow init``
scaffolds a wrapper solution directory whose name the prompt does not pin, so a
correct flow lands at e.g. ``<Name>Solution/<Name>/<Name>.flow`` and the
criterion scores 0.0 purely on the path while the flow itself validates. This is
the same failure ``validate_flow.py`` was added to fix (#2213); it reuses that
module's discovery so both criteria address the same file.
"""

from __future__ import annotations

import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flow_check import find_project_dir  # noqa: E402


def main(argv: list[str]) -> int:
    project_dir = find_project_dir()
    flows = sorted(glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True))
    if not flows:
        print(f"FAIL: No .flow file found under {project_dir}", file=sys.stderr)
        return 1

    print(f"Found {len(flows)} .flow file(s): {', '.join(flows)}")
    if not argv:
        return 0

    bodies = {path: open(path, encoding="utf-8").read() for path in flows}
    missing = [s for s in argv if not any(s in body for body in bodies.values())]
    for s in argv:
        print(f"{'MISSING' if s in missing else 'OK     '} {s}")
    if missing:
        print(
            f"FAIL: {len(missing)} substring(s) absent from every discovered .flow file",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
