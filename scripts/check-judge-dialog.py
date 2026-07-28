#!/usr/bin/env python3
"""Fail if a simulated troubleshoot task grades its ``llm_judge`` on the last turn only.

Why this matters
----------------
With ``simulation.enabled: true`` the simulated user keeps talking after the
agent has delivered its diagnosis ("thanks, I'll get an admin to grant that").
The agent's *final* turn is then a one-line acknowledgement - "Will do.",
"You're welcome." - while the real diagnosis sits two turns back.

An ``llm_judge`` criterion that sets ``include_agent_output: true`` without
``include_dialog: true`` receives ONLY that final turn. The judge sees no
diagnosis and scores 0.00, so a fully correct investigation fails the task.
Six troubleshoot tasks failed exactly this way in the 2026-07-28 nightly, each
with a correct root cause in turn 1.

``include_dialog: true`` hands the judge the whole user<->agent dialog, so the
diagnosis is graded wherever in the conversation it landed.

Scope
-----
Checks the paths it is given, so CI can scope it to the task YAMLs a PR touches
(existing tasks predating this rule are not retroactively blocked). The gate is
wired to ``tests/tasks/uipath-troubleshoot``; widen the workflow's path filter
to cover other skills.

A task is an offender when ALL of these hold:
  1. ``simulation.enabled`` is true (multi-turn - a last-turn-only grade can miss
     the diagnosis; single-turn tasks are fine, their last turn is the answer).
  2. It has an ``llm_judge`` criterion with ``include_agent_output: true``.
  3. That criterion does not set ``include_dialog: true``.

Usage:
    python3 scripts/check-judge-dialog.py <task.yaml> [<task.yaml> ...]
    python3 scripts/check-judge-dialog.py tests/tasks/uipath-troubleshoot

Exit codes:
    0 - no offenders (also when no paths are given, e.g. a PR touching no tasks)
    1 - one or more criteria grade on the last turn only (paths printed)
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

_JUDGE_LINE = re.compile(r"^\s*-\s*type:\s*llm_judge\s*$")


def _iter_task_yamls(args: list[str]) -> list[Path]:
    files: list[Path] = []
    for arg in args:
        path = Path(arg)
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(path.rglob("task.yaml")))
    return files


def _rel(path: Path) -> str:
    """Repo-relative path string, robust to relative/absolute inputs and cwd.

    Always forward-slashed - the GitHub Actions annotation format requires it.
    """
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _judge_line_numbers(path: Path) -> list[int]:
    """1-indexed lines of each `- type: llm_judge`, in document order."""
    return [
        n
        for n, line in enumerate(path.read_text(errors="ignore").splitlines(), start=1)
        if _JUDGE_LINE.match(line)
    ]


def _offending_criteria(doc: dict) -> list[int]:
    """Indices (among llm_judge criteria, in order) that grade the last turn only."""
    simulation = doc.get("simulation")
    if not isinstance(simulation, dict) or simulation.get("enabled") is not True:
        return []

    criteria = doc.get("success_criteria")
    if not isinstance(criteria, list):
        return []

    offenders: list[int] = []
    judge_index = 0
    for criterion in criteria:
        if not isinstance(criterion, dict) or criterion.get("type") != "llm_judge":
            continue
        if criterion.get("include_agent_output") is True and (
            criterion.get("include_dialog") is not True
        ):
            offenders.append(judge_index)
        judge_index += 1
    return offenders


def main(argv: list[str]) -> int:
    offenders: list[tuple[Path, int]] = []

    for path in _iter_task_yamls(argv):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeDecodeError):
            # Malformed YAML is another gate's problem; don't mask it as a pass
            # but don't crash this check either.
            continue
        if not isinstance(doc, dict):
            continue
        judge_lines = _judge_line_numbers(path)
        for index in _offending_criteria(doc):
            line = judge_lines[index] if index < len(judge_lines) else 0
            offenders.append((path, line))

    if not offenders:
        print("OK - every simulated task's llm_judge grades the full dialog.")
        return 0

    noun, verb = ("criterion", "grades") if len(offenders) == 1 else ("criteria", "grade")
    print(f"FAIL - {len(offenders)} llm_judge {noun} {verb} the last turn only:\n")
    for path, line in offenders:
        rel = _rel(path)
        loc = f"{rel}:{line}" if line else rel
        # GitHub Actions annotation (rendered inline on the PR when run in CI).
        print(
            f"::error file={rel},line={line}::llm_judge sets include_agent_output "
            "without include_dialog on a simulated task - add `include_dialog: true`"
        )
        print(f"  {loc}")
    print()
    print(
        "The simulator keeps talking after the diagnosis lands, so the agent's final\n"
        "turn is usually an acknowledgement ('Will do.'). A judge given only that turn\n"
        "scores a correct investigation 0.00.\n\n"
        "Add `include_dialog: true` next to `include_agent_output: true` in each\n"
        "criterion above - see the docstring in scripts/check-judge-dialog.py."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
