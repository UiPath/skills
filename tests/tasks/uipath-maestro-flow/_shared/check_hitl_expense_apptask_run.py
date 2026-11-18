#!/usr/bin/env python3
"""ExpenseAppTask (skill-hitl-e2e-apptask-brownfield): the review step uses the
tenant's deployed ExpenseReviewApp, and a real run waits on it.

`structure`: the flow has a human-in-the-loop step backed by ExpenseReviewApp
(Shared/uipath-agents/ExpenseReviewSol on the codereval tenant), named by app
name, resource key or system name, not an inline quick form.

`run` (default):
1. Debug the flow with a fresh expense id.
2. The run created an Action Center app task whose data shows that expense id,
   the employee and the amount.
3. Complete it with the app's `approve` outcome.
4. The run then completed, the fixture's SAP posting step completed, and the
   named outputs are status = "posted", sapDocumentNumber = "SAPEXP-<id>".

ExpenseReviewApp's schema (retrieve-configuration on the tenant, run
2026-11-17_04-23-30, skill-agent-inline-external-escalation-tool): input
`Content` (string), inOut `Comment` (string), outcomes `approve`, `reject`.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hitl_live_run as live  # noqa: E402
from flow_check import (  # noqa: E402
    _fail_with_capture,
    assert_named_equals,
    find_project_dir,
)

APP_MARKERS = (
    "ExpenseReviewApp",
    "a30ac44f-8ebf-4124-9746-abc93a5ae17d",  # resource key
    "ID5dcddde3c89d4a299e6f031e31568900",  # appSystemName
)
POSTING_MARKER = "SAPEXP-"  # the fixture's posting script builds the document number
DEADLINE_SECONDS = 600
CLI_TIMEOUT = 540
EMPLOYEE = "Dana Whitfield"
AMOUNT = 1840.5
DESCRIPTION = "Client workshop travel, Berlin"


def app_hitl(flow: dict) -> dict | None:
    for node in live.hitl_nodes(flow):
        text = json.dumps(node)
        quick = node.get("type") == "uipath.human-in-the-loop.quick-form" or (
            (node.get("inputs") or {}).get("type") == "quick"
        )
        if not quick and any(m in text for m in APP_MARKERS):
            return node
    return None


def posting_ids(flow: dict) -> set[str]:
    return {
        str(n.get("id"))
        for n in flow.get("nodes") or []
        if POSTING_MARKER in json.dumps((n.get("inputs") or {}))
    }


def structure(project_dir: str) -> None:
    flow = live.load_flow(project_dir)
    node = app_hitl(flow)
    if node is None:
        types = [n.get("type") for n in live.hitl_nodes(flow)]
        live.fail(
            "no human-in-the-loop step backed by the deployed ExpenseReviewApp "
            f"(human steps found: {types})"
        )
    if not posting_ids(flow):
        live.fail("the existing SAP posting step is gone")
    print(f"OK: {node.get('id')} ({node.get('type')}) uses ExpenseReviewApp; the posting step is kept")


def run(project_dir: str) -> None:
    flow = live.load_flow(project_dir)
    node = app_hitl(flow)
    if node is None:
        live.fail("no human-in-the-loop step backed by ExpenseReviewApp to run")
    hitl_id = str(node.get("id"))
    expense = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    inputs = {
        "expenseId": expense,
        "employeeName": EMPLOYEE,
        "amount": AMOUNT,
        "description": DESCRIPTION,
    }
    deadline = time.monotonic() + DEADLINE_SECONDS
    debug = live.start_debug(project_dir, inputs, CLI_TIMEOUT)
    try:
        ids = live.wait_for_ids(debug, deadline)
        print(f"run: folder {ids.folder_id}, job {ids.job_key}, instance {ids.instance_id}")
        task, notes = live.find_run_task(
            ids, lambda _row, bundle: live.has_text(bundle, expense), deadline, debug
        )
        if task is None:
            live.fail(
                f"the run created no open Action Center task for expense {expense}; "
                f"{'; '.join(notes)}; stderr tail: {debug.stderr()[-1500:]}"
            )
        missing = [
            label
            for label, ok in (
                (f"expense id {expense}", live.has_text(task.data, expense)),
                (f"employee {EMPLOYEE!r}", live.has_text(task.data, EMPLOYEE)),
                (f"amount {AMOUNT}", live.has_amount(task.data, AMOUNT)),
            )
            if not ok
        ]
        if missing:
            live.fail(
                f"task {task.task_id} does not show the reviewer {', '.join(missing)}; "
                f"data={str(task.data)[:1500]}"
            )
        if task.task_type.lower() != "apptask":
            live.fail(f"task {task.task_id} is a {task.task_type}, not an app task")
        print(f"OK: app task {task.task_id} shows {expense}, {EMPLOYEE}, {AMOUNT}")
        data = dict(task.data) if isinstance(task.data, dict) else {}
        if not data.get("Comment"):
            data["Comment"] = "Approved by the eval grader"
        live.complete_task(task, ["approve", "Approve"], data)
        payload = live.wait_for_result(debug, deadline)
    except SystemExit:
        live.cancel(debug)
        raise
    live.require_completed(payload)
    done = live.completed_ids(payload)
    if hitl_id not in done:
        _fail_with_capture(f"the review step {hitl_id} did not complete in the run")
    posted = posting_ids(flow) & done
    if not posted:
        _fail_with_capture(
            f"the SAP posting step {sorted(posting_ids(flow))} did not run after approval"
        )
    print(f"OK: review {hitl_id} and posting {sorted(posted)} completed")
    assert_named_equals(payload, "status", "posted")
    assert_named_equals(payload, "sapDocumentNumber", f"SAPEXP-{expense}", case_sensitive=True)
    print(f"OK: status=posted, sapDocumentNumber=SAPEXP-{expense}")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    project_dir = find_project_dir()
    if mode == "structure":
        structure(project_dir)
    elif mode == "run":
        run(project_dir)
    else:
        live.fail(f"unknown mode {mode!r}")


if __name__ == "__main__":
    main()
