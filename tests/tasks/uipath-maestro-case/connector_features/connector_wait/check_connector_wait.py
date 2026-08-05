#!/usr/bin/env python3
"""ConnectorWaitCase: a RESOLVED wait-for-connector task and entry rule are wired.

Asserts the connector-trigger plugin resolved a real Integration Service event
into the caseplan (Rule 8 — no fabricated IDs) with the correct serviceType,
rather than leaving a `data: {}` skeleton. Does NOT run debug: a
wait-for-connector suspends waiting for a real external event.

The task-entry rule must also be upgraded past its Phase 2 stub. The stub has
the final serviceType, so checking serviceType alone would let a non-runnable
`connectorKey: "placeholder"` rule pass.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.case_check import (  # noqa: E402
    assert_task_type_present,
    first_rule_of_condition,
    iter_tasks,
    read_caseplan,
    task_is_skeleton,
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

    task = assert_task_type_present("wait-for-connector")
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
    print(
        f"OK: first task is event-triggered with wait-for-connector-only entry "
        f"semantics and its entry rule is upgraded past the Phase 2 stub "
        f"(connectorKey={rule_ck!r}, no placeholders); wait-for-connector task resolved "
        f"(displayName={task.get('displayName')!r}, "
        f"serviceType={svc}, connectorKey={ck!r}, typeId + connectionId set)"
    )


if __name__ == "__main__":
    main()
