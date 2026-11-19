#!/usr/bin/env python3
"""ExpenseAppTask (skill-hitl-e2e-apptask-brownfield): the review step uses the
tenant's deployed ExpenseReviewApp, and real runs wait on it.

`structure`: the flow has a human-in-the-loop step backed by ExpenseReviewApp
(Shared/uipath-agents/ExpenseReviewSol on the codereval tenant), named by app
name, resource key or system name, not an inline quick form.

`run` (default) debugs the flow twice, each with a fresh expense id:
1. The run created an Action Center app task whose data shows that expense id,
   the employee and the amount.
2. Approve run: the grader completes it with the app's `approve` outcome; the
   run then completed, the review and the fixture's SAP posting step
   completed, and the named outputs are status = "posted",
   sapDocumentNumber = "SAPEXP-<id>".
3. Reject run: the grader completes it with `reject`; the run then completed,
   the review completed, the posting step did not run, and status =
   "rejected". An app task has one `completed` port, so where the flow routes
   on the outcome is not pinned: the two runs show posting happens on approve
   only. No output proves a rejection posted nothing here, so the posting must
   be a dedicated node. Before either run, the posting step must sit behind
   the review: the trigger cannot reach it without passing through the review
   step.

A run that did not complete is cancelled. ExpenseReviewApp's schema (as
`retrieve-configuration` reports it on the tenant): input `Content` (string),
inOut `Comment` (string), outcomes `approve`, `reject`.
"""

from __future__ import annotations

import json
import os
import sys
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


def structure(project_dir: str) -> None:
    flow = live.load_flow(project_dir)
    node = app_hitl(flow)
    if node is None:
        types = [n.get("type") for n in live.hitl_nodes(flow)]
        live.fail(
            "no human-in-the-loop step backed by the deployed ExpenseReviewApp "
            f"(human steps found: {types})"
        )
    if not live.posting_steps(flow, POSTING_MARKER):
        live.fail("the existing SAP posting step is gone")
    print(f"OK: {node.get('id')} ({node.get('type')}) uses ExpenseReviewApp; the posting step is kept")


def run_once(project_dir: str, node: dict, actions: list[str], comment: str) -> tuple[dict, str]:
    """Debug the flow, check the run's app task, answer it with `actions`, and
    return the completed run's payload and expense id."""
    expense = f"EXP-{uuid.uuid4().hex[:8].upper()}"
    inputs = {
        "expenseId": expense,
        "employeeName": EMPLOYEE,
        "amount": AMOUNT,
        "description": DESCRIPTION,
    }
    payload = live.run_with_task(
        project_dir,
        inputs,
        expense,
        node,
        actions,
        lambda task: check_task(task, expense),
        lambda task: answer_data(task, comment),
        "expense",
    )
    return payload, expense


def check_task(task: live.FoundTask, expense: str) -> None:
    missing = [
        label
        for label, ok in (
            (f"expense id {expense}", live.has_text(task.data, expense)),
            (f"employee {EMPLOYEE!r}", live.has_text(task.data, EMPLOYEE)),
            (f"amount {AMOUNT}", live.has_amount(task.data, AMOUNT)),
            (f"description {DESCRIPTION!r}", live.has_text(task.data, DESCRIPTION)),
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
    print(f"OK: app task {task.task_id} shows {expense}, {EMPLOYEE}, {AMOUNT}, {DESCRIPTION}")


def answer_data(task: live.FoundTask, comment: str) -> dict:
    data = dict(task.data) if isinstance(task.data, dict) else {}
    if not data.get("Comment"):
        data["Comment"] = comment
    return data


def run(project_dir: str) -> None:
    flow = live.load_flow(project_dir)
    node = app_hitl(flow)
    if node is None:
        live.fail("no human-in-the-loop step backed by ExpenseReviewApp to run")
    hitl_id = str(node.get("id"))
    posting = live.posting_steps(flow, POSTING_MARKER)
    early = sorted(posting & live.bypassing(flow, hitl_id))
    if early:
        live.fail(f"the SAP posting step(s) {early} can run without the manager's review: "
                  f"the trigger reaches them without passing through {hitl_id}")

    payload, expense = run_once(project_dir, node, ["approve", "Approve"], "Approved by the eval grader")
    done = live.completed_ids(payload)
    if hitl_id not in done:
        _fail_with_capture(f"the review step {hitl_id} did not complete in the run")
    posted = posting & done
    if not posted:
        _fail_with_capture(f"the SAP posting step {sorted(posting)} did not run after approval")
    print(f"OK: review {hitl_id} and posting {sorted(posted)} completed")
    assert_named_equals(payload, "status", "posted")
    assert_named_equals(payload, "sapDocumentNumber", f"SAPEXP-{expense}", case_sensitive=True)
    print(f"OK: status=posted, sapDocumentNumber=SAPEXP-{expense}")

    payload, _expense = run_once(project_dir, node, ["reject", "Reject"], "Rejected by the eval grader")
    done = live.completed_ids(payload)
    if hitl_id not in done:
        _fail_with_capture(f"the review step {hitl_id} did not complete in the reject run")
    if posting & done:
        _fail_with_capture(f"the SAP posting step {sorted(posting & done)} ran after a rejection")
    assert_named_equals(payload, "status", "rejected")
    print("OK: after a rejection nothing was posted and status=rejected")


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
