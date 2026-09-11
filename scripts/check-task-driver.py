#!/usr/bin/env python3
"""Two static gates over the coder-eval task and experiment corpus.

Gate 1: no task YAML pins ``sandbox.driver: tempdir``
-----------------------------------------------------

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

Gate 2: experiment hook commands must be a single line
------------------------------------------------------

On Windows coder_eval runs hooks through ``create_subprocess_shell``, i.e.
cmd.exe, which parses only the FIRST line it is handed. A ``|-`` block scalar
therefore drops the rest, and ``PreRunCommand.fail_on_error`` defaults to
``True``, so an unparseable ``pre_run`` ERRORs every task in the split (skills
#2756, fixed by #3116). Just the newline rule: no false positives, no config.
It does not detect one-line POSIX sh; see the known-gap test for that cost.

Scope is what cmd.exe can reach: every experiment hook (they run for all tasks,
including the Windows split) plus the hooks of ``windows``-tagged tasks. A task
without that tag never runs on Windows, so its hooks are left alone.

Usage:
    python3 scripts/check-task-driver.py                              # tests/tasks
    python3 scripts/check-task-driver.py tests/tasks tests/experiments  # both gates

Exit codes:
    0 — both gates pass
    1 — one or more violations (paths printed, with GitHub annotations)
"""

from __future__ import annotations

import re
import sys
from collections.abc import Iterator
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


def _iter_hook_commands(doc: dict) -> Iterator[tuple[str, str]]:
    """Yield ``(yaml_path, command)`` for every pre_run/post_run command."""
    scopes: list[tuple[str, dict]] = [("", doc)]
    for key, value in doc.items():
        if isinstance(value, dict):
            scopes.append((key, value))
        elif isinstance(value, list):  # variants[] holds per-variant overrides
            scopes.extend(
                (f"{key}[{i}]", v) for i, v in enumerate(value) if isinstance(v, dict)
            )
    for scope_name, scope in scopes:
        for hook in ("pre_run", "post_run"):
            steps = scope.get(hook)
            if not isinstance(steps, list):
                continue
            prefix = f"{scope_name}.{hook}" if scope_name else hook
            for index, step in enumerate(steps):
                if isinstance(step, dict) and isinstance(step.get("command"), str):
                    yield f"{prefix}[{index}].command", step["command"]


def _hook_line_number(path: Path, command: str) -> int:
    """1-indexed line where ``command`` starts in the raw file (0 if not found)."""
    needle = command.strip().splitlines()[0].strip()
    if len(needle) < 8:
        return 0
    for n, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1):
        if needle in line:
            return n
    return 0


def main(argv: list[str]) -> int:
    offenders: list[tuple[Path, int]] = []
    docker_pins: list[Path] = []
    multi_line: list[tuple[Path, int, str]] = []
    hooks_checked = 0

    for path in _iter_task_yamls(argv):
        try:
            doc = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            # Malformed YAML is another gate's problem; don't mask it as a pass
            # but don't crash this check either.
            continue
        if not isinstance(doc, dict):
            continue

        tags = doc.get("tags")
        if (
            "experiment_id" in doc
            or "variants" in doc
            or (isinstance(tags, list) and "windows" in tags)
        ):
            for yaml_path, command in _iter_hook_commands(doc):
                hooks_checked += 1
                if len(command.strip().splitlines()) > 1:
                    multi_line.append((path, _hook_line_number(path, command), yaml_path))

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

    rc = 0

    if multi_line:
        rc = 1
        print(f"FAIL — {len(multi_line)} Windows-reachable hook command(s) span multiple lines:\n")
        for path, line, yaml_path in multi_line:
            rel = _rel(path)
            loc = f"{rel}:{line}" if line else rel
            print(f"::error file={rel},line={line}::{yaml_path} spans multiple lines")
            print(f"  {loc}  ({yaml_path})")
        print()
        print(
            "cmd.exe on the Windows split parses only the first line, so the rest is\n"
            "dropped and an unparseable pre_run ERRORs every task (skills #2756/#3116).\n"
            "Collapse it to one line; if it is POSIX sh that must not run on Windows,\n"
            "prefix it with `:; ` too. See tests/experiments/nightly.yaml."
        )
        print()
    elif hooks_checked:
        print(f"OK — {hooks_checked} Windows-reachable hook command(s) are single-line.")

    if not offenders:
        print("OK — no task pins `sandbox.driver: tempdir`.")
        return rc

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
