#!/usr/bin/env python3
"""ConnectorWaitCase: connector task type and activation stay independent.

Asserts the connector-trigger plugin resolved a real Integration Service event
into the caseplan (Rule 8 — no fabricated IDs) with the correct serviceType,
rather than leaving a `data: {}` skeleton, while preserving the typed task's
positional entry rule. Does NOT run debug: a wait-for-connector suspends waiting
for a real external event.

The task-entry rule must also be upgraded past its Phase 2 stub. The stub has
the final serviceType, so checking serviceType alone would let a non-runnable
`connectorKey: "placeholder"` rule pass.
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    first_rule_of_condition,
    iter_tasks,
    read_caseplan,
    task_is_skeleton,
)

TASKS_PLAN = Path("tasks/tasks.md")


def _task_plan_section(tasks_md: str, task_name: str) -> str:
    pattern = re.compile(
        rf'(?ims)^##\s+T\d+:(?![^\n]*\btask[- ]entry[- ]condition\b)'
        rf'[^\n]*\btask\s+"{re.escape(task_name)}"[^\n]*\n'
        rf'.*?(?=^##\s+T\d+:|\Z)'
    )
    matches = pattern.findall(tasks_md)
    if len(matches) != 1:
        sys.exit(
            f"FAIL: tasks/tasks.md must contain exactly one task T-entry for "
            f"{task_name!r}; found {len(matches)}"
        )
    return matches[0]


def _task_plan_field(section: str, task_name: str, field: str) -> str:
    values = re.findall(rf"(?im)^-\s*{re.escape(field)}:\s*(.*?)\s*$", section)
    if len(values) != 1:
        sys.exit(
            f"FAIL: tasks/tasks.md T-entry for {task_name!r} must contain exactly "
            f"one {field!r} field; found {len(values)}"
        )
    return values[0].strip()


def _assert_plan_activation() -> None:
    if not TASKS_PLAN.is_file():
        sys.exit(f"FAIL: {TASKS_PLAN} is missing; the Phase 1 plan is required")
    tasks_md = TASKS_PLAN.read_text(encoding="utf-8", errors="ignore")
    expected = {
        "Process reply event": ("event-triggered", "wait-for-connector"),
        "Wait for reply email": ("parallel", "current-stage-entered"),
    }
    for task_name, (expected_mode, expected_rule) in expected.items():
        section = _task_plan_section(tasks_md, task_name)
        activation_mode = _task_plan_field(section, task_name, "activation-mode")
        entry_rule = _task_plan_field(section, task_name, "entry-rule")
        if activation_mode != expected_mode or entry_rule != expected_rule:
            sys.exit(
                f"FAIL: tasks/tasks.md T-entry for {task_name!r} must preserve "
                f"activation-mode: {expected_mode} with entry-rule: {expected_rule}; "
                f"got activation-mode={activation_mode!r}, entry-rule={entry_rule!r}"
            )


def _owning_stage_id(plan: dict, target_task: dict) -> str:
    for node in plan.get("nodes") or []:
        for lane in ((node.get("data") or {}).get("tasks")) or []:
            for task in lane or []:
                if task is target_task:
                    return node.get("id")
    sys.exit("FAIL: could not locate the stage owning the event-triggered task")


def _find_task_by_label(plan: dict, label: str) -> dict:
    for task in iter_tasks(plan):
        if task.get("displayName") == label or task.get("label") == label:
            return task
    labels = [
        task.get("displayName") or task.get("label")
        for task in iter_tasks(plan)
    ]
    sys.exit(f"FAIL: task {label!r} not found; saw {labels}")


def _entry_rules(task: dict) -> list[dict]:
    return [
        rule
        for condition in (task.get("entryConditions") or [])
        for group in (condition.get("rules") or [])
        for rule in (group or [])
        if isinstance(rule, dict)
    ]


def main():
    plan = read_caseplan()

    event_task = _find_task_by_label(plan, "Process reply event")
    rules = [
        (first_rule_of_condition(condition) or {}).get("rule")
        for condition in (event_task.get("entryConditions") or [])
    ]
    if rules != ["wait-for-connector"]:
        sys.exit(
            "FAIL: first event-triggered task must have only wait-for-connector "
            f"entry semantics; got {rules!r}"
        )
    rule = first_rule_of_condition((event_task.get("entryConditions") or [None])[0])
    uipath = (rule or {}).get("uipath") or {}
    if uipath.get("serviceType") != "Intsvc.WaitForEvent":
        sys.exit(
            "FAIL: first task's wait-for-connector entry rule must carry "
            f"uipath.serviceType='Intsvc.WaitForEvent'; got {uipath.get('serviceType')!r}"
        )
    rule_context = [
        entry for entry in (uipath.get("context") or []) if isinstance(entry, dict)
    ]
    placeholder_names = sorted(
        entry.get("name") or "<unnamed>"
        for entry in rule_context
        if entry.get("value") == "placeholder"
    )
    if not rule_context or placeholder_names:
        sys.exit(
            "FAIL: wait-for-connector entry rule still has its Phase 2 stub; "
            f"context={rule_context!r}, placeholder entries={placeholder_names!r}"
        )
    rule_ck_entry = next(
        (entry for entry in rule_context if entry.get("name") == "connectorKey"), None
    )
    rule_ck = rule_ck_entry.get("value") if rule_ck_entry else None
    if rule_ck != "uipath-microsoft-outlook365":
        sys.exit(
            "FAIL: entry rule connectorKey must be "
            f"'uipath-microsoft-outlook365'; got {rule_ck!r}"
        )
    expected_element_id = f"{_owning_stage_id(plan, event_task)}-{rule.get('id')}"
    for slot in ("inputs", "outputs"):
        for entry in uipath.get(slot) or []:
            if isinstance(entry, dict) and entry.get("elementId") != expected_element_id:
                sys.exit(
                    f"FAIL: entry rule {slot}[{entry.get('name')!r}].elementId "
                    f"must be {expected_element_id!r}; got {entry.get('elementId')!r}"
                )
    if event_task.get("isRequired") is not False:
        sys.exit(
            "FAIL: event-triggered placeholder process should stay non-required; "
            f"got isRequired={event_task.get('isRequired')!r}"
        )

    assert_task_type_present("wait-for-connector")
    task = _find_task_by_label(plan, "Wait for reply email")
    if task.get("type") != "wait-for-connector":
        sys.exit(
            "FAIL: 'Wait for reply email' must keep type='wait-for-connector'; "
            f"got {task.get('type')!r}"
        )
    task_rules = _entry_rules(task)
    if len(task_rules) != 1 or task_rules[0].get("rule") != "current-stage-entered":
        sys.exit(
            "FAIL: typed wait-for-connector task must preserve exactly one "
            "current-stage-entered entry rule; "
            f"got {task_rules!r}"
        )
    if "uipath" in task_rules[0]:
        sys.exit(
            "FAIL: typed wait-for-connector task's positional "
            "current-stage-entered rule must not carry a connector uipath payload; "
            f"got {task_rules[0].get('uipath')!r}"
        )
    if task_is_skeleton(task):
        sys.exit(
            "FAIL: wait-for-connector task is a skeleton (missing data.typeId / "
            "data.connectionId) — the connector event must resolve against a "
            "live Integration Service connection on the tenant"
        )
    data = task.get("data") or {}
    svc = data.get("serviceType")
    if svc != "Intsvc.WaitForEvent":
        sys.exit(
            f"FAIL: wait-for-connector data.serviceType must be "
            f"'Intsvc.WaitForEvent'; got {svc!r}"
        )
    context = data.get("context", [])
    ck_entry = next((c for c in context if c.get("name") == "connectorKey"), None)
    ck = ck_entry.get("value") if ck_entry else None
    if ck != "uipath-microsoft-outlook365":
        sys.exit(
            f"FAIL: expected connectorKey 'uipath-microsoft-outlook365'; got {ck!r} — "
            "agent may have resolved against the mock connector"
        )
    _assert_plan_activation()
    print(
        f"OK: first task is event-triggered with wait-for-connector-only entry "
        f"semantics and its entry rule is upgraded past the Phase 2 stub "
        f"(connectorKey={rule_ck!r}, no placeholders); typed wait-for-connector "
        f"task preserves one positional "
        f"parallel/current-stage-entered plan pair, has no connector uipath on "
        f"that entry rule, and is resolved "
        f"(displayName={task.get('displayName')!r}, "
        f"serviceType={svc}, connectorKey={ck!r}, typeId + connectionId set)"
    )


if __name__ == "__main__":
    main()
