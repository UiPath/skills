#!/usr/bin/env python3
"""FlowProcessCase: the flow-process task binds the deployed
CaseEvalFlowFixture flow as a bare `process` (no resourceSubType), wires the
invoice number in and the flow's `status` out, and the debugged case runs the
task to completion."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.case_check import (  # noqa: E402
    _get_ci,
    assert_task_type_present,
    find_caseplan,
    read_caseplan,
    run_debug,
)

FLOW = "CaseEvalFlowFixture"
FOLDER = "Shared/CaseEvalFlowFixture"
BOUND_VAR = "ackStatus"


def binding(plan: dict, ref: object) -> dict:
    ref = str(ref or "")
    if not ref.startswith("=bindings."):
        sys.exit(f"FAIL: expected a =bindings.<id> reference, got {ref!r}.")
    found = next((b for b in plan.get("bindings") or [] if b.get("id") == ref.removeprefix("=bindings.")), None)
    if found is None:
        sys.exit(f"FAIL: {ref!r} names no root binding.")
    return found


def check_structure(plan: dict, task: dict) -> None:
    data = task.get("data") or {}
    name = binding(plan, data.get("name"))
    folder = binding(plan, data.get("folderPath"))
    for b, attr, expected in ((name, "name", FLOW), (folder, "folderPath", FOLDER)):
        if b.get("resource") != "process" or "resourceSubType" in b:
            sys.exit(f"FAIL: the {attr} binding is resource={b.get('resource')!r} subType={b.get('resourceSubType')!r}; "
                     "the Designer binds a flow as a bare `process`.")
        if b.get("propertyAttribute") != attr or b.get("default") != expected:
            sys.exit(f"FAIL: the {attr} binding defaults to {b.get('default')!r} ({b.get('propertyAttribute')!r}), expected {expected!r}.")
    inputs = {i.get("name"): i.get("value") for i in data.get("inputs") or []}
    if "invoiceNumber" not in str(inputs.get("invoiceNumber", "")):
        sys.exit(f"FAIL: the flow's invoiceNumber input is {inputs.get('invoiceNumber')!r}, expected the case variable invoiceNumber.")
    status = next((o for o in data.get("outputs") or [] if o.get("name") == "status"), None)
    if status is None or status.get("var") != BOUND_VAR:
        sys.exit(f"FAIL: the SDD's `status -> {BOUND_VAR}` row did not bind: {status!r}")


def assert_task_completed(payload: dict, task: dict) -> None:
    """Case debug reports element executions, not variable values, so the task's
    own execution reaching Completed is what the run can prove."""
    executions = _get_ci(payload, "elementExecutions", "ElementExecutions") or []
    runs = [e for e in executions if _get_ci(e, "elementId", "ElementId") == task.get("id")]
    if not runs:
        sys.exit(f"FAIL: debug has no execution for task {task.get('displayName')!r} (id {task.get('id')!r}).")
    status = _get_ci(runs[-1], "status", "Status")
    if status not in ("Completed", "Successful"):
        sys.exit(f"FAIL: debug execution for task {task.get('displayName')!r} finished {status!r}.")


def main():
    plan_path = find_caseplan("FlowProcessCase/**/caseplan.json")
    plan = read_caseplan(plan_path)
    task = assert_task_type_present("flow-process", caseplan_path=plan_path)
    check_structure(plan, task)
    payload = run_debug(timeout=540)
    assert_task_completed(payload, task)
    print(f"OK: flow-process task binds {FLOW} in {FOLDER}; debug Completed, task executed")


if __name__ == "__main__":
    main()
