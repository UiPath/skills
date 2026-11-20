#!/usr/bin/env python3
"""Grade that a new process landed in a fresh solution, not a taken one.

Usage (cwd = sandbox root): check_fresh_solution.py <ProcessName> --taken <SolutionDir>

The sandbox already holds <SolutionDir>, a solution with its own registered
project, under the name SKILL.md's default for a new solution
(`<ProcessName>Solution`). With nobody to answer, the skill puts the project in
a new solution under a free name. Passes when some `.uipx` outside the taken
directory registers the directory holding `<ProcessName>.bpmn`, and no
`<ProcessName>.bpmn` sits under the taken directory.

The taken `.uipx` keeping its `SolutionId` and registrations is graded by the
task's json_check, not here: `uip solution init` over it resets both, and a
bare `bpmn init` from the root appends to it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    sys.exit(1)


def registered_dirs(uipx: Path) -> set[Path]:
    """Project directories a `.uipx` registers, resolved against its folder."""
    try:
        value = json.loads(uipx.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    projects = value.get("Projects") if isinstance(value, dict) else None
    dirs = set()
    for project in projects if isinstance(projects, list) else []:
        if not isinstance(project, dict):
            continue
        if str(project.get("Type", "")).lower() != "processorchestration":
            continue
        rel = project.get("ProjectRelativePath")
        if isinstance(rel, str) and rel:
            dirs.add((uipx.parent / rel).parent.resolve())
    return dirs


def check(root: Path, process: str, taken: str) -> str:
    root = root.resolve()
    taken_dir = root / taken
    bpmns = [
        path.resolve()
        for path in root.rglob("*.bpmn")
        if path.name.lower() == f"{process}.bpmn".lower()
    ]
    if not bpmns:
        fail(f"no {process}.bpmn was created")
    inside = [path for path in bpmns if taken_dir in path.parents]
    if inside:
        fail(f"{process}.bpmn was put in the existing {taken}: {inside[0]}")
    for uipx in sorted(root.rglob("*.uipx")):
        if taken_dir in uipx.parents:
            continue
        dirs = registered_dirs(uipx)
        for bpmn in bpmns:
            if bpmn.parent in dirs:
                return f"OK: {uipx.relative_to(root)} registers {bpmn.relative_to(root)}"
    fail(f"no solution other than {taken} registers the {process} project")
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("process")
    parser.add_argument("--taken", required=True)
    args = parser.parse_args()
    print(check(Path.cwd(), args.process, args.taken))


if __name__ == "__main__":
    main()
