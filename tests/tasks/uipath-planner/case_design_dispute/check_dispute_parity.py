#!/usr/bin/env python3
"""Deterministic parity checks on the card-dispute case design SDD.

The dispute brief is built around on-demand human work: three actions any
handler may take at any time, a cardholder who can drop the dispute during any
active phase, and a senior review that parks until a person picks the next
phase. Those are exactly the shapes where an authoring mistake still produces a
document that reads fine and a case that stalls, so each one is graded here
rather than left to the judge.

Usage:  check_dispute_parity.py <check-name> [sdd-file ...]

Checks:
  adhoc-stage-exit      no stage-exit rule selects an adhoc task
  ondemand-actions      the at-any-time actions are adhoc and not required
  wait-for-user-pairing wait-for-user exits and user-selected-stage entries pair up
  dropped-terminal      a dropped/withdrawn terminal lane exists and is entered
  send-back-loop        the analyst send-back returns to the checking phase
"""

from __future__ import annotations

import glob
import re
import sys

STAGE_RE = re.compile(r"^###\s+(?:Stage \d+|Exception Stage|Secondary Stage)\s*:\s*(.+)$")
TASK_RE = re.compile(r"^#####\s+Task\s+S?[\d.]+\s*:\s*(.+)$")
ACTIVATION_RE = re.compile(r"^\*\*Activation Mode:\*\*\s*`?([\w-]+)", re.I)
ENTRY_MARKER_RE = re.compile(r"^\*\*Entry Condition", re.I)
EXIT_HEADING_RE = re.compile(r"^####\s+.*Exit Conditions", re.I)
ENTRY_HEADING_RE = re.compile(r"^####\s+.*Entry Conditions", re.I)
ENVELOPE_RE = re.compile(r"^\*\*Task envelope\*\*", re.I)
TASKS_HEADING_RE = re.compile(r"^####\s+Tasks\s*$", re.I)
RULE_TOKEN_RE = re.compile(r"`?\s*([a-z][a-z]+(?:-[a-z]+)*)")
QUOTED_RE = re.compile(r"[\"“]([^\"“”]+)[\"”]")


def _clean(value: str) -> str:
    """Strip backticks, quotes and a trailing parenthetical from a display name."""
    text = re.sub(r"\s*\([^)]*\)\s*$", "", value.strip().strip("`"))
    return text.strip().strip("\"'").strip()


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return not cells or not cells[0] or set(cells[0]) <= set("-: ")


class Sdd:
    """Everything the checks need, parsed once from the SDD markdown."""

    def __init__(self, text: str, source: str):
        self.source = source
        self.adhoc_tasks: dict[str, str] = {}          # task name -> owning stage
        self.task_required: dict[str, str] = {}        # task name -> Required cell
        self.stage_exit_selectors: list[tuple[str, str, int]] = []  # (task, stage, line)
        self.exit_types: set[str] = set()
        self.stage_entry_rules: set[str] = set()
        self.stages: list[str] = []

        stage = "case"
        task: str | None = None
        section: str | None = None
        envelope_pending = False
        summary_cols: tuple[int | None, int | None] = (None, None)

        for line_no, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()

            stage_match = STAGE_RE.match(line)
            if stage_match:
                stage = _clean(stage_match.group(1)) or "case"
                self.stages.append(stage)
                task, section, envelope_pending = None, None, False
                continue

            task_match = TASK_RE.match(line)
            if task_match:
                task = _clean(task_match.group(1))
                section, envelope_pending = None, False
                continue

            if TASKS_HEADING_RE.match(line):
                section, task = "tasks-summary", None
                continue
            if EXIT_HEADING_RE.match(line):
                section, task = "stage-exit", None
                continue
            if ENTRY_HEADING_RE.match(line):
                section, task = "stage-entry", None
                continue
            if ENTRY_MARKER_RE.match(line):
                section = "task-entry"
                continue
            if ENVELOPE_RE.match(line):
                envelope_pending = True
                continue
            if line.startswith("#"):
                task, section, envelope_pending = None, None, False
                continue

            activation = ACTIVATION_RE.match(line)
            if activation and task:
                if activation.group(1).lower() == "adhoc":
                    self.adhoc_tasks.setdefault(task, stage)
                continue

            if not line.startswith("|"):
                continue

            cells = _cells(line)
            header = [c.strip().lower() for c in cells]
            if _is_separator(cells) or cells[0].upper() in {"WHEN", "REQUIRED", "#"}:
                if envelope_pending and cells and cells[0].upper() == "REQUIRED":
                    section = "envelope"
                if section == "tasks-summary" and "required" in header:
                    summary_cols = (
                        next((i for i, h in enumerate(header) if "task name" in h or h == "task"), None),
                        next((i for i, h in enumerate(header) if h == "required"), None),
                    )
                continue

            if section == "tasks-summary" and all(i is not None for i in summary_cols):
                name_idx, req_idx = summary_cols
                if max(name_idx, req_idx) < len(cells):
                    self.task_required.setdefault(_clean(cells[name_idx]), cells[req_idx])
                continue

            if section == "envelope" and task and cells:
                self.task_required.setdefault(task, cells[0])
                envelope_pending = False
                continue

            token = RULE_TOKEN_RE.match(cells[0])
            rule = token.group(1) if token else ""

            if section == "task-entry" and task and rule == "adhoc":
                self.adhoc_tasks.setdefault(task, stage)
            elif section == "stage-entry":
                self.stage_entry_rules.add(rule)
            elif section == "stage-exit":
                if rule == "selected-tasks-completed":
                    for name in QUOTED_RE.findall(cells[0]):
                        self.stage_exit_selectors.append((_clean(name), stage, line_no))
                for cell in cells[1:]:
                    for exit_type in ("return-to-origin", "wait-for-user", "exit-only"):
                        if exit_type in cell:
                            self.exit_types.add(exit_type)


def _load(paths: list[str]) -> Sdd:
    candidates = [p for p in paths if p] or sorted(glob.glob("*sdd*.md"))
    for path in candidates:
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        if text.strip():
            return Sdd(text, path)
    sys.exit("FAIL: no SDD markdown found to check")


def check_adhoc_stage_exit(sdd: Sdd) -> list[str]:
    return [
        f"stage-exit rule in {stage!r} selects adhoc task {task!r} ({sdd.source}:{line}) — "
        "an adhoc task is launched by a person, so the gate may never fire"
        for task, stage, line in sdd.stage_exit_selectors
        if task in sdd.adhoc_tasks
    ]


def check_ondemand_actions(sdd: Sdd) -> list[str]:
    if len(sdd.adhoc_tasks) < 2:
        return [
            "the brief lists actions handlers may take at any time; expected at least 2 "
            f"adhoc tasks, found {len(sdd.adhoc_tasks)}"
        ]
    return [
        f"adhoc task {task!r} is marked Required: {sdd.task_required.get(task)} — "
        "optional user-launched work never blocks stage completion"
        for task in sdd.adhoc_tasks
        if sdd.task_required.get(task, "No").strip().lower().startswith("yes")
    ]


def check_wait_for_user_pairing(sdd: Sdd) -> list[str]:
    has_exit = "wait-for-user" in sdd.exit_types
    has_entry = "user-selected-stage" in sdd.stage_entry_rules
    if has_exit and has_entry:
        return []
    if not has_exit and not has_entry:
        return [
            "senior review must park until a person picks the next phase — no "
            "`wait-for-user` exit and no `user-selected-stage` entry were modeled"
        ]
    missing = "user-selected-stage entry" if has_exit else "wait-for-user exit"
    return [f"the two halves of the picker pairing must both exist — missing the {missing}"]


def check_dropped_terminal(sdd: Sdd) -> list[str]:
    if any(re.search(r"drop|withdraw", stage, re.I) for stage in sdd.stages):
        return []
    return ["no stage covers the cardholder dropping the dispute"]


def check_send_back_loop(sdd: Sdd) -> list[str]:
    text = open(sdd.source, encoding="utf-8").read().lower()
    if "return-to-origin" in text or re.search(r"send[- ]back|more evidence", text):
        return []
    return ["the analyst send-back path back to the checking phase is not modeled"]


CHECKS = {
    "adhoc-stage-exit": check_adhoc_stage_exit,
    "ondemand-actions": check_ondemand_actions,
    "wait-for-user-pairing": check_wait_for_user_pairing,
    "dropped-terminal": check_dropped_terminal,
    "send-back-loop": check_send_back_loop,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in CHECKS:
        sys.exit(f"usage: {sys.argv[0]} <{'|'.join(CHECKS)}> [sdd-file ...]")
    name = sys.argv[1]
    sdd = _load(sys.argv[2:])
    issues = CHECKS[name](sdd)
    if issues:
        sys.exit(f"FAIL: {name} ({sdd.source})\n  - " + "\n  - ".join(issues))
    print(f"OK: {name} ({sdd.source})")


if __name__ == "__main__":
    main()
