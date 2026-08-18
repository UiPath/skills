#!/usr/bin/env python3
"""Grade the SDD's `Activation Mode` → task-entry-rule mapping.

`sdd_check.py` validates that a task-entry rule is a *legal* member of the enum, so
`current-stage-entered`, `runs-sequentially`, and `selected-tasks-completed(...)` all pass
it equally. Legality is not intent. A plain in-order run written as
`current-stage-entered` on the first task plus `selected-tasks-completed("<previous>")` on
its follower compiles to the same scheduler primitives, so nothing downstream complains —
but it is wrong in two ways that only show up later:

* Studio Web renders every task in the stage as "Runs out of sequence".
* A non-sequential task's completion is **not** reset when its stage is re-entered, so a
  re-entered stage cannot re-run it. A sequential task's is.

This checker grades the choice. Exit 1 on any violation, 0 when every ordered run uses
`runs-sequentially`.

Usage:  python3 check_sequential_activation.py [path-to-sdd]
"""
from __future__ import annotations

import glob
import re
import sys

# Modes whose entry rule must be `runs-sequentially`.
SEQUENTIAL_MODES = {"sequential", "parallel-after-predecessor"}

STAGE_RE = re.compile(r"^###\s+(?:Stage\s+[^:]*|Secondary Stage):\s*(.+)$")
TASK_RE = re.compile(r"^#{4,5}\s+Task\s+[\d.]+:\s*(.+)$")
MODE_RE = re.compile(r"^\*\*Activation Mode:\*\*\s*(.+)$")


def find_sdd(argv: list[str]) -> str | None:
    if len(argv) > 1:
        return argv[1]
    for pat in ("sdd.md", "sdd.draft.md", "*sdd*.md", "**/sdd.md", "**/sdd.draft.md", "**/*sdd*.md"):
        hits = sorted(glob.glob(pat, recursive=True))
        if hits:
            return hits[0]
    return None


def parse_tasks(text: str) -> list[dict]:
    """Task records in document order, each with stage, name, mode, and entry rules."""
    tasks: list[dict] = []
    stage: str | None = None
    cur: dict | None = None
    in_entry = False

    for raw in text.splitlines():
        s = raw.strip()

        m = STAGE_RE.match(s)
        if m:
            stage, cur, in_entry = m.group(1).strip(), None, False
            continue

        m = TASK_RE.match(s)
        if m:
            cur = {"stage": stage, "name": m.group(1).strip(), "mode": None, "when": []}
            tasks.append(cur)
            in_entry = False
            continue

        if cur is None:
            continue

        m = MODE_RE.match(s)
        if m:
            cur["mode"] = m.group(1).strip().strip("`").lower()
            continue

        if s.startswith("**Entry Condition"):
            in_entry = True
            continue
        # Any other bold field, heading, or horizontal rule closes the entry table.
        if s.startswith("**") or s.startswith("#") or s == "---":
            in_entry = False
            continue

        if in_entry and s.startswith("|"):
            cells = [c.strip() for c in s.strip().strip("|").split("|")]
            if not cells or cells[0].upper() == "WHEN":
                continue
            if not cells[0] or set(cells[0]) <= set("-: "):
                continue
            cur["when"].append(cells[0].strip("`"))

    return tasks


def rule_token(cell: str) -> str:
    m = re.match(r"^([a-z-]+)", cell.strip().strip("`").lower())
    return m.group(1) if m else ""


def selected_targets(cell: str) -> list[str]:
    return [t.strip() for t in re.findall(r'"([^"]+)"', cell)]


def violations(tasks: list[dict]) -> list[str]:
    """One finding per offending task, most specific message first.

    A task can trip several clauses for a single mistake: a sequential follower written as
    `selected-tasks-completed("<previous>")` both lacks `runs-sequentially` and names its
    predecessor. Reporting each clause separately inflates the count and makes one fix look
    like several, so the unit here is the task, not the clause.
    """
    out: list[str] = []
    by_stage: dict[str, list[dict]] = {}
    for t in tasks:
        by_stage.setdefault(t["stage"] or "?", []).append(t)

    for stage, group in by_stage.items():
        names = [t["name"] for t in group]
        for i, t in enumerate(group):
            mode = t["mode"] or ""
            rules = [rule_token(c) for c in t["when"]]
            label = f'{stage} / {t["name"]}'
            finding = None

            # Most specific: an immediate-predecessor selector IS a sequential run,
            # whatever the declared mode says.
            for cell in t["when"]:
                if rule_token(cell) != "selected-tasks-completed":
                    continue
                targets = selected_targets(cell)
                if len(targets) == 1 and i > 0 and targets[0] == names[i - 1]:
                    finding = (
                        f'{label}: selected-tasks-completed("{targets[0]}") selects the '
                        f"immediately previous task - that is a sequential run. Use "
                        f"runs-sequentially; selected-tasks-completed is for fan-in, branch "
                        f"convergence, condition routing, or a non-immediate dependency."
                    )
                    break

            if finding is None and mode in SEQUENTIAL_MODES:
                if "runs-sequentially" not in rules:
                    finding = (
                        f'{label}: Activation Mode "{mode}" but entry rule is '
                        f'{rules or ["(none)"]}. A sequential task carries runs-sequentially, '
                        f"including the first task in the run."
                    )
                elif "current-stage-entered" in rules:
                    finding = (
                        f"{label}: sequential task must not also carry current-stage-entered - "
                        f"runs-sequentially already means 'stage entered' on the first task set."
                    )

            if finding:
                out.append(finding)
    return out


def main(argv: list[str]) -> int:
    path = find_sdd(argv)
    if not path:
        print("FAIL: no sdd.md / sdd.draft.md found", file=sys.stderr)
        return 1

    try:
        text = open(path, encoding="utf-8").read()
    except OSError as exc:
        print(f"FAIL: cannot read {path}: {exc}", file=sys.stderr)
        return 1

    tasks = parse_tasks(text)
    if not tasks:
        print(f"FAIL: parsed zero task detail blocks from {path}", file=sys.stderr)
        return 1

    # Unfilled template text is not a design; grading it would pass vacuously.
    if any((t["mode"] or "").startswith("<") for t in tasks):
        print(f"FAIL: {path} still carries unfilled Activation Mode placeholders", file=sys.stderr)
        return 1

    seq = [t for t in tasks if (t["mode"] or "") in SEQUENTIAL_MODES]
    problems = violations(tasks)

    print(f"{path}: {len(tasks)} tasks, {len(seq)} in a sequential mode")
    if not problems:
        print("PASS: every ordered run uses runs-sequentially")
        return 0

    print(f"\nFAIL: {len(problems)} sequential-activation violation(s):", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    print(
        "\n  See case-sdd-template.md § Entry Condition — Activation Mode decides WHEN.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
