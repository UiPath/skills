#!/usr/bin/env python3
"""InvoiceApproval (skill-hitl-e2e-invoice-approval-greenfield): run the flow
for real, act as the finance manager, and check what the run did.

The flow is debugged twice, each with a fresh invoice number so the run's task
is told apart from any other open task in the folder. In both runs the run
created an Action Center task whose data shows that invoice number, the vendor,
the total amount and the currency. Then:

1. Approve run: the grader completes the task with the Approve outcome. The
   run then completed; the HITL step completed; a step reachable only from
   Approve completed when there is one, and no step reachable only from
   Reject ran. The named outputs: status = "posted", sapDocumentNumber =
   "SAP-<invoice>".
2. Reject run: the grader completes it with Reject. The run then completed;
   the HITL step completed; no step reachable only from Approve ran. The
   named outputs: status = "rejected", sapDocumentNumber empty.

Before either run, a step that builds the "SAP-" document number (the posting
stand-in; an End node mapping the output is not a step) that the trigger can
reach without passing through the HITL step draws a warning, not a failure:
the stand-in has no side effect, and the reject run's outputs show nothing is
posted. Any outcome layout is accepted: per-outcome ports, both into a
switch on the decision, or one step after the HITL that sets both outputs.
Nothing here pins node ids, labels or variable names. A run that did not complete is
cancelled.
"""

from __future__ import annotations

import os
import sys
import uuid
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hitl_live_run as live  # noqa: E402
from flow_check import (  # noqa: E402
    _get_ci,
    _fail_with_capture,
    _named_global,
    assert_named_equals,
    find_project_dir,
)

VENDOR = "Northwind Office Supplies"
AMOUNT = 4870.25
CURRENCY = "EUR"
SAP_MARKER = "SAP-"


class Decision(Enum):
    APPROVE = "approve"
    REJECT = "reject"


def outcome_plan(hitl: dict) -> tuple[list[str], list[str], set[str], set[str]]:
    """(approve action names to try, reject action names, Approve ports, Reject ports)."""
    outcomes = ((hitl.get("inputs") or {}).get("schema") or {}).get("outcomes") or []
    approve, reject, approve_ports, reject_ports = [], [], set(), set()
    for o in outcomes:
        name, oid = str(o.get("name") or ""), str(o.get("id") or "")
        label = f"{name} {oid}".lower()
        if "approv" in label:
            approve += [name, oid]
            approve_ports.add(f"outcome-{oid}")
        elif "reject" in label:
            reject += [name, oid]
            reject_ports.add(f"outcome-{oid}")
    return approve or ["Approve"], reject or ["Reject"], approve_ports, reject_ports


def completion_data(hitl: dict, existing: object, text_answer: str, decision: Decision) -> dict:
    """The task's form data plus an answer for each empty output field, keyed
    the way Action Center shows the fields (first letter upper-cased:
    `comment` -> `Comment`), the shape a completion that resumes the run uses.
    Boolean fields are true only on approval."""
    data = dict(existing) if isinstance(existing, dict) else {}
    for f in ((hitl.get("inputs") or {}).get("schema") or {}).get("fields") or []:
        fid = str(f.get("id") or "")
        if not fid or f.get("direction") not in ("output", "inOut"):
            continue
        key = next((k for k in data if k.lower() == fid.lower()), fid[:1].upper() + fid[1:])
        if data.get(key) not in (None, ""):
            continue
        kind = str(f.get("type") or "").lower()
        data[key] = 0 if kind in ("number", "integer", "float", "double") else (
            decision is Decision.APPROVE if kind == "boolean" else text_answer
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


def run_once(
    project_dir: str, hitl: dict, decision: Decision, actions: list[str], comment: str
) -> tuple[dict, str]:
    """Debug the flow, check the run's task, answer it with `actions`, and
    return the completed run's payload and invoice number."""
    invoice = f"INV-{uuid.uuid4().hex[:8].upper()}"
    inputs = {
        "invoiceNumber": invoice,
        "vendorName": VENDOR,
        "totalAmount": AMOUNT,
        "currency": CURRENCY,
    }
    payload = live.run_with_task(
        project_dir,
        inputs,
        invoice,
        hitl,
        actions,
        lambda task: check_task_data(task, invoice),
        lambda task: completion_data(hitl, task.data, comment, decision),
        "invoice",
    )
    return payload, invoice


def main() -> None:
    project_dir = find_project_dir()
    flow = live.load_flow(project_dir)
    hitls = live.hitl_nodes(flow)
    if len(hitls) != 1:
        live.fail(f"expected one human-in-the-loop step, found {len(hitls)}")
    hitl = hitls[0]
    hitl_id = str(hitl.get("id"))
    approve, reject, approve_ports, reject_ports = outcome_plan(hitl)
    edges = flow.get("edges") or []
    node_types = {str(n.get("id")): str(n.get("type", "")) for n in flow.get("nodes") or []}

    def only_from(ports: set[str], others: set[str]) -> set[str]:
        reach = lambda ps: live.reachable(edges, set().union(*(live.port_targets(edges, hitl_id, p) for p in ps)))
        return {n for n in reach(ports) - reach(others) if node_types.get(n) != "core.control.end"}

    approve_only = only_from(approve_ports, reject_ports)
    reject_only = only_from(reject_ports, approve_ports)
    early = sorted(live.posting_steps(flow, SAP_MARKER) & live.bypassing(flow, hitl_id))
    if early:
        print(f"WARN: the SAP step(s) {early} can run without the finance manager's approval: "
              f"the trigger reaches them without passing through {hitl_id}")

    payload, invoice = run_once(project_dir, hitl, Decision.APPROVE, approve, "Approved by the eval grader")
    done = live.completed_ids(payload)
    if hitl_id not in done:
        _fail_with_capture(f"the approval step {hitl_id} did not complete in the run")
    if approve_only:
        if not approve_only & done:
            _fail_with_capture(
                f"no step on the Approve path {sorted(approve_only)} completed after approval"
            )
        print(f"OK: the Approve path ran: {sorted(approve_only & done)}")
    ran_rejected = sorted(reject_only & done)
    if ran_rejected:
        _fail_with_capture(f"steps reachable only from Reject ran after an approval: {ran_rejected}")
    assert_named_equals(payload, "status", "posted")
    assert_named_equals(payload, "sapDocumentNumber", f"SAP-{invoice}", case_sensitive=True)
    print(f"OK: status=posted, sapDocumentNumber=SAP-{invoice}")

    payload, _invoice = run_once(project_dir, hitl, Decision.REJECT, reject, "Rejected by the eval grader")
    done = live.completed_ids(payload)
    if hitl_id not in done:
        _fail_with_capture(f"the approval step {hitl_id} did not complete in the reject run")
    ran_approved = sorted(approve_only & done)
    if ran_approved:
        _fail_with_capture(f"steps reachable only from Approve ran after a rejection: {ran_approved}")
    assert_named_equals(payload, "status", "rejected")
    sap, _globals = _named_global(payload, "sapDocumentNumber")
    if str(sap if sap is not None else "").strip():
        _fail_with_capture(f"output 'sapDocumentNumber' must be empty after a rejection, got {sap!r}")
    print("OK: after a rejection nothing was posted, status=rejected and sapDocumentNumber is empty")


if __name__ == "__main__":
    main()
