#!/usr/bin/env python3
"""Deterministic grammar audit for tasks/tasks.md, on either planning lane.

Usage:
    python3 audit_plan.py <tasks/tasks.md> [--lane plan|build] [--sdd <sdd.md>]

Read-only. Exit 0 = grammar-clean. Exit 1 = numbered findings on stderr;
repair the plan with Write/Edit and re-run until clean.

`--lane plan` (the default) enforces the compact no-build contract
(planning.md § Compact no-build T-entry shape): `## T{N}: task "{Task Name}"`
headings, one `field: value` per line, the full plan-only field set, and no
registry-derived keys.

`--lane build` audits a build-lane plan, whose T-entries legitimately carry
resolved registry data (`taskTypeId`), JSON-shaped task keys (`isRequired`,
`runOnlyOnce`), and their stage and type in the canonical heading rather than
as fields. It therefore drops the forbidden-key and plan-only field checks and
keeps only what both lanes share: `activation-mode` and `entry-rule` present on
every task T-entry, both drawn from their vocabularies, correctly paired, and
consecutive single-task lanes on sequential runs.

Checks common to both lanes: legal `activation-mode` values, legal
`activation-mode` / `entry-rule` pairs, sequential lane numbering.
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

# The build lane names the same task differently: `stage` and `type` come from
# the canonical heading, `required`/`run-only-once` are written as the JSON keys
# `isRequired`/`runOnlyOnce`, and `resource-intent`/`identity` do not exist once
# the registry is resolved. Only the two activation fields are required on both
# lanes -- the same pair planning.md's Plan-shape gate and SKILL.md Rule 6 demand.
BUILD_LANE_REQUIRED = ["activation-mode", "entry-rule"]
LANES = ("plan", "build")

# Compact form (`## T{N}: task "Name"`) or canonical full-form build title
# (`## T{N}: Add <type> task "Name" to "Stage"`) — both are addressable.
TASK_HEADING = re.compile(
    r'^## T\d+: (?:task "[^"\n]+"|Add [a-z][a-z-]* task "[^"\n]+" to "[^"\n]+")\s*$'
)
ANY_T_HEADING = re.compile(r"^## T\d+\s*[:.]", re.M)
FORBIDDEN_KEYS = ["taskTypeId", "activityTypeId", "connectionId", "registry-resolved", "recipients-resolved"]

# planning.md § Activation-mode audit — the six user-visible task modes plus
# `parallel-after-predecessor`.
ACTIVATION_MODES = {
    "sequential", "parallel", "parallel-after-predecessor",
    "event-triggered", "adhoc", "fan-in", "conditional-gate",
}
# plugins/conditions/task-entry-conditions/planning.md § activation-mode /
# rule-type table, keyed by rule. Rules outside this map are explicitly
# authored event/condition rules and pair with any mode that permits them.
ENTRY_RULE_MODES = {
    "runs-sequentially": {"sequential", "parallel-after-predecessor"},
    "current-stage-entered": {"parallel"},
    "adhoc": {"adhoc"},
    "selected-tasks-completed": {"fan-in", "conditional-gate"},
    "wait-for-connector": {"event-triggered"},
}


def field_value(section: str, field: str) -> str | None:
    match = re.search(rf"(?im)^\s*[-*]?\s*{re.escape(field)}\s*:\s*(.+)$", section)
    return match.group(1).strip() if match else None


def rule_token(value: str | None) -> str | None:
    """Leading canonical identifier, dropping any `("selector")` and trailing prose."""
    match = re.match(r"[a-z][a-z0-9-]*", (value or "").strip().strip('`"\' ').casefold())
    return match.group(0) if match else None


def heading_stage(head_line: str) -> str | None:
    """Stage name from a canonical build-lane heading: `... task "X" to "StageA"`."""
    match = re.search(r'\bto\s+"([^"\n]+)"\s*$', head_line.strip())
    return match.group(1) if match else None


def audit(path: Path, lane: str = "plan") -> list[str]:
    findings: list[str] = []
    sequential_lanes: dict[str, list[tuple[str, int]]] = {}
    text = path.read_text(encoding="utf-8")

    headings = list(re.finditer(r"(?m)^## (T\d+)[^\n]*$", text))
    if not headings:
        findings.append("no `## T{N}:` entries found — the compact plan uses T-numbered H2 entries")
        return findings

    if lane == "plan":
        for key in FORBIDDEN_KEYS:
            if key in text:
                findings.append(f"forbidden key {key!r} — the no-build plan omits registry-derived data")

    required_fields = ALWAYS_REQUIRED if lane == "plan" else BUILD_LANE_REQUIRED

    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.start():end]
        head_line = section.splitlines()[0]
        label = heading.group(1)

        is_task_entry = TASK_HEADING.match(head_line) is not None
        # The salvage heuristic recovers a §4.6 task whose heading is malformed.
        # It is plan-lane only: a build-lane plan also carries §4.7 condition
        # entries (`Add task-entry condition for "X" in "Y"`) that satisfy every
        # clause below while carrying `rule-type:`, not `entry-rule:`.
        looks_like_task = lane == "plan" and (
            (
                field_value(section, "stage") is not None
                and field_value(section, "activation-mode") is not None
            )
            or re.search(r"(?i)\btask\b[^\n]*\"", head_line) is not None
        )

        if not is_task_entry and looks_like_task:
            findings.append(
                f'{label}: task heading must be `## {label}: task "{{Task Name}}"` or the canonical '
                f'`## {label}: Add <type> task "{{Task Name}}" to "{{Stage}}"` (got: {head_line!r})'
            )

        if not (is_task_entry or looks_like_task):
            continue

        # One `field: value` per line; semicolon-packed lines hide fields.
        for field in required_fields:
            if field_value(section, field) is None:
                hint = ""
                if re.search(rf"(?i)[;,]\s*{re.escape(field)}\s*:", section):
                    hint = " (present mid-line — each field goes on its own line)"
                findings.append(f"{label}: missing `{field}:` line{hint}")

        activation = (field_value(section, "activation-mode") or "").casefold()
        mode = rule_token(activation)
        rule = rule_token(field_value(section, "entry-rule"))
        if mode is not None and mode not in ACTIVATION_MODES:
            findings.append(
                f"{label}: `activation-mode: {mode}` is not a task mode; use one of "
                f"{', '.join(sorted(ACTIVATION_MODES))}"
            )
        elif mode is not None and rule in ENTRY_RULE_MODES:
            allowed = ENTRY_RULE_MODES[rule]
            if mode not in allowed:
                findings.append(
                    f"{label}: `activation-mode: {mode}` cannot carry `entry-rule: {rule}` — "
                    f"that rule pairs with {' or '.join(sorted(allowed))} "
                    f"(list position never normalizes an authored rule into another mode)"
                )
        lane = field_value(section, "lane")
        if "sequential" in activation and (lane is None or not re.match(r"^\d+$", lane)):
            findings.append(f"{label}: sequential task needs an integer `lane:` line")
        elif "sequential" in activation and lane is not None:
            stage = (field_value(section, "stage") or heading_stage(head_line) or "").strip('"` ')
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
    # Every `#### Stage SLA` block declares its title on its own line —
    # a collapsed `**SLA Type:** … **SLA Title:** …` line hides the title
    # from line-start tooling and reference resolution.
    for match in re.finditer(r"(?im)^####\s+Stage SLA\s*$", text):
        block_end = re.search(r"(?m)^#{1,4}\s", text[match.end():])
        block = text[match.end(): match.end() + block_end.start()] if block_end else text[match.end():]
        if not re.search(r"(?im)^\*\*SLA Title:\*\*\s*\S", block):
            line_no = text[: match.start()].count("\n") + 1
            findings.append(
                f"{source}:{line_no}: '#### Stage SLA' block has no line-start '**SLA Title:**' — "
                "render '**SLA Type:**' and '**SLA Title:**' as two separate lines"
            )
    for line_no, line in enumerate(text.splitlines(), 1):
        for call in re.finditer(r"sla-status-change\s*\(([^)]*)\)", line, re.I):
            args = re.findall(r"[\"“‘']([^\"”’']+)[\"”’']", call.group(1))
            if args and len(args) not in (2, 3):
                findings.append(
                    f"{source}:{line_no}: sla-status-change reference needs 2 (breach) "
                    f"or 3 (at-risk) quoted args; got {len(args)}"
                )
            if args and args[0].strip().casefold() == "case":
                findings.append(
                    f"{source}:{line_no}: sla-status-change target 'Case' — the case-level target is the literal 'root'"
                )
    return findings


def plan_repeats_sdd_sla_rules(plan: str, sdd: str) -> list[str]:
    """Every quoted-arg sla-status-change entry declared in the SDD is repeated
    verbatim in the plan (compact-contract requirement) — target + each title."""
    findings: list[str] = []
    declared: list[list[str]] = []
    for call in re.finditer(r"sla-status-change\s*\(([^)]*)\)", sdd, re.I):
        args = re.findall(r"[\"“‘']([^\"”’']+)[\"”’']", call.group(1))
        if args and args not in declared:
            declared.append(args)
    if not declared:
        return findings
    lowered = plan.casefold()
    if "sla-status-change" not in lowered:
        findings.append(
            "the SDD declares sla-status-change entry rules but the plan carries none — "
            "each gets its own T-entry with rule-type: sla-status-change, repeating target and titles verbatim"
        )
        return findings
    for args in declared:
        missing = [a for a in args if a.casefold() not in lowered]
        if missing:
            findings.append(
                f"plan does not repeat the SDD sla-status-change entry {tuple(args)!r} verbatim — missing: {', '.join(missing)}"
            )
    return findings


def main() -> None:
    args = list(sys.argv[1:])
    sdd: Path | None = None
    lane = "plan"
    if "--sdd" in args:
        i = args.index("--sdd")
        sdd = Path(args[i + 1])
        del args[i:i + 2]
    if "--lane" in args:
        i = args.index("--lane")
        lane = args[i + 1]
        del args[i:i + 2]
        if lane not in LANES:
            sys.exit(f"--lane must be one of {', '.join(LANES)}")
    if len(args) != 1:
        sys.exit(__doc__)
    findings = audit(Path(args[0]), lane)
    if sdd is not None:
        sdd_text = sdd.read_text(encoding="utf-8")
        findings.extend(sla_shape_findings(sdd_text, sdd.name))
        findings.extend(plan_repeats_sdd_sla_rules(Path(args[0]).read_text(encoding="utf-8"), sdd_text))
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
