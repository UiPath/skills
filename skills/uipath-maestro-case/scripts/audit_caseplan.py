#!/usr/bin/env python3
"""Deterministic completeness audit: caseplan.json against sdd.md.

Usage:
    python3 audit_caseplan.py <caseplan.json> --sdd <sdd.md> [--registry <tasks/registry-resolved.json>]

Read-only. Exit 0 = every SDD element reached the caseplan. Exit 1 = numbered
MISSING findings on stderr; repair `caseplan.json` with Write/Edit and re-run
until clean (max 3 loops, then AskUserQuestion).

This gate runs against the FINAL artifact. `uip maestro case validate` only
warns `Task has no entry rules`, and a missing entry rule hangs `case debug`
indefinitely -- so entry-rule presence, placeholder honesty, and binding
resource-key shape are checked here, per task, against what the SDD declared.

WARN findings (EXTRA caseplan elements, placeholder tasks, surviving
`<UNRESOLVED>` markers) are reported but do not fail the run.

Scope note: SDD *rendering* conventions (heading shape, `**SLA Title:**` on its
own line) are not audited here -- they belong to the SDD author. This gate only
checks that what the SDD declares exists in the caseplan, plus the
`sla-status-change(...)` reference arity that both artifacts share.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"(?m)^(#{1,6})[ \t]+(.*?)[ \t]*$")
STAGE_HEADING = re.compile(r"^(?:\w+\s+)?Stage(?:\s+\d+)?\s*[:.]\s*(.+)$", re.I)
TASK_HEADING = re.compile(r"^Task\s+[\d.]+\s*[:.]\s*(.+)$", re.I)
SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")
PLACEHOLDER_CELLS = {"", "-", "—", "–", "n/a", "na", "none", "tbd"}
STAGE_NODE_TYPES = {"case-management:Stage", "case-management:ExceptionStage"}
TRIGGER_NODE_TYPES = {"uipath.case.trigger", "case-management:Trigger"}
UNRESOLVED = re.compile(r"<UNRESOLVED[^>]*>", re.I)


# SDD headings often carry a trailing slug -- `Intake and completeness (`stage-intake`)`
# -- while the caseplan label holds the bare name.
TRAILING_SLUG = re.compile(r"\s*\((?:`[^`]*`|[a-z0-9_-]+)\)\s*$", re.I)


def norm(value: str | None) -> str:
    """Match key for a display name: case-folded, whitespace-collapsed, unpunctuated,
    with any trailing `(slug)` dropped."""
    text = TRAILING_SLUG.sub("", (value or "").strip()).strip('`"“”‘’ ')
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.casefold())).strip()


def is_blank(cell: str) -> bool:
    return norm(cell) in {norm(p) for p in PLACEHOLDER_CELLS}


# --------------------------------------------------------------------------
# Markdown helpers
# --------------------------------------------------------------------------

def section_blocks(text: str) -> list[dict]:
    """Every heading with the body that belongs to it (up to the next heading
    of the same or a shallower level)."""
    heads = [
        {"level": len(m.group(1)), "title": m.group(2), "start": m.start(), "body_at": m.end()}
        for m in HEADING.finditer(text)
    ]
    for index, head in enumerate(heads):
        end = len(text)
        for later in heads[index + 1:]:
            if later["level"] <= head["level"]:
                end = later["start"]
                break
        head["body"] = text[head["body_at"]:end]
        head["own"] = text[head["body_at"]:heads[index + 1]["start"]] if index + 1 < len(heads) else text[head["body_at"]:]
    return heads


def first_table(block: str) -> tuple[list[str], list[list[str]]]:
    """Header cells and data rows of the first pipe table in `block`."""
    header: list[str] = []
    rows: list[list[str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if header and rows:
                break
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if cells and all(SEPARATOR_CELL.match(c) for c in cells if c):
            continue
        if not header:
            header = cells
        else:
            rows.append(cells)
    return header, rows


def column(header: list[str], *names: str) -> int | None:
    wanted = [norm(n) for n in names]
    for index, cell in enumerate(header):
        if norm(cell) in wanted:
            return index
    return None


def cell(row: list[str], index: int | None) -> str:
    return row[index] if index is not None and index < len(row) else ""


def field(block: str, label: str) -> str | None:
    match = re.search(rf"(?im)^\*\*{re.escape(label)}:?\*\*[ \t]*(.*)$", block)
    return match.group(1).strip() if match else None


# --------------------------------------------------------------------------
# SDD
# --------------------------------------------------------------------------

def parse_sdd(text: str) -> dict:
    heads = section_blocks(text)
    sdd: dict = {"stages": [], "case_exit_rows": 0, "triggers": 0, "variables": [], "sla_case": False}

    for head in heads:
        title = head["title"]
        body = head["body"]

        if head["level"] == 3 and norm(title) == norm("Case Exit Conditions"):
            sdd["case_exit_rows"] = len(first_table(body)[1])
        elif head["level"] == 3 and norm(title) == norm("Case Triggers"):
            sdd["triggers"] = len(first_table(body)[1])
        elif head["level"] == 3 and norm(title) == norm("Case-Level SLA Escalation Rules"):
            sdd["sla_case"] = bool(first_table(body)[1])
        elif head["level"] == 3 and norm(title) == norm("Case Variables"):
            header, rows = first_table(body)
            name_at = column(header, "Name", "Variable", "Variable Name")
            for row in rows:
                name = cell(row, name_at)
                if name and not is_blank(name):
                    sdd["variables"].append(name.strip("`"))
        elif head["level"] == 3 and STAGE_HEADING.match(title):
            sdd["stages"].append(parse_stage(STAGE_HEADING.match(title).group(1), head["body"]))

    return sdd


def parse_stage(name: str, body: str) -> dict:
    stage: dict = {
        "name": name.strip(),
        "tasks": [],
        "entry_rows": 0,
        "exit_rows": 0,
        "has_sla": False,
        "required": field(body, "Required for Case Completion"),
    }
    details: dict[str, dict] = {}

    for head in section_blocks(body):
        title, block = head["title"], head["body"]
        if head["level"] == 4 and norm(title) == norm("Stage Entry Conditions"):
            stage["entry_rows"] = len(first_table(block)[1])
        elif head["level"] == 4 and norm(title) == norm("Stage Exit Conditions"):
            stage["exit_rows"] = len(first_table(block)[1])
        elif head["level"] == 4 and norm(title) == norm("Stage SLA"):
            stage["has_sla"] = bool(first_table(block)[1])
        elif head["level"] == 4 and norm(title) == norm("Tasks"):
            header, rows = first_table(block)
            name_at = column(header, "Task Name", "Task", "Name")
            type_at = column(header, "Type", "Task Type")
            mode_at = column(header, "Activation Mode", "Activation")
            req_at = column(header, "Required")
            for row in rows:
                task_name = cell(row, name_at)
                if not task_name or is_blank(task_name):
                    continue
                stage["tasks"].append({
                    "name": task_name.strip("`"),
                    "type": cell(row, type_at).strip("`"),
                    "mode": cell(row, mode_at),
                    "required": cell(row, req_at),
                    "resolved_resource": None,
                    "identity_resolved": False,
                    "entry_rows": 0,
                })
        elif head["level"] == 5 and TASK_HEADING.match(title):
            detail_name = TASK_HEADING.match(title).group(1).strip()
            entry = 0
            for sub in section_blocks(block):
                if norm(sub["title"]).startswith(norm("Entry Condition")):
                    entry = len(first_table(sub["body"])[1])
            match = re.search(r"(?is)\*\*Entry Condition:?\*\*(.*?)(?=\n\*\*[A-Z]|\n#{1,6} |\Z)", block)
            if match:
                entry = max(entry, len(first_table(match.group(1))[1]))
            identity_fields = [
                field(block, "Resource Identity"), field(block, "Folder Path"),
                field(block, "Connection ID"), field(block, "Activity Type ID"),
            ]
            declared = [f for f in identity_fields if f and not is_blank(f)]
            details[norm(detail_name)] = {
                "type": (field(block, "Type") or "").strip("`"),
                "resolved_resource": field(block, "Resolved Resource"),
                # Resolved only when at least one identity field is filled in and
                # none of the declared ones still carry an <UNRESOLVED> marker.
                "identity_resolved": bool(declared) and not any(UNRESOLVED.search(f) for f in declared),
                "entry_rows": entry,
            }

    for task in stage["tasks"]:
        detail = details.get(norm(task["name"]))
        if detail:
            task["resolved_resource"] = detail["resolved_resource"]
            task["identity_resolved"] = detail["identity_resolved"]
            task["entry_rows"] = detail["entry_rows"]
            if not task["type"] and detail["type"]:
                task["type"] = detail["type"]
            task["detail_type"] = detail["type"]
    stage["detail_names"] = list(details)
    return stage


# --------------------------------------------------------------------------
# caseplan.json
# --------------------------------------------------------------------------

def parse_caseplan(doc: dict) -> dict:
    plan: dict = {"stages": [], "triggers": 0, "variables": [], "bindings": doc.get("bindings") or []}
    metadata = doc.get("metadata") or {}
    plan["case_exit_rules"] = len(metadata.get("caseExitRules") or [])
    plan["case_sla"] = bool(metadata.get("slaRules"))

    variables = doc.get("variables") or {}
    for group in ("inputs", "outputs", "inputOutputs"):
        for variable in variables.get(group) or []:
            plan["variables"].append(variable.get("name"))

    for node in doc.get("nodes") or []:
        node_type = node.get("type")
        data = node.get("data") or {}
        if node_type in TRIGGER_NODE_TYPES:
            plan["triggers"] += 1
        elif node_type in STAGE_NODE_TYPES:
            tasks = []
            for lane in data.get("tasks") or []:
                for task in lane:
                    tasks.append({
                        # Some builds carry the display name only on the `name`
                        # binding; resolve it so the task is not reported missing.
                        "name": task.get("displayName")
                        or task.get("label")
                        or binding_default(plan, (task.get("data") or {}).get("name")),
                        "type": task.get("type"),
                        "entry": task.get("entryConditions") or [],
                        "data": task.get("data") or {},
                    })
            plan["stages"].append({
                "name": data.get("label") or data.get("displayName"),
                "tasks": tasks,
                "entry": data.get("entryConditions") or [],
                "exit": data.get("exitConditions") or [],
                "sla": data.get("slaRules") or [],
            })
    return plan


def binding_default(plan: dict, expression) -> str | None:
    """Follow a `=bindings.<id>` reference to the literal it defaults to."""
    binding = binding_for(plan, expression)
    if binding is None:
        return None
    value = binding.get("default")
    return value if isinstance(value, str) else None


def binding_for(plan: dict, expression) -> dict | None:
    if not isinstance(expression, str):
        return None
    match = re.fullmatch(r"=bindings\.(\w+)", expression.strip())
    if not match:
        return None
    for binding in plan["bindings"]:
        if binding.get("id") == match.group(1):
            return binding
    return None


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------

def resolve_task(plan_tasks: dict, key: str, seen: set[str]) -> dict | None:
    """Exact display-name match, else the one unseen caseplan task whose name is
    the SDD name plus a disambiguating suffix."""
    if key in plan_tasks:
        return plan_tasks[key]
    candidates = [
        task for name, task in plan_tasks.items()
        if name not in seen and name.startswith(key + " ")
    ]
    return candidates[0] if len(candidates) == 1 else None


def compare(sdd: dict, plan: dict) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    warn: list[str] = []

    plan_stages = {norm(s["name"]): s for s in plan["stages"]}
    seen_stages: set[str] = set()

    for stage in sdd["stages"]:
        key = norm(stage["name"])
        target = plan_stages.get(key)
        if target is None:
            missing.append(f"stage {stage['name']!r}: declared in the SDD, absent from caseplan.json")
            continue
        seen_stages.add(key)

        if stage["entry_rows"] and not target["entry"]:
            missing.append(
                f"stage {stage['name']!r}: SDD declares {stage['entry_rows']} entry condition row(s), caseplan has none"
            )
        if stage["exit_rows"] and not target["exit"]:
            missing.append(
                f"stage {stage['name']!r}: SDD declares {stage['exit_rows']} exit condition row(s), caseplan has none"
            )
        if stage["has_sla"] and not target["sla"]:
            missing.append(f"stage {stage['name']!r}: SDD declares a Stage SLA, caseplan has no slaRules")

        plan_tasks = {norm(t["name"]): t for t in target["tasks"]}
        seen_tasks: set[str] = set()

        for task in stage["tasks"]:
            task_key = norm(task["name"])
            found = resolve_task(plan_tasks, task_key, seen_tasks)
            if found is None:
                missing.append(
                    f"stage {stage['name']!r} task {task['name']!r}: declared in the SDD, absent from caseplan.json"
                )
                continue
            seen_tasks.add(norm(found["name"]))
            label = f"stage {stage['name']!r} task {task['name']!r}"

            if task["type"] and norm(task["type"]) != norm(found["type"]):
                missing.append(f"{label}: SDD type {task['type']!r}, caseplan type {found['type']!r}")

            # `validate` only WARNS here; a real miss hangs `case debug` forever.
            if not found["entry"]:
                missing.append(
                    f"{label}: no entryConditions in caseplan.json -- `validate` only warns, "
                    f"but a task with no entry rule hangs `case debug` indefinitely"
                )
            elif task["entry_rows"] and not any((c.get("rules") or []) for c in found["entry"]):
                missing.append(f"{label}: entryConditions carry no rules")

            resolved = (task["resolved_resource"] or "").strip()
            is_placeholder = not found["data"]
            if is_placeholder and task.get("identity_resolved"):
                missing.append(
                    f"{label}: caseplan has empty `data: {{}}` (placeholder) but the SDD resolved "
                    f"the resource to {resolved!r}"
                )
            elif is_placeholder:
                warn.append(f"{label}: placeholder task (empty `data`) -- resource still unresolved")

            missing.extend(binding_findings(plan, found, label))

        for extra in target["tasks"]:
            if norm(extra["name"]) not in seen_tasks:
                warn.append(
                    f"stage {stage['name']!r} task {extra['name']!r}: in caseplan.json, no matching SDD task row"
                )

    for extra_key, extra in plan_stages.items():
        if extra_key not in seen_stages:
            warn.append(f"stage {extra['name']!r}: in caseplan.json, no matching SDD stage")

    if sdd["case_exit_rows"] and not plan["case_exit_rules"]:
        missing.append(
            f"case: SDD declares {sdd['case_exit_rows']} Case Exit Condition row(s), "
            f"caseplan metadata.caseExitRules is empty"
        )
    if sdd["sla_case"] and not plan["case_sla"]:
        missing.append("case: SDD declares Case-Level SLA Escalation Rules, caseplan metadata.slaRules is empty")
    if sdd["triggers"] and not plan["triggers"]:
        missing.append(f"case: SDD declares {sdd['triggers']} trigger(s), caseplan has no trigger node")

    plan_variables = {norm(v) for v in plan["variables"] if v}
    for name in sdd["variables"]:
        if norm(name) not in plan_variables:
            missing.append(f"variable {name!r}: declared in the SDD Case Variables table, absent from caseplan.json")

    return missing, warn


def binding_findings(plan: dict, task: dict, label: str) -> list[str]:
    """Resource-key shape checks on the bindings a task points at.

    A bare `resourceKey` (no `.<entry>` leaf suffix) passes `validate` and then
    faults or hangs at debug; an api-workflow binding additionally needs
    `resourceSubType: "Api"`.
    """
    findings: list[str] = []
    for attribute in ("name", "folderPath"):
        binding = binding_for(plan, task["data"].get(attribute))
        if binding is None:
            continue
        key = binding.get("resourceKey")
        if isinstance(key, str) and key and "." not in key.rsplit("/", 1)[-1]:
            findings.append(
                f"{label}: binding {binding.get('id')!r} has a bare resourceKey {key!r} -- "
                f"it needs the `.<entry name>` leaf suffix"
            )
        if task["type"] == "api-workflow" and not binding.get("resourceSubType"):
            findings.append(
                f"{label}: api-workflow binding {binding.get('id')!r} is missing `resourceSubType: \"Api\"`"
            )
    return findings


def sla_reference_findings(text: str, source: str) -> list[str]:
    """`sla-status-change` takes 2 quoted args (breach) or 3 (at-risk); the
    case-level target is the literal `root`, never `Case`."""
    findings: list[str] = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for call in re.finditer(r"sla-status-change\s*\(([^)]*)\)", line, re.I):
            args = re.findall(r"[\"“‘']([^\"”’']+)[\"”’']", call.group(1))
            if args and len(args) not in (2, 3):
                findings.append(
                    f"{source}:{line_no}: sla-status-change reference needs 2 (breach) or 3 (at-risk) "
                    f"quoted args; got {len(args)}"
                )
            if args and args[0].strip().casefold() == "case":
                findings.append(
                    f"{source}:{line_no}: sla-status-change target 'Case' -- the case-level target is the literal 'root'"
                )
    return findings


def registry_findings(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    markers = sorted(set(UNRESOLVED.findall(text)))
    if markers:
        return [f"{path.name}: {len(markers)} unresolved marker kind(s) survive: {', '.join(markers)}"]
    return []


def main() -> None:
    args = list(sys.argv[1:])
    sdd_path: Path | None = None
    registry_path: Path | None = None
    for flag, setter in (("--sdd", "sdd"), ("--registry", "registry")):
        if flag in args:
            index = args.index(flag)
            value = Path(args[index + 1])
            del args[index:index + 2]
            if setter == "sdd":
                sdd_path = value
            else:
                registry_path = value
    if len(args) != 1 or sdd_path is None:
        sys.exit(__doc__)

    doc = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    sdd_text = sdd_path.read_text(encoding="utf-8")

    missing, warn = compare(parse_sdd(sdd_text), parse_caseplan(doc))
    missing.extend(sla_reference_findings(sdd_text, sdd_path.name))
    if registry_path is not None and registry_path.exists():
        warn.extend(registry_findings(registry_path))

    for note in warn:
        print(f"  WARN: {note}", file=sys.stderr)
    if missing:
        shown = missing[:40]
        print("AUDIT FAIL -- MISSING IN CASEPLAN; repair these, then re-run:", file=sys.stderr)
        for number, finding in enumerate(shown, 1):
            print(f"  {number}. {finding}", file=sys.stderr)
        if len(missing) > len(shown):
            print(f"  ... and {len(missing) - len(shown)} more", file=sys.stderr)
        sys.exit(1)
    print("AUDIT OK: caseplan.json covers every SDD element")


if __name__ == "__main__":
    main()
