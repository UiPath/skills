#!/usr/bin/env python3
"""ConnectorWaitCase: a RESOLVED wait-for-connector task is wired.

Asserts the connector-trigger plugin resolved a real Integration Service event
into the caseplan (Rule 8 — no fabricated IDs) with the correct serviceType,
rather than leaving a `data: {}` skeleton. Does NOT run debug: a
wait-for-connector suspends waiting for a real external event.
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
        f"semantics; wait-for-connector task resolved "
        f"(displayName={task.get('displayName')!r}, "
        f"serviceType={svc}, connectorKey={ck!r}, typeId + connectionId set)"
    )


if __name__ == "__main__":
    main()
