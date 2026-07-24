#!/usr/bin/env python3
"""Fail if any coder-eval task YAML pins ``sandbox.driver: tempdir``.

The sandbox driver is decided by the run environment, NOT by the task:

  - The Linux nightly slice runs every non-windows task under ``driver: docker``
    (the ``skills-image`` bakes the full ``uip`` CLI + all tool plugins). The
    experiment config (``tests/experiments/nightly.yaml``) sets that default.
  - The Windows slice selects tasks by the ``windows`` tag and forces
    ``--driver tempdir`` on the CLI (which wins over any YAML). Windows tasks
    therefore do NOT need — and must not rely on — a YAML driver override.

A task that pins ``driver: tempdir`` opts out of the docker image and runs on
the bare host, where the tool plugins are NOT installed. Any task that then
calls a tool-backed command (e.g. ``uip maestro flow validate`` needs
``@uipath/maestro-tool``) fails with "No compatible version found", scoring
zero on an otherwise-correct run. This gate blocks that footgun.

If a task genuinely needs the Windows toolchain, tag it ``windows`` — do not
pin the driver.

Usage:
    python3 scripts/check-task-driver.py                 # scans tests/tasks
    python3 scripts/check-task-driver.py tests/tasks ...  # scan given roots/files

Exit codes:
    0 — no task pins ``driver: tempdir``
    1 — one or more tasks pin ``driver: tempdir`` (paths printed)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required. Install with: pip install pyyaml")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO_ROOT / "tests" / "tasks"

_DRIVER_LINE = re.compile(r"^\s*driver:\s*tempdir\s*$")


def _iter_task_yamls(args: list[str]) -> list[Path]:
    roots = [Path(a) for a in args] if args else [DEFAULT_ROOT]
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        else:
            files.extend(sorted(root.rglob("*.yaml")))
            files.extend(sorted(root.rglob("*.yml")))
    return files


def _rel(path: Path) -> str:
    """Repo-relative path string, robust to relative/absolute inputs and cwd."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _driver_line_number(path: Path) -> int:
    """1-indexed line of the offending `driver: tempdir` (0 if not found textually)."""
    for n, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        if _DRIVER_LINE.match(line):
            return n
    return 0


def main(argv: list[str]) -> int:
    offenders: list[tuple[Path, int]] = []
    docker_pins: list[Path] = []

    for path in _iter_task_yamls(argv):
        try:
            doc = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            # Malformed YAML is another gate's problem; don't mask it as a pass
            # but don't crash this check either.
            continue
        if not isinstance(doc, dict):
            continue
        sandbox = doc.get("sandbox")
        if not isinstance(sandbox, dict):
            continue
        driver = sandbox.get("driver")
        if driver == "tempdir":
            offenders.append((path, _driver_line_number(path)))
        elif driver == "docker":
            docker_pins.append(path)

    if docker_pins:
        print(
            f"note: {len(docker_pins)} task(s) pin `sandbox.driver: docker` (redundant with "
            "the Linux default, harmless — not blocked):"
        )
        for p in docker_pins:
            print(f"  {_rel(p)}")
        print()

    if not offenders:
        print("OK — no task pins `sandbox.driver: tempdir`.")
        return 0

    print(f"FAIL — {len(offenders)} task(s) pin `sandbox.driver: tempdir`:\n")
    for path, line in offenders:
        rel = _rel(path)
        loc = f"{rel}:{line}" if line else rel
        # GitHub Actions annotation (rendered inline on the PR when run in CI).
        print(f"::error file={rel},line={line}::Task pins sandbox.driver: tempdir")
        print(f"  {loc}")
    print()
    print(
        "The sandbox driver is decided by the run environment, not the task.\n"
        "Remove the `driver: tempdir` line (delete the `sandbox:` block if it becomes empty).\n"
        "If the task needs the Windows toolchain, tag it `windows` instead — see the\n"
        "docstring in scripts/check-task-driver.py for the full rationale."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
