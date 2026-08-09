#!/usr/bin/env python3
"""Deterministic grammar audit for the compact no-build plan (tasks/tasks.md).

Usage:
    python3 audit_plan.py <tasks/tasks.md> [--sdd <sdd.md>]

Read-only. Exit 0 = grammar-clean. Exit 1 = numbered findings on stderr;
repair the plan with Write/Edit and re-run until clean. Enforces the compact
`tasks/tasks.md` contract: `## T{N}: task "{Task Name}"` headings, one
`field: value` per line, lanes on sequential runs, no registry-derived keys.
`--sdd` additionally checks every `sla-status-change(...)` reference in the
SDD for the 2-arg (breach) / 3-arg (at-risk) quoted shape.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TASK_FIELDS = [
    "stage", "type", "activation-mode", "entry-rule", "lane", "required",
    "run-only-once", "resource-intent", "identity", "rationale",
]
# `lane` is only mandatory for sequential runs; checked separately.
ALWAYS_REQUIRED = [f for f in TASK_FIELDS if f != "lane"]

TASK_HEADING = re.compile(r'^## T\d+: task "[^"\n]+"\s*$')
ANY_T_HEADING = re.compile(r"^## T\d+\s*[:.]", re.M)
FORBIDDEN_KEYS = ["taskTypeId", "activityTypeId", "connectionId", "registry-resolved", "recipients-resolved"]


def field_value(section: str, field: str) -> str | None:
    match = re.search(rf"(?im)^\s*[-*]?\s*{re.escape(field)}\s*:\s*(.+)$", section)
    return match.group(1).strip() if match else None


def audit(path: Path) -> list[str]:
    findings: list[str] = []
    sequential_lanes: dict[str, list[tuple[str, int]]] = {}
    text = path.read_text(encoding="utf-8")

    headings = list(re.finditer(r"(?m)^## (T\d+)[^\n]*$", text))
    if not headings:
        findings.append("no `## T{N}:` entries found — the compact plan uses T-numbered H2 entries")
        return findings

    for key in FORBIDDEN_KEYS:
        if key in text:
            findings.append(f"forbidden key {key!r} — the no-build plan omits registry-derived data")

    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.start():end]
        head_line = section.splitlines()[0]
        label = heading.group(1)

        is_task_entry = TASK_HEADING.match(head_line) is not None
        looks_like_task = (
            field_value(section, "stage") is not None
            and field_value(section, "activation-mode") is not None
        ) or re.search(r"(?i)\btask\b[^\n]*\"", head_line) is not None

        if not is_task_entry and looks_like_task:
            findings.append(
                f'{label}: task heading must be exactly `## {label}: task "{{Task Name}}"` — '
                f"no verb phrases or stage suffixes in the heading (got: {head_line!r})"
            )

        if not (is_task_entry or looks_like_task):
            continue

        # One `field: value` per line; semicolon-packed lines hide fields.
        for field in ALWAYS_REQUIRED:
            if field_value(section, field) is None:
                hint = ""
                if re.search(rf"(?i)[;,]\s*{re.escape(field)}\s*:", section):
                    hint = " (present mid-line — each field goes on its own line)"
                findings.append(f"{label}: missing `{field}:` line{hint}")

        activation = (field_value(section, "activation-mode") or "").casefold()
        lane = field_value(section, "lane")
        if "sequential" in activation and (lane is None or not re.match(r"^\d+$", lane)):
            findings.append(f"{label}: sequential task needs an integer `lane:` line")
        elif "sequential" in activation and lane is not None:
            stage = (field_value(section, "stage") or "").strip('"` ')
            sequential_lanes.setdefault(stage, []).append((label, int(lane)))

    # Sequential runs use consecutive single-task lanes: no duplicates, no gaps.
    for stage, lanes in sequential_lanes.items():
        numbers = [n for _, n in lanes]
        if sorted(numbers) != list(range(min(numbers), min(numbers) + len(numbers))):
            labels = ", ".join(f"{t}=lane {n}" for t, n in lanes)
            findings.append(
                f"stage {stage!r}: sequential lanes must be consecutive single-task numbers with no duplicates; got {labels}"
            )

    findings.extend(sla_shape_findings(text, path.name))
    return findings


def sla_shape_findings(text: str, source: str) -> list[str]:
    """sla-status-change references need 2 quoted args (breach) or 3 (at-risk).

    Zero-quoted-arg mentions are summary/prose shorthand and are not flagged.
    """
    findings: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for call in re.finditer(r"sla-status-change\s*\(([^)]*)\)", line, re.I):
            args = re.findall(r"[\"“‘']([^\"”’']+)[\"”’']", call.group(1))
            if args and len(args) not in (2, 3):
                findings.append(
                    f"{source}:{line_no}: sla-status-change reference needs 2 (breach) "
                    f"or 3 (at-risk) quoted args; got {len(args)}"
                )
    return findings


def main() -> None:
    args = list(sys.argv[1:])
    sdd: Path | None = None
    if "--sdd" in args:
        i = args.index("--sdd")
        sdd = Path(args[i + 1])
        del args[i:i + 2]
    if len(args) != 1:
        sys.exit(__doc__)
    findings = audit(Path(args[0]))
    if sdd is not None:
        findings.extend(sla_shape_findings(sdd.read_text(encoding="utf-8"), sdd.name))
    if findings:
        shown = findings[:40]
        print("AUDIT FAIL — repair these, then re-run:", file=sys.stderr)
        for n, f in enumerate(shown, 1):
            print(f"  {n}. {f}", file=sys.stderr)
        if len(findings) > len(shown):
            print(f"  … and {len(findings) - len(shown)} more", file=sys.stderr)
        sys.exit(1)
    print("AUDIT OK: tasks.md grammar is clean")


if __name__ == "__main__":
    main()
