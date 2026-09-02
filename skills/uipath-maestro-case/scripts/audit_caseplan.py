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

Every check has the shape "the SDD declares X, so caseplan.json must have X",
so an SDD the parser does not recognize would pass vacuously. The run therefore
fails when the parse yields no stages, and both the OK and FAIL lines carry the
parse census (`stages=N tasks=N vars=N ...`) so a degraded parse is visible.

Scope note: SDD *rendering* conventions (`**SLA Title:**` on its own line) are
not audited here -- they belong to the SDD author. This gate only checks that
what the SDD declares exists in the caseplan, plus the `sla-status-change(...)`
reference arity that both artifacts share. Section headings and table headers are
the exception, because the parser reads them: common dialects are accepted, and a
heading or column header that would silently empty a check class fails the run
with `did not parse cleanly` -- repair the SDD for those, not the caseplan.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HEADING = re.compile(r"(?m)^(#{1,6})[ \t]+(.*?)[ \t]*$")
STAGE_HEADING = re.compile(r"^(?:\w+\s+)?Stage(?:\s+\d+)?\s*[:.]\s*(.+)$", re.I)
TASK_HEADING = re.compile(r"^Task\s+[A-Z]?[\d.]+\s*[:.]\s*(.+)$", re.I)
SEPARATOR_CELL = re.compile(r"^:?-{2,}:?$")
PLACEHOLDER_CELLS = {"", "-", "—", "–", "n/a", "na", "none", "tbd"}
STAGE_NODE_TYPES = {"case-management:Stage"}
TRIGGER_NODE_TYPES = {"uipath.case.trigger", "case-management:Trigger"}
UNRESOLVED = re.compile(r"<UNRESOLVED[^>]*>", re.I)


# SDD headings often carry a trailing slug -- `Intake and completeness (`stage-intake`)`
# -- while the caseplan label holds the bare name.
TRAILING_SLUG = re.compile(r"\s*\((?:`[^`]*`|[a-z0-9_-]+)\)\s*$", re.I)

# Fixed section headings vary between SDD authors: a section number can lead
# (`### 1.5 Case Variables`, `### Section 2: ...`) and "Completion" stands in for
# "Exit". Exact-equality matching dropped those headings, and with them the whole
# check class the section feeds -- so matching strips a leading section number
# and lists every accepted spelling here.
SECTION_NUMBER = re.compile(r"^(?:section )?[a-z]?\d+[a-z]?(?: \d+[a-z]?)* ")
CASE_EXIT_HEADINGS = ("Case Exit Conditions", "Case Completion Conditions")
CASE_TRIGGER_HEADINGS = ("Case Triggers", "Triggers")
CASE_SLA_HEADINGS = ("Case-Level SLA Escalation Rules",)
CASE_VARIABLE_HEADINGS = ("Case Variables",)
STAGE_ENTRY_HEADINGS = ("Stage Entry Conditions",)
STAGE_EXIT_HEADINGS = ("Stage Exit Conditions", "Stage Completion Conditions")
STAGE_SLA_HEADINGS = ("Stage SLA",)
STAGE_TASK_HEADINGS = ("Tasks",)

# A heading that reads like one of the audited sections above but matches none of
# the accepted spellings. `topic_of` names the datum such a heading would feed;
# the heading is reported only when that datum is still empty, so a look-alike
# heading elsewhere in the document (an appendix `### Process Variables` next to a
# parsed `### Case Variables`) stays quiet while a genuinely skipped section does
# not. An unrecognized heading that owns a datum deletes a whole check class, and
# the gate then passes vacuously.
TOPIC_SUFFIX = re.compile(r"(?:^|\s)(conditions|variables|triggers|sla)$")


def norm(value: str | None) -> str:
    """Match key for a display name: case-folded, whitespace-collapsed, unpunctuated,
    with any trailing `(slug)` dropped."""
    text = TRAILING_SLUG.sub("", (value or "").strip()).strip('`"“”‘’ ')
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.casefold())).strip()


def heading_key(title: str | None) -> str:
    """`norm` for a fixed section heading, with any leading section number
    (`1.5 `, `Section 2: `) dropped."""
    return SECTION_NUMBER.sub("", norm(title))


def heading_is(title: str, *accepted: str) -> bool:
    return heading_key(title) in {heading_key(a) for a in accepted}


def topic_of(title: str) -> str | None:
    """The audited datum an unmatched heading looks like it would feed, if any."""
    key = heading_key(title)
    if {"task", "tasks"} & set(key.split()):
        return "tasks"
    match = TOPIC_SUFFIX.search(key)
    return match.group(1) if match else None


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


def no_name_column_note(title: str, wanted: tuple[str, ...], header: list[str]) -> str:
    return (
        f"section {title!r}: the table has rows but no {'/'.join(wanted)} column "
        f"(header: {' | '.join(header) or '<none>'}) -- every row is skipped, "
        f"so the section contributes nothing to audit"
    )


def unrecognized_heading_note(title: str, level: int) -> str:
    return (
        f"heading {title!r} (level {level}) reads like an audited section but matches no "
        f"accepted spelling -- rename it to one of the canonical headings, or the checks "
        f"it feeds are skipped"
    )


def field(block: str, label: str) -> str | None:
    match = re.search(rf"(?im)^\*\*{re.escape(label)}:?\*\*[ \t]*(.*)$", block)
    return match.group(1).strip() if match else None


# --------------------------------------------------------------------------
# SDD
# --------------------------------------------------------------------------

def parse_sdd(text: str) -> dict:
    heads = section_blocks(text)
    sdd: dict = {
        "stages": [], "case_exit_rows": 0, "triggers": 0, "variables": [],
        "sla_case": False, "parse_notes": [],
    }
    notes: list[str] = sdd["parse_notes"]
    lookalikes: list[tuple[str, str]] = []

    for head in heads:
        title = head["title"]
        body = head["body"]

        if head["level"] != 3:
            continue

        if heading_is(title, *CASE_EXIT_HEADINGS):
            sdd["case_exit_rows"] = len(first_table(body)[1])
        elif heading_is(title, *CASE_TRIGGER_HEADINGS):
            sdd["triggers"] = len(first_table(body)[1])
        elif heading_is(title, *CASE_SLA_HEADINGS):
            sdd["sla_case"] = bool(first_table(body)[1])
        elif heading_is(title, *CASE_VARIABLE_HEADINGS):
            header, rows = first_table(body)
            wanted = ("Name", "Variable", "Variable Name")
            name_at = column(header, *wanted)
            if rows and name_at is None:
                notes.append(no_name_column_note(title, wanted, header))
            for row in rows:
                name = cell(row, name_at)
                if name and not is_blank(name):
                    sdd["variables"].append(name.strip("`"))
        elif STAGE_HEADING.match(title):
            sdd["stages"].append(parse_stage(STAGE_HEADING.match(title).group(1), head["body"], notes))
        else:
            topic = topic_of(title)
            if topic in ("conditions", "variables", "triggers"):
                lookalikes.append((title, topic))

    empty = {
        "conditions": not sdd["case_exit_rows"],
        "variables": not sdd["variables"],
        "triggers": not sdd["triggers"],
    }
    notes.extend(unrecognized_heading_note(t, 3) for t, topic in lookalikes if empty[topic])
    return sdd


def parse_stage(name: str, body: str, notes: list[str] | None = None) -> dict:
    stage: dict = {
        "name": name.strip(),
        "tasks": [],
        "entry_rows": 0,
        "exit_rows": 0,
        "has_sla": False,
        "required": field(body, "Required for Case Completion"),
    }
    details: dict[str, dict] = {}
    notes = notes if notes is not None else []
    stage_notes: list[str] = []
    lookalikes: list[tuple[str, str]] = []

    for head in section_blocks(body):
        title, block = head["title"], head["body"]
        if head["level"] == 4 and heading_is(title, *STAGE_ENTRY_HEADINGS):
            stage["entry_rows"] = len(first_table(block)[1])
        elif head["level"] == 4 and heading_is(title, *STAGE_EXIT_HEADINGS):
            stage["exit_rows"] = len(first_table(block)[1])
        elif head["level"] == 4 and heading_is(title, *STAGE_SLA_HEADINGS):
            stage["has_sla"] = bool(first_table(block)[1])
        elif head["level"] == 4 and heading_is(title, *STAGE_TASK_HEADINGS):
            header, rows = first_table(block)
            wanted = ("Task Name", "Task", "Name")
            name_at = column(header, *wanted)
            if rows and name_at is None:
                stage_notes.append(no_name_column_note(title, wanted, header))
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
        elif head["level"] == 4 and topic_of(title) in ("conditions", "sla", "tasks"):
            lookalikes.append((title, topic_of(title)))
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
    empty = {
        "conditions": not (stage["entry_rows"] or stage["exit_rows"]),
        "sla": not stage["has_sla"],
        "tasks": not stage["tasks"],
    }
    stage_notes.extend(unrecognized_heading_note(t, 4) for t, topic in lookalikes if empty[topic])
    if details and not stage["tasks"] and not stage_notes:
        # `##### Task <n>.<m>:` blocks exist, so the stage has tasks -- the Tasks
        # table they belong to was neither found nor parsed, and nothing above
        # already explains why.
        stage_notes.append(
            f"{len(details)} `Task <n>.<m>:` detail section(s) but no task row parsed -- the "
            f"`#### Tasks` table is missing or has no Task Name column, so none of its tasks "
            f"are audited"
        )
    notes.extend(f"stage {stage['name']!r}: {note}" for note in stage_notes)
    stage["detail_names"] = list(details)
    return stage


# --------------------------------------------------------------------------
# caseplan.json
# --------------------------------------------------------------------------

def parse_caseplan(doc: dict) -> dict:
    plan: dict = {"stages": [], "triggers": 0, "variables": [], "bindings": doc.get("bindings") or []}
    metadata = doc.get("metadata") or {}
    plan["case_exit_conditions"] = metadata.get("caseExitRules") or []
    plan["case_exit_rules"] = len(plan["case_exit_conditions"])
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

def resolve_tasks(sdd_tasks: list[dict], plan_tasks: list[dict]) -> list[int | None]:
    """Bind each SDD task row to at most one caseplan task, returned by index.

    Tiers run as separate passes over every row -- exact display name, then
    normalized name, then the SDD name plus a disambiguating suffix -- so a
    loose suffix match can never consume the node an exact row needs, and one
    caseplan task can never absorb two rows and hide a dropped one. The looser
    tiers bind only when exactly one unbound caseplan task qualifies: `norm`
    strips punctuation and trailing parentheticals, so `Approve (initial)` and
    `Approve (final)` share a key and must be reported, not silently paired.
    """
    bound: list[int | None] = [None] * len(sdd_tasks)
    taken: set[int] = set()

    def free(predicate) -> list[int]:
        return [i for i, task in enumerate(plan_tasks) if i not in taken and predicate(task)]

    def bind(row: int, index: int) -> None:
        bound[row] = index
        taken.add(index)

    for row, task in enumerate(sdd_tasks):
        hits = free(lambda t, name=task["name"]: (t["name"] or "") == name)
        if hits:
            bind(row, hits[0])

    ambiguous: set[int] = set()
    for row, task in enumerate(sdd_tasks):
        if bound[row] is not None:
            continue
        hits = free(lambda t, key=norm(task["name"]): norm(t["name"]) == key)
        if len(hits) == 1:
            bind(row, hits[0])
        elif hits:
            # Several caseplan tasks collapse to this key. Leave the row
            # unbound rather than guessing, and skip the suffix tier so it
            # cannot bind some unrelated task instead.
            ambiguous.add(row)

    for row, task in enumerate(sdd_tasks):
        if bound[row] is not None or row in ambiguous:
            continue
        hits = free(lambda t, key=norm(task["name"]): norm(t["name"]).startswith(key + " "))
        if len(hits) == 1:
            bind(row, hits[0])

    return bound


def rule_total(conditions: list | None) -> int:
    """Rules kept across a condition list (`Rules = Rule[][]` -- case-schema.md §5).

    Counts rules, never condition objects: an SDD condition table row maps to a
    rule, but several rows may legitimately merge into one condition's AND-group
    (and one row may fan out into several OR-groups), so the condition count is
    not comparable to the row count while the rule total is.
    """
    total = 0
    for condition in conditions or []:
        for group in (condition or {}).get("rules") or []:
            total += len(group) if isinstance(group, list) else 1
    return total


def coverage_finding(label: str, kind: str, rows: int, conditions: list | None) -> list[str]:
    """Compare an SDD condition table against the rules the caseplan kept.

    `>=`, not `==`: grouping and DNF fan-out both push the rule total above the
    row count legitimately, so only a total BELOW the row count is evidence rows
    were dropped. Truthiness alone is not enough -- a build that keeps 1 of 3
    rows is the archetypal lossy build this gate exists to catch.
    """
    if not rows:
        return []
    total = rule_total(conditions)
    if total >= rows:
        return []
    if not total:
        return [f"{label}: SDD declares {rows} {kind} condition row(s), caseplan has no {kind} rules"]
    return [
        f"{label}: SDD declares {rows} {kind} condition row(s), caseplan keeps {total} {kind} "
        f"rule(s) -- rows may group into fewer conditions, never into fewer rules"
    ]


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

        stage_label = f"stage {stage['name']!r}"
        missing.extend(coverage_finding(stage_label, "entry", stage["entry_rows"], target["entry"]))
        missing.extend(coverage_finding(stage_label, "exit", stage["exit_rows"], target["exit"]))
        if stage["has_sla"] and not target["sla"]:
            missing.append(f"stage {stage['name']!r}: SDD declares a Stage SLA, caseplan has no slaRules")

        seen_tasks: set[int] = set()

        for task, index in zip(stage["tasks"], resolve_tasks(stage["tasks"], target["tasks"])):
            if index is None:
                missing.append(
                    f"stage {stage['name']!r} task {task['name']!r}: declared in the SDD, absent from caseplan.json"
                )
                continue
            seen_tasks.add(index)
            found = target["tasks"][index]
            label = f"stage {stage['name']!r} task {task['name']!r}"

            if task["type"] and norm(task["type"]) != norm(found["type"]):
                missing.append(f"{label}: SDD type {task['type']!r}, caseplan type {found['type']!r}")

            # `validate` only WARNS here; a real miss hangs `case debug` forever.
            # Gate on the rule total, never the envelope: `[{"rules": []}]` is
            # truthy but carries nothing, and hangs `debug` exactly like `[]`.
            if not rule_total(found["entry"]):
                if not found["entry"]:
                    missing.append(
                        f"{label}: no entryConditions in caseplan.json -- `validate` only warns, "
                        f"but a task with no entry rule hangs `case debug` indefinitely"
                    )
                else:
                    missing.append(f"{label}: entryConditions carry no rules")
            else:
                missing.extend(coverage_finding(label, "entry", task["entry_rows"], found["entry"]))

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

        for index, extra in enumerate(target["tasks"]):
            if index not in seen_tasks:
                warn.append(
                    f"stage {stage['name']!r} task {extra['name']!r}: in caseplan.json, no matching SDD task row"
                )

    for extra_key, extra in plan_stages.items():
        if extra_key not in seen_stages:
            warn.append(f"stage {extra['name']!r}: in caseplan.json, no matching SDD stage")

    case_exit_total = rule_total(plan["case_exit_conditions"])
    if sdd["case_exit_rows"] and not case_exit_total:
        missing.append(
            f"case: SDD declares {sdd['case_exit_rows']} Case Exit Condition row(s), "
            f"caseplan metadata.caseExitRules is empty"
        )
    elif sdd["case_exit_rows"] > case_exit_total:
        missing.append(
            f"case: SDD declares {sdd['case_exit_rows']} Case Exit Condition row(s), "
            f"caseplan metadata.caseExitRules keeps {case_exit_total} rule(s) -- rows may group "
            f"into fewer conditions, never into fewer rules"
        )
    if sdd["sla_case"] and not plan["case_sla"]:
        missing.append("case: SDD declares Case-Level SLA Escalation Rules, caseplan metadata.slaRules is empty")
    if sdd["triggers"] and not plan["triggers"]:
        missing.append(f"case: SDD declares {sdd['triggers']} trigger(s), caseplan has no trigger node")
    elif sdd["triggers"] > plan["triggers"]:
        # One trigger row is one trigger node -- no grouping applies here.
        missing.append(
            f"case: SDD declares {sdd['triggers']} trigger(s), caseplan has {plan['triggers']} trigger node(s)"
        )

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


def census(sdd: dict) -> str:
    """Parse tally for the OK/FAIL line -- a zero here means the parser did not
    recognize the SDD, not that the SDD is empty."""
    return (
        f"parsed sdd: stages={len(sdd['stages'])} "
        f"tasks={sum(len(s['tasks']) for s in sdd['stages'])} "
        f"vars={len(sdd['variables'])} triggers={sdd['triggers']} "
        f"case-exit-rows={sdd['case_exit_rows']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("caseplan", type=Path, help="Path to the caseplan.json to audit")
    parser.add_argument("--sdd", type=Path, required=True,
                        help="Path to the sdd.md the caseplan was built from")
    parser.add_argument("--registry", type=Path,
                        help="Path to tasks/registry-resolved.json; scanned for surviving <UNRESOLVED> markers")
    args = parser.parse_args()
    sdd_path = args.sdd
    registry_path = args.registry

    doc = json.loads(args.caseplan.read_text(encoding="utf-8"))
    sdd_text = sdd_path.read_text(encoding="utf-8")

    sdd = parse_sdd(sdd_text)
    tally = census(sdd)
    if sdd["parse_notes"]:
        print(
            f"AUDIT FAIL -- {sdd_path.name} did not parse cleanly ({tally}); each finding below "
            f"silently empties a check class. Repair the SDD, not caseplan.json:",
            file=sys.stderr,
        )
        for number, note in enumerate(sdd["parse_notes"], 1):
            print(f"  {number}. {note}", file=sys.stderr)
        sys.exit(1)
    if not sdd["stages"]:
        print(
            f"AUDIT FAIL -- nothing parsed from {sdd_path.name} ({tally}); the gate would pass vacuously.",
            file=sys.stderr,
        )
        print(
            "  Every check reads 'the SDD declares X, so caseplan.json must have X' -- with zero stages "
            "parsed there is nothing to check. Repair the SDD, not caseplan.json: stage headings must be "
            "level-3 `### Stage <n>: <Name>`, with a `#### Tasks` table under each.",
            file=sys.stderr,
        )
        sys.exit(1)

    missing, warn = compare(sdd, parse_caseplan(doc))
    missing.extend(sla_reference_findings(sdd_text, sdd_path.name))
    if registry_path is not None and registry_path.exists():
        warn.extend(registry_findings(registry_path))

    for note in warn:
        print(f"  WARN: {note}", file=sys.stderr)
    if missing:
        shown = missing[:40]
        print(f"AUDIT FAIL -- MISSING IN CASEPLAN ({tally}); repair these, then re-run:", file=sys.stderr)
        for number, finding in enumerate(shown, 1):
            print(f"  {number}. {finding}", file=sys.stderr)
        if len(missing) > len(shown):
            print(f"  ... and {len(missing) - len(shown)} more", file=sys.stderr)
        sys.exit(1)
    print(f"AUDIT OK: caseplan.json covers every SDD element ({tally})")


if __name__ == "__main__":
    main()
