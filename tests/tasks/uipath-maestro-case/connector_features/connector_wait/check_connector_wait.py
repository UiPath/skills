#!/usr/bin/env python3
"""ConnectorWaitCase: a RESOLVED wait-for-connector task AND entry rule are wired.

Asserts the connector-trigger plugin resolved a real Integration Service event
into the caseplan (Rule 8 — no fabricated IDs) with the correct serviceType,
rather than leaving a `data: {}` skeleton. Does NOT run debug: a
wait-for-connector suspends waiting for a real external event.

Also asserts the task-entry `wait-for-connector` RULE was upgraded past its
Phase 2 stub. The stub written at Step 10 already carries
serviceType='Intsvc.WaitForEvent' and two "placeholder" context entries, so
serviceType alone does not prove Phase 3 Step 10.5 ran. A stub left behind
passes `uip maestro case validate` (which only checks that rule.uipath +
context are present) and faults only at debug/run — this checker is the guard.

Not covered here: whether Step 10.5 Phase C projected the rule's Connection
into bindings_v2.json. This fixture gives the rule and the task the same
connection id, and bindings_v2 groups by resourceKey, so the two collapse into
one entry — a rule-specific assertion cannot be written against it. Covering it
needs a fixture where the rule and task use different connections.
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
    """Stage id of the stage whose data.tasks contains target_task.

    A connector rule's elementId prefix is the OWNING STAGE id even for a
    task-entry rule — a documented pitfall, so the check must compare the whole
    string rather than a suffix.
    """
    for node in plan.get("nodes") or []:
        lanes = ((node.get("data") or {}).get("tasks")) or []
        for lane in lanes:
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
    raw_context = uipath.get("context") or []
    rule_context = [entry for entry in raw_context if isinstance(entry, dict)]
    if raw_context and not rule_context:
        sys.exit(
            "FAIL: the entry rule's uipath.context is not a list of objects; got "
            f"{raw_context!r}"
        )
    stubbed = sorted(
        entry.get("name") or "<unnamed>"
        for entry in rule_context
        if entry.get("value") == "placeholder"
    )
    if not rule_context or stubbed:
        sys.exit(
            "FAIL: the wait-for-connector ENTRY RULE still carries its Phase 2 stub "
            f"uipath — context={rule_context!r}, placeholder entries={stubbed}. "
            "Phase 3 Step 10.5 must replace the stub with the case-spec-minted "
            "block. serviceType alone does not prove the upgrade ran: the stub "
            "sets it too, and validate accepts a stub."
        )
    rule_ck_entry = next(
        (entry for entry in rule_context if entry.get("name") == "connectorKey"), None
    )
    rule_ck = rule_ck_entry.get("value") if rule_ck_entry else None
    if rule_ck != "uipath-microsoft-outlook365":
        sys.exit(
            "FAIL: entry rule connectorKey must be 'uipath-microsoft-outlook365'; "
            f"got {rule_ck!r} — rule may have resolved against the mock connector"
        )
    rule_id = (rule or {}).get("id")
    stage_id = _owning_stage_id(plan, event_task)
    expected_eid = f"{stage_id}-{rule_id}"
    for slot in ("inputs", "outputs"):
        for entry in uipath.get(slot) or []:
            if not isinstance(entry, dict):
                continue
            eid = entry.get("elementId")
            if eid != expected_eid:
                sys.exit(
                    f"FAIL: entry rule {slot}[{entry.get('name')!r}].elementId must be "
                    f"{expected_eid!r} (the OWNING STAGE id, not the task id, per "
                    f"task-entry-conditions/impl-json.md); got {eid!r}"
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
        f"(connectorKey={rule_ck!r}, {len(rule_context)} context entries, no "
        f"placeholders); wait-for-connector task resolved "
        f"(displayName={task.get('displayName')!r}, "
        f"serviceType={svc}, connectorKey={ck!r}, typeId + connectionId set)"
    )


if __name__ == "__main__":
    main()
