#!/usr/bin/env python3
"""Read-only contract checks for Planner Case SDDs and Maestro caseplans.

Commands:
  inspect-sdd    Parse a Planner-authored Case SDD into a normalized contract.
  check-sdd      Validate that an SDD is complete and safe to build.
  check-caseplan Validate Case JSON invariants that ``uip ... validate`` misses.
  check-parity   Prove that a caseplan preserves its source SDD semantics.

The checker never writes files or contacts a tenant. Exit 0 means clean, exit 1
means deterministic findings, and exit 2 means invocation/input failure.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


TASK_TYPES = frozenset(
    {
        "action",
        "agent",
        "api-workflow",
        "case-management",
        "execute-connector-activity",
        "process",
        "rpa",
        "wait-for-connector",
        "wait-for-timer",
    }
)
TRIGGER_TYPES = frozenset({"manual", "timer", "intsvc.eventtrigger"})
ACTIVATION_MODES = frozenset(
    {
        "adhoc",
        "conditional-gate",
        "event-triggered",
        "fan-in",
        "parallel",
        "parallel-after-predecessor",
        "sequential",
    }
)
LAYOUT_FIELDS = frozenset({"position", "style", "measured", "width", "height", "zIndex"})
STAGE_ENTRY_RULES = frozenset(
    {
        "case-entered",
        "selected-stage-completed",
        "selected-stage-exited",
        "sla-status-change",
        "user-selected-stage",
        "wait-for-connector",
    }
)
STAGE_COMPLETION_RULES = frozenset({"required-tasks-completed", "wait-for-connector"})
STAGE_EXIT_RULES = frozenset({"selected-tasks-completed", "wait-for-connector"})
TASK_ENTRY_RULES = frozenset(
    {
        "adhoc",
        "current-stage-entered",
        "runs-sequentially",
        "selected-tasks-completed",
        "sla-status-change",
        "wait-for-connector",
    }
)
CASE_COMPLETION_RULES = frozenset({"required-stages-completed", "wait-for-connector"})
CASE_EXIT_RULES = frozenset(
    {"selected-stage-completed", "selected-stage-exited", "wait-for-connector"}
)
EXIT_TYPES = frozenset({"exit-only", "return-to-origin", "wait-for-user"})
REQUIRED_HEADINGS = (
    "## Planner Handoff",
    "## Table of Contents",
    "## Section 1: Case Definition",
    "### Case Metadata",
    "### Case Triggers",
    "### Case Exit Conditions",
    "### Case Variables",
    "## Section 2: Stages & Tasks",
    "## Section 3: Personas & App Views",
    "### Personas",
    "### Process App Views",
    "## Section 4: Integrations",
)
STAGE_RE = re.compile(r"^###\s+(Stage\s+\d+|Secondary Stage):\s*(.+?)\s*$", re.M)
TASK_RE = re.compile(r"^#####\s+Task\s+(S?\d+|[A-Z]+)\.(\d+):\s*(.+?)\s*$", re.M)
RULE_RE = re.compile(r"`?\s*([a-z][a-z]+(?:-[a-z]+)*)")
PLACEHOLDERS = frozenset({"", "-", "—", "n/a", "none", "<unresolved>"})


@dataclass(frozen=True, order=True)
class Finding:
    code: str
    message: str
    path: str
    severity: str = "error"


class InputFailure(Exception):
    """An unreadable or malformed input artifact."""


def clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().strip("`\"").strip("'").strip()


def optional(value: Any) -> str | None:
    result = clean(value)
    return None if result.casefold() in PLACEHOLDERS or result.startswith("<UNRESOLVED") else result


def boolean(value: Any) -> bool | None:
    token = clean(value).casefold()
    if token in {"yes", "true", "enabled", "direct"}:
        return True
    if token in {"no", "false", "disabled", "indirect"}:
        return False
    return None


def strip_id_suffix(value: str) -> str:
    return re.sub(r"\s*\(`[^`]*`\)\s*$", "", value).strip()


def split_markdown_row(line: str) -> list[str]:
    """Split a Markdown table row without breaking escaped or code-span pipes."""
    source = line.strip()
    if source.startswith("|"):
        source = source[1:]
    if source.endswith("|"):
        source = source[:-1]
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    escaped = False
    for char in source:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            current.append(char)
            escaped = True
            continue
        if char == "`":
            in_code = not in_code
            current.append(char)
            continue
        if char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).casefold())


def parse_table(lines: list[str]) -> list[dict[str, str]]:
    if len(lines) < 2:
        return []
    headers = [normalize_header(cell) for cell in split_markdown_row(lines[0])]
    if not headers or not all(headers):
        return []
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = split_markdown_row(line)
        if not cells or all(re.fullmatch(r"[-: ]*", cell) for cell in cells):
            continue
        cells += [""] * (len(headers) - len(cells))
        rows.append(dict(zip(headers, cells)))
    return rows


def table_after(block: str, heading: str) -> list[dict[str, str]]:
    match = re.search(rf"^{re.escape(heading)}\s*$", block, re.M)
    if not match:
        return []
    tail = block[match.end() :]
    lines = tail.splitlines()
    start = next((index for index, line in enumerate(lines) if line.lstrip().startswith("|")), None)
    if start is None:
        return []
    table_lines: list[str] = []
    for line in lines[start:]:
        if not line.lstrip().startswith("|"):
            break
        table_lines.append(line)
    return parse_table(table_lines)


def field(block: str, label: str) -> str | None:
    match = re.search(rf"^\*\*{re.escape(label)}:\*\*\s*(.*?)\s*$", block, re.M)
    return optional(match.group(1)) if match else None


def section(text: str, heading: str, level: int) -> str:
    match = re.search(rf"^{re.escape(heading)}\s*$", text, re.M)
    if not match:
        return ""
    following = re.search(rf"^#{{1,{level}}}\s+", text[match.end() :], re.M)
    end = match.end() + following.start() if following else len(text)
    return text[match.start() : end]


def rule_token(value: str) -> str | None:
    match = RULE_RE.match(clean(value))
    return match.group(1) if match else None


def normalized_type(value: str) -> str:
    return clean(value).casefold()


def normalized_trigger_type(value: str) -> str:
    token = normalized_type(value)
    return "timer" if token == "intsvc.timertrigger" else token


def normalized_default(value: str | None) -> Any:
    if value is None:
        return None
    raw = clean(value)
    if raw.casefold() in PLACEHOLDERS:
        return None
    if raw.casefold() == "true":
        return True
    if raw.casefold() == "false":
        return False
    if raw.casefold() == "null":
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def parse_condition_rows(rows: list[dict[str, str]], marks_key: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        when = row.get("when", "")
        rule = rule_token(when)
        if not rule:
            continue
        args_match = re.search(r"\((.*)\)", when)
        args = re.findall(r"[\"'“‘]([^\"'”’]+)[\"'”’]", args_match.group(1)) if args_match else []
        result.append(
            {
                "rule": rule,
                "arguments": args,
                "condition": optional(row.get("if")),
                "displayName": optional(row.get("displayname")),
                "interrupting": boolean(row.get("interrupting")),
                "marksComplete": boolean(row.get(marks_key)),
                "exitType": optional(row.get("exittype")),
            }
        )
    return result


def parse_task(block: str, name: str, stage_name: str, summary: dict[str, str]) -> dict[str, Any]:
    task_type = normalized_type(field(block, "Type") or summary.get("type", ""))
    activation = normalized_type(field(block, "Activation Mode") or summary.get("activationmode", ""))
    envelope = table_after(block, "**Task envelope**")
    envelope_row = envelope[0] if envelope else {}
    entry = parse_condition_rows(table_after(block, "**Entry Condition:**"), "markscomplete")
    inputs = table_after(block, "**Inputs:**")
    outputs = table_after(block, "**Outputs:**")
    resource_name = field(block, "Resolved Resource") or field(block, "Child Case")
    resource = None
    if resource_name:
        resource = {
            "name": resource_name,
            "folder": field(block, "Folder Path") or field(block, "Folder"),
            "identity": field(block, "Resource Identity"),
        }
    return {
        "name": strip_id_suffix(name),
        "type": task_type,
        "activationMode": activation,
        "required": boolean(envelope_row.get("required") or summary.get("required")),
        "runOnlyOnce": boolean(envelope_row.get("runonlyonce") or summary.get("runonlyonce")),
        "entryConditions": entry,
        "inputs": [
            {
                "field": clean(row.get("field")),
                "type": normalized_type(row.get("type", "")),
                "binding": clean(row.get("binding")),
            }
            for row in inputs
            if optional(row.get("field"))
        ],
        "outputs": [
            {
                "field": clean(row.get("field")),
                "binding": clean(row.get("bindingvalue") or row.get("binding") or row.get("value")),
            }
            for row in outputs
            if optional(row.get("field"))
        ],
        "resource": resource,
        "stage": stage_name,
    }


def parse_sdd(path: Path) -> tuple[dict[str, Any], list[Finding]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputFailure(f"cannot read SDD {path}: {exc}") from exc

    findings: list[Finding] = []
    title = re.search(r"^# SDD —\s*(.+?)\s*$", text, re.M)
    case_name = clean(title.group(1)) if title else ""
    if not title:
        findings.append(Finding("SDD-TITLE", "first heading must be '# SDD — {Case Name}'", "document.title"))

    for heading in REQUIRED_HEADINGS:
        if not re.search(rf"^{re.escape(heading)}\s*$", text, re.M):
            findings.append(Finding("SDD-HEADING", f"missing required heading {heading!r}", f"document.headings[{heading}]"))
    if "<!-- planner-handoff:v1 -->" not in text:
        findings.append(Finding("SDD-HANDOFF-MARKER", "missing planner-handoff:v1 marker", "plannerHandoff.marker"))

    handoff_rows = table_after(text, "## Planner Handoff")
    handoff = {
        normalize_header(row.get("field", "")): clean(row.get("value", ""))
        for row in handoff_rows
    }
    if handoff.get("status", "").casefold() != "ready":
        findings.append(Finding("SDD-HANDOFF-STATUS", "Planner Handoff status must be 'ready'", "plannerHandoff.status"))
    if handoff.get("generatedby", "").casefold() != "uipath-planner":
        findings.append(Finding("SDD-HANDOFF-AUTHOR", "Case SDD must be generated by uipath-planner", "plannerHandoff.generatedBy"))
    if handoff.get("templatevalidation", "").casefold() != "passed":
        findings.append(Finding("SDD-HANDOFF-TEMPLATE", "Planner template validation must be 'passed'", "plannerHandoff.templateValidation"))
    build_handoff = handoff.get("buildhandoff", "")
    if "direct" not in build_handoff.casefold() or "uipath-maestro-case" not in build_handoff.casefold():
        findings.append(
            Finding(
                "SDD-HANDOFF-DIRECT",
                "Case SDD must hand off directly to uipath-maestro-case",
                "plannerHandoff.buildHandoff",
            )
        )

    metadata_rows = table_after(text, "### Case Metadata")
    metadata = {normalize_header(row.get("property", "")): clean(row.get("value", "")) for row in metadata_rows}
    identifier = metadata.get("caseidentifier", "")
    identifier_type = None
    identifier_prefix = None
    type_match = re.search(r"Type:\s*([A-Za-z-]+)", identifier, re.I)
    prefix_match = re.search(r"Prefix:\s*([^.;]+)", identifier, re.I)
    if type_match:
        identifier_type = type_match.group(1).casefold()
    if prefix_match:
        identifier_prefix = clean(prefix_match.group(1))

    trigger_rows = table_after(text, "### Case Triggers")
    triggers = [
        {
            "id": clean(row.get("name") or row.get("t")),
            "type": normalized_trigger_type(row.get("triggertype", "")),
            "source": optional(row.get("source")),
            "configuration": optional(row.get("configuration")),
        }
        for row in trigger_rows
        if optional(row.get("triggertype"))
    ]
    trigger_names = [trigger["id"] for trigger in triggers if trigger["id"]]
    trigger_ids = set(trigger_names)
    for duplicate in sorted(
        name for name, count in Counter(trigger_names).items() if count > 1
    ):
        findings.append(
            Finding(
                "SDD-TRIGGER-DUPLICATE",
                f"duplicate trigger name {duplicate!r}",
                f"triggers[{duplicate}]",
            )
        )
    for trigger in triggers:
        trigger_path = f"triggers[{trigger['id'] or '?'}]"
        if not trigger["id"]:
            findings.append(
                Finding("SDD-TRIGGER-NAME", "trigger name is required", f"{trigger_path}.name")
            )
        elif re.fullmatch(r"T\d+", trigger["id"], re.I):
            findings.append(
                Finding(
                    "SDD-TRIGGER-NAME",
                    "trigger names must be semantic, not numbered aliases",
                    f"{trigger_path}.name",
                )
            )
        elif ":" in trigger["id"]:
            findings.append(
                Finding(
                    "SDD-TRIGGER-NAME",
                    "trigger names cannot contain ':'",
                    f"{trigger_path}.name",
                )
            )
        if trigger["type"] not in TRIGGER_TYPES:
            findings.append(
                Finding(
                    "SDD-TRIGGER-TYPE",
                    f"unsupported trigger type {trigger['type']!r}",
                    f"{trigger_path}.type",
                )
            )

    variable_rows = table_after(text, "### Case Variables")
    variables = [
        {
            "name": clean(row.get("name")),
            "category": clean(row.get("category")),
            "type": normalized_type(row.get("type", "")),
            "sourceTriggers": [part.strip() for part in clean(row.get("sourcetriggers")).split(",") if part.strip()],
            "sourceFields": optional(row.get("sourcefields") or row.get("sourcefield")),
            "default": normalized_default(optional(row.get("default"))),
        }
        for row in variable_rows
        if optional(row.get("name"))
    ]
    variable_names = {variable["name"] for variable in variables}
    if len(variable_names) != len(variables):
        findings.append(Finding("SDD-VARIABLE-DUPLICATE", "Case Variable names must be unique", "variables"))
    for variable in variables:
        path_prefix = f"variables[{variable['name']}]"
        if variable["category"] not in {"In", "Out", "Variable"}:
            findings.append(Finding("SDD-VARIABLE-CATEGORY", f"invalid category {variable['category']!r}", f"{path_prefix}.category"))
        for source_trigger in variable["sourceTriggers"]:
            if source_trigger not in trigger_ids:
                findings.append(Finding("SDD-VARIABLE-TRIGGER", f"unknown source trigger {source_trigger!r}", f"{path_prefix}.sourceTriggers"))
        source_fields = variable["sourceFields"]
        if variable["category"] == "Out" and (variable["sourceTriggers"] or source_fields):
            findings.append(
                Finding(
                    "SDD-VARIABLE-SOURCE-DIRECTION",
                    "Out variables cannot declare sourceTriggers or sourceFields",
                    path_prefix,
                )
            )
        if variable["category"] == "In":
            if len(variable["sourceTriggers"]) > 1:
                findings.append(
                    Finding(
                        "SDD-VARIABLE-IN-TRIGGER",
                        "In variables can bind to at most one trigger",
                        f"{path_prefix}.sourceTriggers",
                    )
                )
            if source_fields:
                findings.append(
                    Finding(
                        "SDD-VARIABLE-IN-FIELD",
                        "In variables cannot extract a source field",
                        f"{path_prefix}.sourceFields",
                    )
                )
        if variable["category"] == "Variable":
            if variable["sourceTriggers"] and not source_fields:
                findings.append(
                    Finding(
                        "SDD-VARIABLE-SOURCE-FIELD",
                        "trigger-sourced variables require sourceFields",
                        f"{path_prefix}.sourceFields",
                    )
                )
            if source_fields and not variable["sourceTriggers"]:
                findings.append(
                    Finding(
                        "SDD-VARIABLE-SOURCE-TRIGGER",
                        "sourceFields requires sourceTriggers",
                        f"{path_prefix}.sourceTriggers",
                    )
                )
            if len(variable["sourceTriggers"]) > 1 and source_fields:
                chunks = [part.strip() for part in source_fields.split(";") if part.strip()]
                mapped: set[str] = set()
                for chunk in chunks:
                    for trigger_name in sorted(variable["sourceTriggers"], key=len, reverse=True):
                        if chunk.startswith(f"{trigger_name}:"):
                            mapped.add(trigger_name)
                            break
                if mapped != set(variable["sourceTriggers"]):
                    findings.append(
                        Finding(
                            "SDD-VARIABLE-SOURCE-MAP",
                            "multi-trigger sourceFields must key exactly one field path per source trigger",
                            f"{path_prefix}.sourceFields",
                        )
                    )

    case_exit = parse_condition_rows(table_after(text, "### Case Exit Conditions"), "markscasecomplete")
    stage_matches = list(STAGE_RE.finditer(text))
    section_three = re.search(r"^## Section 3: Personas & App Views\s*$", text, re.M)
    stage_end = section_three.start() if section_three else len(text)
    stages: list[dict[str, Any]] = []
    resources: list[dict[str, Any]] = []
    for stage_index, match in enumerate(stage_matches):
        end = stage_matches[stage_index + 1].start() if stage_index + 1 < len(stage_matches) else stage_end
        stage_block = text[match.start() : end]
        stage_name = strip_id_suffix(match.group(2))
        kind = "secondary" if match.group(1) == "Secondary Stage" else normalized_type(field(stage_block, "Stage Kind") or "primary")
        task_summary = {clean(row.get("taskname")): row for row in table_after(stage_block, "#### Tasks")}
        task_matches = list(TASK_RE.finditer(stage_block))
        tasks: list[dict[str, Any]] = []
        for task_index, task_match in enumerate(task_matches):
            task_end = task_matches[task_index + 1].start() if task_index + 1 < len(task_matches) else len(stage_block)
            task_name = strip_id_suffix(task_match.group(3))
            task = parse_task(
                stage_block[task_match.start() : task_end],
                task_name,
                stage_name,
                task_summary.get(task_name, {}),
            )
            tasks.append(task)
            if task["resource"]:
                resources.append(
                    {
                        "folder": task["resource"]["folder"],
                        "identity": task["resource"]["identity"],
                        "name": task["resource"]["name"],
                        "stage": stage_name,
                        "task": task_name,
                        "taskType": task["type"],
                    }
                )
        stages.append(
            {
                "name": stage_name,
                "kind": kind,
                "required": boolean(field(stage_block, "Required for Case Completion")),
                "interrupting": boolean(field(stage_block, "Interrupting")),
                "entryConditions": parse_condition_rows(table_after(stage_block, "#### Stage Entry Conditions"), "markscomplete"),
                "exitConditions": parse_condition_rows(table_after(stage_block, "#### Stage Exit Conditions"), "marksstagecomplete"),
                "tasks": tasks,
            }
        )

    stage_names = [stage["name"] for stage in stages]
    if not stages:
        findings.append(Finding("SDD-STAGE-MISSING", "at least one stage is required", "stages"))
    for duplicate in sorted(name for name, count in Counter(stage_names).items() if count > 1):
        findings.append(Finding("SDD-STAGE-DUPLICATE", f"duplicate stage name {duplicate!r}", f"stages[{duplicate}]"))
    for stage in stages:
        stage_path = f"stages[{stage['name']}]"
        if ":" in stage["name"]:
            findings.append(Finding("SDD-NAME-COLON", "stage names cannot contain ':'", f"{stage_path}.name"))
        if stage["kind"] not in {"primary", "secondary"}:
            findings.append(Finding("SDD-STAGE-KIND", f"invalid stage kind {stage['kind']!r}", f"{stage_path}.kind"))
        if not stage["entryConditions"]:
            findings.append(Finding("SDD-STAGE-ENTRY", "stage has no entry condition", f"{stage_path}.entryConditions"))
        if not stage["exitConditions"]:
            findings.append(Finding("SDD-STAGE-EXIT", "stage has no exit condition", f"{stage_path}.exitConditions"))
        task_names = [task["name"] for task in stage["tasks"]]
        for duplicate in sorted(name for name, count in Counter(task_names).items() if count > 1):
            findings.append(Finding("SDD-TASK-DUPLICATE", f"duplicate task name {duplicate!r}", f"{stage_path}.tasks[{duplicate}]"))
        for task in stage["tasks"]:
            task_path = f"{stage_path}.tasks[{task['name']}]"
            if task["type"] not in TASK_TYPES:
                findings.append(Finding("SDD-TASK-TYPE", f"unsupported task type {task['type']!r}", f"{task_path}.type"))
            if task["activationMode"] not in ACTIVATION_MODES:
                findings.append(
                    Finding(
                        "SDD-TASK-ACTIVATION",
                        f"unsupported activation mode {task['activationMode']!r}",
                        f"{task_path}.activationMode",
                    )
                )
            if ":" in task["name"]:
                findings.append(Finding("SDD-NAME-COLON", "task names cannot contain ':'", f"{task_path}.name"))
            if task["required"] is None:
                findings.append(Finding("SDD-TASK-REQUIRED", "task envelope must declare Required Yes/No", f"{task_path}.required"))
            if task["runOnlyOnce"] is None:
                findings.append(Finding("SDD-TASK-RUN-ONCE", "task envelope must declare Run Only Once Yes/No", f"{task_path}.runOnlyOnce"))
            if not task["entryConditions"]:
                findings.append(Finding("SDD-TASK-ENTRY", "task has no entry condition", f"{task_path}.entryConditions"))
            task_rules = {condition["rule"] for condition in task["entryConditions"]}
            activation_rule = {
                "adhoc": "adhoc",
                "fan-in": "selected-tasks-completed",
                "parallel": "current-stage-entered",
                "parallel-after-predecessor": "runs-sequentially",
                "sequential": "runs-sequentially",
            }.get(task["activationMode"])
            if activation_rule and activation_rule not in task_rules:
                findings.append(
                    Finding(
                        "SDD-TASK-ACTIVATION-RULE",
                        f"activation mode {task['activationMode']!r} requires {activation_rule!r}",
                        f"{task_path}.entryConditions",
                    )
                )

    def validate_rules(items: Iterable[dict[str, Any]], legal: frozenset[str], path_prefix: str) -> None:
        for index, item in enumerate(items):
            if item["rule"] not in legal:
                findings.append(Finding("SDD-RULE-LEGALITY", f"rule {item['rule']!r} is not legal at this gate", f"{path_prefix}[{index}].rule"))

    validate_rules(case_exit, CASE_COMPLETION_RULES | CASE_EXIT_RULES, "case.exitConditions")
    for stage in stages:
        stage_path = f"stages[{stage['name']}]"
        validate_rules(stage["entryConditions"], STAGE_ENTRY_RULES, f"{stage_path}.entryConditions")
        validate_rules(stage["exitConditions"], STAGE_COMPLETION_RULES | STAGE_EXIT_RULES, f"{stage_path}.exitConditions")
        for condition in stage["exitConditions"]:
            exit_type = condition["exitType"]
            if exit_type and exit_type not in EXIT_TYPES:
                findings.append(Finding("SDD-EXIT-TYPE", f"invalid exit type {exit_type!r}", f"{stage_path}.exitConditions"))
            legal = STAGE_COMPLETION_RULES if condition["marksComplete"] else STAGE_EXIT_RULES
            if condition["marksComplete"] is not None and condition["rule"] not in legal:
                findings.append(Finding("SDD-RULE-MARKS", "rule and Marks Stage Complete value are inconsistent", f"{stage_path}.exitConditions"))
            if exit_type == "return-to-origin" and not (
                condition["marksComplete"] is True and condition["rule"] in STAGE_COMPLETION_RULES
            ):
                findings.append(Finding("SDD-RETURN-PAIRING", "return-to-origin requires a completing stage-exit rule", f"{stage_path}.exitConditions"))
        for task in stage["tasks"]:
            validate_rules(task["entryConditions"], TASK_ENTRY_RULES, f"{stage_path}.tasks[{task['name']}].entryConditions")

    if not any(item["marksComplete"] is True and item["rule"] in CASE_COMPLETION_RULES for item in case_exit):
        findings.append(Finding("SDD-CASE-COMPLETION", "case has no completing exit rule", "case.exitConditions"))

    refs = set(re.findall(r"=vars\.([A-Za-z]\w*)", text))
    for reference in sorted(refs - variable_names):
        findings.append(Finding("SDD-VARIABLE-REFERENCE", f"undeclared variable reference {reference!r}", f"variables[{reference}]"))
    produced = set(re.findall(r"->\s*([A-Za-z]\w*)", text)) | set(re.findall(r"\b([A-Za-z]\w*)\s*=\s*(?!=)", text))
    for variable in variables:
        if (
            variable["name"] in refs
            and variable["category"] != "In"
            and variable["default"] is None
            and not variable["sourceTriggers"]
            and variable["name"] not in produced
        ):
            findings.append(Finding("SDD-VARIABLE-LINEAGE", "variable is consumed but never produced", f"variables[{variable['name']}]"))

    contract = {
        "case": {
            "name": metadata.get("casename") or case_name,
            "description": optional(metadata.get("casedescription")),
            "identifier": {"type": identifier_type, "prefix": identifier_prefix},
            "appEnabled": boolean(metadata.get("caseapp")),
            "directlyPassTaskOutputs": boolean(metadata.get("taskoutputpassing")),
            "exitConditions": case_exit,
        },
        "handoff": {
            "status": handoff.get("status"),
            "generatedBy": handoff.get("generatedby"),
            "templateValidation": handoff.get("templatevalidation"),
            "buildHandoff": build_handoff,
        },
        "triggers": triggers,
        "variables": variables,
        "stages": stages,
        "resources": resources,
    }
    return contract, sorted(set(findings))


def iter_rule_types(conditions: Iterable[dict[str, Any]]) -> list[str]:
    result: list[str] = []
    for condition in conditions:
        for group in condition.get("rules") or []:
            for rule in group or []:
                if isinstance(rule, dict) and isinstance(rule.get("rule"), str):
                    result.append(rule["rule"])
    return result


def flatten_tasks(stage: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for group_index, group in enumerate((stage.get("data") or {}).get("tasks") or []):
        for task in group or []:
            if isinstance(task, dict):
                result.append({**task, "_group": group_index})
    return result


def collect_ids(value: Any, path: str = "$") -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    if isinstance(value, dict):
        if (
            not path.endswith(".parentElement")
            and isinstance(value.get("id"), str)
            and value["id"]
        ):
            result.append((value["id"], f"{path}.id"))
        for key, nested in value.items():
            result.extend(collect_ids(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            result.extend(collect_ids(nested, f"{path}[{index}]"))
    return result


def load_caseplan(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise InputFailure(f"cannot read caseplan {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise InputFailure(f"invalid JSON in caseplan {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise InputFailure(f"caseplan root must be an object: {path}")
    return value


def check_caseplan(plan: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    if plan.get("edges") != []:
        findings.append(Finding("CASEPLAN-EDGES", "schema.edges must be an empty array", "$.edges"))
    if not isinstance(plan.get("layout"), dict):
        findings.append(Finding("CASEPLAN-LAYOUT", "top-level layout must be an object", "$.layout"))
    ids = collect_ids(plan)
    for duplicate, count in sorted(Counter(identifier for identifier, _ in ids).items()):
        if count > 1:
            paths = [path for identifier, path in ids if identifier == duplicate]
            findings.append(Finding("CASEPLAN-ID-DUPLICATE", f"id {duplicate!r} appears {count} times: {', '.join(paths)}", "$.ids"))

    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        return sorted(findings + [Finding("CASEPLAN-NODES", "nodes must be an array", "$.nodes")])
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            findings.append(
                Finding("CASEPLAN-NODE", "node must be an object", f"$.nodes[{index}]")
            )
            continue
        for layout_field in sorted(LAYOUT_FIELDS & node.keys()):
            findings.append(
                Finding(
                    "CASEPLAN-LAYOUT-FIELD",
                    f"authored node layout field {layout_field!r} is forbidden",
                    f"$.nodes[{index}].{layout_field}",
                )
            )

    def validate_actual_rules(
        conditions: Any,
        legal: frozenset[str],
        path: str,
        marks_key: str | None = None,
    ) -> None:
        if not isinstance(conditions, list):
            return
        for condition_index, condition in enumerate(conditions):
            if not isinstance(condition, dict):
                continue
            for rule in iter_rule_types([condition]):
                rule_path = f"{path}[{condition_index}].rules"
                if rule not in legal:
                    findings.append(
                        Finding(
                            "CASEPLAN-RULE-LEGALITY",
                            f"rule {rule!r} is not legal at this gate",
                            rule_path,
                        )
                    )
                if marks_key is not None and condition.get(marks_key) is not None:
                    completion_legal = (
                        STAGE_COMPLETION_RULES
                        if marks_key == "marksStageComplete"
                        else CASE_COMPLETION_RULES
                    )
                    exit_legal = (
                        STAGE_EXIT_RULES
                        if marks_key == "marksStageComplete"
                        else CASE_EXIT_RULES
                    )
                    expected = completion_legal if condition.get(marks_key) is True else exit_legal
                    if rule not in expected:
                        findings.append(
                            Finding(
                                "CASEPLAN-RULE-MARKS",
                                f"rule {rule!r} is inconsistent with {marks_key}",
                                rule_path,
                            )
                        )

    trigger_nodes = [
        node
        for node in nodes
        if isinstance(node, dict) and node.get("type") == "uipath.case.trigger"
    ]
    trigger_labels = [
        clean(((node.get("data") or {}).get("display") or {}).get("label"))
        for node in trigger_nodes
    ]
    for duplicate, count in sorted(Counter(trigger_labels).items()):
        if duplicate and count > 1:
            findings.append(
                Finding(
                    "CASEPLAN-TRIGGER-DUPLICATE",
                    f"duplicate trigger label {duplicate!r}",
                    "$.nodes",
                )
            )
    for trigger in trigger_nodes:
        data = trigger.get("data") or {}
        label = clean((data.get("display") or {}).get("label")) or clean(trigger.get("id"))
        service_type = normalized_type((data.get("inputs") or {}).get("serviceType", ""))
        actual_type = "manual" if service_type in {"", "none"} else service_type
        if actual_type not in TRIGGER_TYPES:
            findings.append(
                Finding(
                    "CASEPLAN-TRIGGER-TYPE",
                    f"unsupported trigger service type {actual_type!r}",
                    f"$.triggers[{label}].type",
                )
            )

    stages = [
        node
        for node in nodes
        if isinstance(node, dict)
        and node.get("type") in {"case-management:Stage", "case-management:ExceptionStage"}
    ]
    labels = [clean((stage.get("data") or {}).get("label")) for stage in stages]
    for duplicate, count in sorted(Counter(labels).items()):
        if duplicate and count > 1:
            findings.append(Finding("CASEPLAN-STAGE-DUPLICATE", f"duplicate stage label {duplicate!r}", "$.nodes"))
    for stage in stages:
        data = stage.get("data") or {}
        label = clean(data.get("label")) or clean(stage.get("id"))
        stage_path = f"$.stages[{label}]"
        if not data.get("entryConditions"):
            findings.append(Finding("CASEPLAN-STAGE-ENTRY", "stage has no entry condition", f"{stage_path}.entryConditions"))
        if not data.get("exitConditions"):
            findings.append(Finding("CASEPLAN-STAGE-EXIT", "stage has no exit condition", f"{stage_path}.exitConditions"))
        validate_actual_rules(
            data.get("entryConditions"), STAGE_ENTRY_RULES, f"{stage_path}.entryConditions"
        )
        validate_actual_rules(
            data.get("exitConditions"),
            STAGE_COMPLETION_RULES | STAGE_EXIT_RULES,
            f"{stage_path}.exitConditions",
            "marksStageComplete",
        )
        task_sets = data.get("tasks")
        if not isinstance(task_sets, list) or any(
            not isinstance(group, list) for group in task_sets
        ):
            findings.append(
                Finding(
                    "CASEPLAN-TASK-SETS",
                    "stage data.tasks must be a two-dimensional array",
                    f"{stage_path}.tasks",
                )
            )
        task_names: list[str] = []
        for task in flatten_tasks(stage):
            name = clean(task.get("displayName"))
            task_names.append(name)
            if task.get("type") not in TASK_TYPES:
                findings.append(Finding("CASEPLAN-TASK-TYPE", f"unsupported task type {task.get('type')!r}", f"{stage_path}.tasks[{name}].type"))
            validate_actual_rules(
                task.get("entryConditions"),
                TASK_ENTRY_RULES,
                f"{stage_path}.tasks[{name}].entryConditions",
            )
        for duplicate, count in sorted(Counter(task_names).items()):
            if duplicate and count > 1:
                findings.append(Finding("CASEPLAN-TASK-DUPLICATE", f"duplicate task displayName {duplicate!r}", f"{stage_path}.tasks"))
    exit_rules = (plan.get("metadata") or {}).get("caseExitRules") or []
    validate_actual_rules(
        exit_rules,
        CASE_COMPLETION_RULES | CASE_EXIT_RULES,
        "$.metadata.caseExitRules",
        "marksCaseComplete",
    )
    if not any(
        condition.get("marksCaseComplete") is True
        and any(rule == "required-stages-completed" for rule in iter_rule_types([condition]))
        for condition in exit_rules
        if isinstance(condition, dict)
    ):
        findings.append(Finding("CASEPLAN-CASE-COMPLETION", "metadata.caseExitRules has no completing rule", "$.metadata.caseExitRules"))
    variables = plan.get("variables") or {}
    for category in ("inputs", "outputs"):
        for index, variable in enumerate(variables.get(category) or []):
            identifier = variable.get("id") if isinstance(variable, dict) else None
            if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", identifier):
                findings.append(
                    Finding(
                        "CASEPLAN-ARGUMENT-ID",
                        "formal argument id must start with a letter or underscore",
                        f"$.variables.{category}[{index}].id",
                    )
                )
    if "$xref(" in json.dumps(plan, sort_keys=True):
        findings.append(
            Finding(
                "CASEPLAN-XREF",
                "unresolved $xref marker remains in caseplan.json",
                "$",
            )
        )
    return sorted(findings)


def caseplan_variable_map(plan: dict[str, Any]) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    result: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    variables = plan.get("variables") or {}
    for category, key in (("In", "inputs"), ("Out", "outputs"), ("Variable", "inputOutputs")):
        for item in variables.get(key) or []:
            if isinstance(item, dict) and item.get("name"):
                result.setdefault(str(item["name"]), []).append((category, item))
    return result


def finding_if_mismatch(
    findings: list[Finding], code: str, expected: Any, actual: Any, path: str
) -> None:
    if expected is not None and expected != actual:
        findings.append(Finding(code, f"expected {expected!r}; found {actual!r}", path))


def check_parity(contract: dict[str, Any], plan: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    case = contract["case"]
    metadata = plan.get("metadata") or {}
    finding_if_mismatch(findings, "PARITY-CASE-NAME", case["name"], plan.get("name"), "case.name")
    finding_if_mismatch(findings, "PARITY-CASE-DESCRIPTION", case["description"], plan.get("description"), "case.description")
    finding_if_mismatch(findings, "PARITY-CASE-ID-TYPE", case["identifier"]["type"], metadata.get("caseIdentifierType"), "case.identifier.type")
    finding_if_mismatch(findings, "PARITY-CASE-ID-PREFIX", case["identifier"]["prefix"], metadata.get("caseIdentifier"), "case.identifier.prefix")
    finding_if_mismatch(findings, "PARITY-CASE-APP", case["appEnabled"], metadata.get("caseAppEnabled"), "case.appEnabled")
    finding_if_mismatch(findings, "PARITY-OUTPUT-PASSING", case["directlyPassTaskOutputs"], metadata.get("caseDirectlyPassTaskOutputs"), "case.directlyPassTaskOutputs")

    def caseplan_trigger_type(node: dict[str, Any]) -> str:
        service_type = normalized_type(
            ((node.get("data") or {}).get("inputs") or {}).get("serviceType", "")
        )
        return "manual" if service_type in {"", "none"} else service_type

    plan_triggers = {
        clean((((node.get("data") or {}).get("display") or {}).get("label"))): node
        for node in plan.get("nodes") or []
        if isinstance(node, dict) and node.get("type") == "uipath.case.trigger"
    }
    sdd_trigger_names = {trigger["id"] for trigger in contract["triggers"]}
    for extra in sorted(set(plan_triggers) - sdd_trigger_names):
        findings.append(
            Finding(
                "PARITY-TRIGGER-EXTRA",
                "caseplan.json contains a trigger not declared by the SDD",
                f"triggers[{extra}]",
            )
        )
    for trigger in contract["triggers"]:
        name = trigger["id"]
        path = f"triggers[{name}]"
        actual = plan_triggers.get(name)
        if actual is None:
            findings.append(
                Finding(
                    "PARITY-TRIGGER-MISSING",
                    "trigger declared by the SDD is missing from caseplan.json",
                    path,
                )
            )
            continue
        finding_if_mismatch(
            findings,
            "PARITY-TRIGGER-TYPE",
            trigger["type"],
            caseplan_trigger_type(actual),
            f"{path}.type",
        )

    plan_variables = caseplan_variable_map(plan)
    for variable in contract["variables"]:
        name = variable["name"]
        entries = plan_variables.get(name, [])
        path = f"variables[{name}]"
        if not entries:
            findings.append(Finding("PARITY-VARIABLE-MISSING", "variable declared by the SDD is missing from caseplan.json", path))
            continue
        expected_category = variable["category"]
        if expected_category == "Variable":
            candidates = [item for category, item in entries if category == "Variable"]
        else:
            candidates = [item for category, item in entries if category == expected_category]
        if not candidates:
            findings.append(Finding("PARITY-VARIABLE-CATEGORY", f"expected category {expected_category!r}", f"{path}.category"))
            continue
        item = candidates[0]
        finding_if_mismatch(findings, "PARITY-VARIABLE-TYPE", variable["type"], normalized_type(item.get("type", "")), f"{path}.type")
        finding_if_mismatch(findings, "PARITY-VARIABLE-DEFAULT", variable["default"], item.get("default"), f"{path}.default")

    stage_nodes = {
        clean((node.get("data") or {}).get("label")): node
        for node in plan.get("nodes") or []
        if isinstance(node, dict)
        and node.get("type") in {"case-management:Stage", "case-management:ExceptionStage"}
    }
    sdd_stage_names = {stage["name"] for stage in contract["stages"]}
    for extra in sorted(set(stage_nodes) - sdd_stage_names):
        findings.append(Finding("PARITY-STAGE-EXTRA", "caseplan.json contains a stage not declared by the SDD", f"stages[{extra}]"))
    for stage in contract["stages"]:
        name = stage["name"]
        path = f"stages[{name}]"
        node = stage_nodes.get(name)
        if node is None:
            findings.append(Finding("PARITY-STAGE-MISSING", "stage declared by the SDD is missing from caseplan.json", path))
            continue
        data = node.get("data") or {}
        actual_kind = "secondary" if data.get("stageType") == "secondary" or node.get("type") == "case-management:ExceptionStage" else "primary"
        finding_if_mismatch(findings, "PARITY-STAGE-KIND", stage["kind"], actual_kind, f"{path}.kind")
        finding_if_mismatch(findings, "PARITY-STAGE-REQUIRED", stage["required"], data.get("isRequired"), f"{path}.required")
        expected_entry = Counter(item["rule"] for item in stage["entryConditions"])
        actual_entry = Counter(iter_rule_types(data.get("entryConditions") or []))
        finding_if_mismatch(findings, "PARITY-STAGE-ENTRY", expected_entry, actual_entry, f"{path}.entryConditions")
        expected_exit = Counter((item["rule"], item["marksComplete"], item["exitType"]) for item in stage["exitConditions"])
        actual_exit = Counter(
            (rule, condition.get("marksStageComplete"), condition.get("type"))
            for condition in data.get("exitConditions") or []
            for rule in iter_rule_types([condition])
        )
        finding_if_mismatch(findings, "PARITY-STAGE-EXIT", expected_exit, actual_exit, f"{path}.exitConditions")

        task_map = {clean(task.get("displayName")): task for task in flatten_tasks(node)}
        sdd_task_names = {task["name"] for task in stage["tasks"]}
        for extra in sorted(set(task_map) - sdd_task_names):
            findings.append(Finding("PARITY-TASK-EXTRA", "caseplan.json contains a task not declared by the SDD", f"{path}.tasks[{extra}]"))
        for task in stage["tasks"]:
            task_name = task["name"]
            task_path = f"{path}.tasks[{task_name}]"
            actual = task_map.get(task_name)
            if actual is None:
                findings.append(Finding("PARITY-TASK-MISSING", "task declared by the SDD is missing from caseplan.json", task_path))
                continue
            finding_if_mismatch(findings, "PARITY-TASK-TYPE", task["type"], actual.get("type"), f"{task_path}.type")
            finding_if_mismatch(findings, "PARITY-TASK-REQUIRED", task["required"], actual.get("isRequired"), f"{task_path}.required")
            finding_if_mismatch(findings, "PARITY-TASK-RUN-ONCE", task["runOnlyOnce"], actual.get("shouldRunOnlyOnce"), f"{task_path}.runOnlyOnce")
            expected_rules = Counter(item["rule"] for item in task["entryConditions"])
            actual_rules = Counter(iter_rule_types(actual.get("entryConditions") or []))
            finding_if_mismatch(findings, "PARITY-TASK-ENTRY", expected_rules, actual_rules, f"{task_path}.entryConditions")
            plan_inputs = {
                clean(item.get("name"))
                for item in (actual.get("data") or {}).get("inputs") or []
                if isinstance(item, dict) and item.get("name")
            }
            expected_inputs = {item["field"] for item in task["inputs"]}
            if plan_inputs and expected_inputs != plan_inputs:
                findings.append(Finding("PARITY-TASK-INPUTS", f"expected input fields {sorted(expected_inputs)!r}; found {sorted(plan_inputs)!r}", f"{task_path}.inputs"))

        parallel_sets: dict[tuple[str, tuple[tuple[str, tuple[str, ...], str], ...]], set[int]] = {}
        for task in stage["tasks"]:
            if task["activationMode"] not in {"parallel", "parallel-after-predecessor"}:
                continue
            actual = task_map.get(task["name"])
            if actual is None:
                continue
            signature = tuple(
                sorted(
                    (
                        condition["rule"],
                        tuple(condition["arguments"]),
                        condition["condition"] or "",
                    )
                    for condition in task["entryConditions"]
                )
            )
            key = (task["activationMode"], signature)
            parallel_sets.setdefault(key, set()).add(actual["_group"])
        if any(len(groups) > 1 for groups in parallel_sets.values()):
            findings.append(
                Finding(
                    "PARITY-TASK-GROUP",
                    "parallel tasks with the same entry behavior must share one task set",
                    f"{path}.tasks",
                )
            )

    expected_case_exit = Counter(
        (item["rule"], item["marksComplete"]) for item in case["exitConditions"]
    )
    actual_case_exit = Counter(
        (rule, condition.get("marksCaseComplete"))
        for condition in metadata.get("caseExitRules") or []
        for rule in iter_rule_types([condition])
    )
    finding_if_mismatch(findings, "PARITY-CASE-EXIT", expected_case_exit, actual_case_exit, "case.exitConditions")
    return sorted(findings)


def summary(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "case": contract["case"]["name"],
        "resources": len(contract["resources"]),
        "stages": len(contract["stages"]),
        "tasks": sum(len(stage["tasks"]) for stage in contract["stages"]),
        "triggers": len(contract["triggers"]),
        "variables": len(contract["variables"]),
    }


def emit(payload: dict[str, Any], output: str) -> None:
    if output == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if payload.get("ok"):
        print(f"OK: {payload['command']}")
        if payload.get("summary"):
            print(json.dumps(payload["summary"], sort_keys=True))
    else:
        print(f"FAIL: {payload['command']}", file=sys.stderr)
        for finding in payload.get("findings", []):
            print(f"  {finding['code']} {finding['path']}: {finding['message']}", file=sys.stderr)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)
    for name in ("inspect-sdd", "check-sdd"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--sdd", required=True, type=Path)
        sub.add_argument("--output", choices=("json", "text"), default="text")
    sub = subparsers.add_parser("check-caseplan")
    sub.add_argument("--caseplan", required=True, type=Path)
    sub.add_argument("--output", choices=("json", "text"), default="text")
    sub = subparsers.add_parser("check-parity")
    sub.add_argument("--sdd", required=True, type=Path)
    sub.add_argument("--caseplan", required=True, type=Path)
    sub.add_argument("--output", choices=("json", "text"), default="text")
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command in {"inspect-sdd", "check-sdd"}:
            contract, findings = parse_sdd(args.sdd)
            payload: dict[str, Any] = {
                "command": args.command,
                "findings": [asdict(finding) for finding in findings],
                "ok": not findings,
                "summary": summary(contract),
            }
            if args.command == "inspect-sdd":
                payload["contract"] = contract
            emit(payload, args.output)
            return 0 if not findings else 1
        if args.command == "check-caseplan":
            findings = check_caseplan(load_caseplan(args.caseplan))
            payload = {
                "command": args.command,
                "findings": [asdict(finding) for finding in findings],
                "ok": not findings,
            }
            emit(payload, args.output)
            return 0 if not findings else 1
        contract, sdd_findings = parse_sdd(args.sdd)
        plan = load_caseplan(args.caseplan)
        findings = sdd_findings + check_caseplan(plan)
        if not sdd_findings:
            findings += check_parity(contract, plan)
        findings = sorted(set(findings))
        payload = {
            "command": args.command,
            "findings": [asdict(finding) for finding in findings],
            "ok": not findings,
            "summary": summary(contract),
        }
        emit(payload, args.output)
        return 0 if not findings else 1
    except InputFailure as exc:
        payload = {
            "command": args.command,
            "findings": [asdict(Finding("INPUT", str(exc), "$"))],
            "ok": False,
        }
        emit(payload, args.output)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
