#!/usr/bin/env python3
"""InvoiceApproval (skill-hitl-e2e-invoice-approval-greenfield): run the flow
for real, act as the finance manager, and check what the run did.

1. Debug the flow with a fresh invoice number, so the run's task is told apart
   from any other open task in the folder.
2. The run created an Action Center task whose data shows that invoice number,
   the vendor, the total amount and the currency.
3. Complete the task with the Approve outcome.
4. The run then completed; the HITL step completed; a step reachable only
   from the Approve outcome (the SAP posting) completed, and no step reachable
   only from Reject ran.
5. The named outputs: status = "posted", sapDocumentNumber = "SAP-<invoice>".

Any layout is accepted: per-outcome ports or one port into a switch on the
decision; nothing here pins node ids, labels or variable names.
"""

from __future__ import annotations

import os
import sys
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hitl_live_run as live  # noqa: E402
from flow_check import (  # noqa: E402
    _get_ci,
    _fail_with_capture,
    assert_named_equals,
    find_project_dir,
)

DEADLINE_SECONDS = 600
CLI_TIMEOUT = 540
VENDOR = "Northwind Office Supplies"
AMOUNT = 4870.25
CURRENCY = "EUR"
TEXT_ANSWER = "Approved by the eval grader"


def outcome_plan(hitl: dict) -> tuple[list[str], set[str], set[str]]:
    """(approve action names to try, Approve ports, Reject ports)."""
    outcomes = ((hitl.get("inputs") or {}).get("schema") or {}).get("outcomes") or []
    approve, approve_ports, reject_ports = [], set(), set()
    for o in outcomes:
        name, oid = str(o.get("name") or ""), str(o.get("id") or "")
        label = f"{name} {oid}".lower()
        if "approv" in label:
            approve += [name, oid]
            approve_ports.add(f"outcome-{oid}")
        elif "reject" in label:
            reject_ports.add(f"outcome-{oid}")
    return approve or ["Approve"], approve_ports, reject_ports


def completion_data(hitl: dict, existing: object) -> dict:
    data = dict(existing) if isinstance(existing, dict) else {}
    for f in ((hitl.get("inputs") or {}).get("schema") or {}).get("fields") or []:
        fid = f.get("id")
        if not fid or f.get("direction") not in ("output", "inOut") or data.get(fid) not in (None, ""):
            continue
        kind = str(f.get("type") or "").lower()
        data[fid] = 0 if kind in ("number", "integer", "float", "double") else (
            True if kind == "boolean" else TEXT_ANSWER
        )
    return data


def check_task_data(task: live.FoundTask, invoice: str) -> None:
    bundle = {"title": _get_ci(task.row, "Title"), "data": task.data}
    missing = []
    if not live.has_text(bundle, invoice):
        missing.append(f"invoice number {invoice}")
    if not live.has_text(bundle, VENDOR):
        missing.append(f"vendor {VENDOR!r}")
    if not live.has_amount(task.data, AMOUNT):
        missing.append(f"total amount {AMOUNT}")
    if not live.has_text(task.data, CURRENCY):
        missing.append(f"currency {CURRENCY}")
    if missing:
        live.fail(
            f"task {task.task_id} was created but does not show the finance manager "
            f"{', '.join(missing)}; title={bundle['title']!r} data={str(task.data)[:1500]}"
        )
    print(
        f"OK: Action Center task {task.task_id} ({task.task_type}, folder {task.folder_id}) "
        f"shows invoice {invoice}, {VENDOR}, {AMOUNT} {CURRENCY}"
    )


def main() -> None:
    project_dir = find_project_dir()
    flow = live.load_flow(project_dir)
    hitls = live.hitl_nodes(flow)
    if len(hitls) != 1:
        live.fail(f"expected one human-in-the-loop step, found {len(hitls)}")
    hitl = hitls[0]
    hitl_id = str(hitl.get("id"))
    actions, approve_ports, reject_ports = outcome_plan(hitl)

    invoice = f"INV-{uuid.uuid4().hex[:8].upper()}"
    inputs = {
        "invoiceNumber": invoice,
        "vendorName": VENDOR,
        "totalAmount": AMOUNT,
        "currency": CURRENCY,
    }
    deadline = time.monotonic() + DEADLINE_SECONDS
    run = live.start_debug(project_dir, inputs, CLI_TIMEOUT)
    try:
        ids = live.wait_for_ids(run, deadline)
        print(f"run: folder {ids.folder_id}, job {ids.job_key}, instance {ids.instance_id}")
        task, notes = live.find_run_task(
            ids, lambda _row, bundle: live.has_text(bundle, invoice), deadline, run
        )
        if task is None:
            out = run.stdout()[-1500:] if run.proc.poll() is not None else "(still running)"
            live.fail(
                "the run created no open Action Center task for invoice "
                f"{invoice}; {'; '.join(notes)}; debug stdout: {out}; "
                f"stderr tail: {run.stderr()[-1500:]}"
            )
        check_task_data(task, invoice)
        live.complete_task(task, actions, completion_data(hitl, task.data))
        payload = live.wait_for_result(run, deadline)
    except SystemExit:
        live.cancel(run)
        raise
    live.require_completed(payload)

    done = live.completed_ids(payload)
    if hitl_id not in done:
        _fail_with_capture(f"the approval step {hitl_id} did not complete in the run")
    edges = flow.get("edges") or []
    node_types = {str(n.get("id")): str(n.get("type", "")) for n in flow.get("nodes") or []}
    approve_reach = live.reachable(edges, set().union(*(live.port_targets(edges, hitl_id, p) for p in approve_ports)) if approve_ports else set())
    reject_reach = live.reachable(edges, set().union(*(live.port_targets(edges, hitl_id, p) for p in reject_ports)) if reject_ports else set())
    approve_only = {n for n in approve_reach - reject_reach if node_types.get(n) != "core.control.end"}
    reject_only = {n for n in reject_reach - approve_reach if node_types.get(n) != "core.control.end"}
    if approve_only:
        if not approve_only & done:
            _fail_with_capture(
                f"no step on the Approve path {sorted(approve_only)} completed after approval"
            )
        print(f"OK: the Approve path ran: {sorted(approve_only & done)}")
    else:
        print("note: both outcomes share their downstream steps; the outputs below decide the path")
    ran_rejected = sorted(reject_only & done)
    if ran_rejected:
        _fail_with_capture(f"steps reachable only from Reject ran after an approval: {ran_rejected}")

    assert_named_equals(payload, "status", "posted")
    assert_named_equals(payload, "sapDocumentNumber", f"SAP-{invoice}", case_sensitive=True)
    print(f"OK: status=posted, sapDocumentNumber=SAP-{invoice}")


if __name__ == "__main__":
    main()
