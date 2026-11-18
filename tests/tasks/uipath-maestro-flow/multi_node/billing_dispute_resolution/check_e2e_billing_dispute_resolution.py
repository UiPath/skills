#!/usr/bin/env python3
"""Effects check for BillingDisputeResolution.

Debugs the flow once against the live tenant and asserts what the run DID,
read from the debug trace, for one of two disputes on invoice MCS-2026-04872:

  overcharge       Line 5 (Custom Integration Build) billed 14 x 300 = 4200
                   against a contracted 14 x 185 = 2590. The dispute is valid,
                   so the run must: extract the invoice (IxP), complete both
                   lookups, run the analyst, POST through
                   FinancialPostingFunction (whose live reply must cite the
                   invoice), run the writer, and return an email
                   draft that cites the invoice number and the credit amount
                   the flow returns.

  no-discrepancy   Line 4 (Solutions Architect Consulting) billed 4 x 325 = 1300,
                   exactly the contract. There is nothing to credit, so the run
                   must complete WITHOUT posting and without running the writer
                   (no email drafted), and still return an explanation.

The email is never sent: the structural check forbids a send-email node.

Each run leaves its time window in `.grading/posting_window_<case>.json` for
the advisory Orchestrator job probe (`probe_posting_jobs.py`).

Usage: check_e2e_billing_dispute_resolution.py overcharge|no-discrepancy
"""
import copy
import glob
import json
import os
import sys
from datetime import datetime, timezone

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    _declared_input_global_keys,
    _fail_with_capture,
    _get_ci,
    _named_global,
    find_project_dir,
    node_output_leaves,
    read_flow_file_input_vars,
    read_flow_input_vars,
    run_debug,
)

INVOICE = "MCS-2026-04872"

# Self-contained billing-dispute submission event (matches the flow's
# webhookPayload input schema). Disputed amount is above the credit-approval
# threshold so the analyst has a substantive, escalation-worthy dispute to reason
# about. Line items are present so the discrepancy script has data even on the
# headless lane where IxP extraction does not run.
WEBHOOK_PAYLOAD = {
    "event": "billing_dispute_submitted",
    "timestamp": "2026-04-02T15:04:05Z",
    "disputeId": "DSP-2026-00341",
    "customer": {
        "companyName": "Northwind Electronics Corp.",
        "accountNumber": "ACCT-98201-NE",
        "contactName": "Lisa Huang",
        "contactEmail": "lisa.huang@northwindelectronics.com",
        "address": {"street": "100 Market St", "city": "Seattle", "state": "WA", "zipCode": "98101"},
    },
    "invoice": {
        "invoiceNumber": INVOICE,
        "invoiceDate": "2026-03-01",
        "dueDate": "2026-03-31",
        "billingPeriod": {"start": "2026-02-01", "end": "2026-02-28"},
        "totalAmount": 24175.80,
        "currency": "USD",
        "vendor": {"name": "Contoso Cloud Services", "address": "1 Cloud Way, Redmond WA",
                   "email": "billing@contoso.example"},
    },
    "dispute": {
        "type": "duplicate_charge",
        "disputedLineItems": [
            {"description": "Premium support tier", "quantity": "14", "unitPrice": 300,
             "amount": 4200, "lineNumber": 3, "reason": "Billed at $300/unit vs contracted $290/unit"},
        ],
        "disputedAmount": 11000,
        "acceptedAmount": 13175.80,
        "customerStatement": "We were charged a higher unit price than our contract specifies.",
    },
    "attachments": [],
    "config": {
        "billingOpsChannel": "#billing-ops",
        "billingAnalystEmail": "analyst@contoso.example",
        "accountManagerSlackId": "U12345",
        "accountManagerName": "Sam Rivera",
        "accountManagerEmail": "sam.rivera@contoso.example",
        "creditApprovalThreshold": 5000,
        "autoResolveThreshold": 500,
    },
}

PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"invoice-{INVOICE}.pdf")
WINDOW_FILE = ".grading/posting_window_{case}.json"

DISPUTES = {
    "overcharge": {
        "type": "pricing",
        "disputedLineItems": [
            {"lineNumber": 5, "description": "Custom Integration Build",
             "quantity": 14, "unitPrice": 300, "amount": 4200,
             "reason": "Billed at $300/hour vs the contracted $185/hour"},
        ],
        "disputedAmount": 4200,
        "customerStatement": "We were charged a higher hourly rate than our contract specifies.",
    },
    "no-discrepancy": {
        "type": "pricing",
        "disputedLineItems": [
            {"lineNumber": 4, "description": "Solutions Architect Consulting",
             "quantity": 4, "unitPrice": 325, "amount": 1300,
             "reason": "We believe this rate is too high"},
        ],
        "disputedAmount": 1300,
        "customerStatement": "The consulting rate looks higher than we expected.",
    },
}


def _flow():
    flows = sorted(glob.glob(os.path.join(find_project_dir(), "**/*.flow"), recursive=True))
    if not flows:
        sys.exit("FAIL: no .flow file in the project")
    with open(flows[0]) as f:
        return json.load(f)


def _ids_of(flow, sub):
    return {n["id"] for n in flow.get("nodes") or [] if sub in str(n.get("type", ""))}


def _downstream(flow, starts):
    adj = {}
    for e in flow.get("edges") or []:
        adj.setdefault(e.get("sourceNodeId"), []).append(e.get("targetNodeId"))
    seen, stack = set(), list(starts)
    while stack:
        for y in adj.get(stack.pop(), ()):
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return seen


def _executed_ids(payload, *, completed=False):
    els = _get_ci(payload, "elementExecutions", "Elements", "elements") or []
    return {
        _get_ci(e, "elementId", "ElementId", "nodeId", "NodeId")
        for e in els
        if not completed or str(_get_ci(e, "status", "Status")).lower() == "completed"
    }


def _completed(flow, payload, sub):
    return _ids_of(flow, sub) & _executed_ids(payload, completed=True)


def _outputs(flow, payload):
    """The declared `out` variables and their runtime values, inputs excluded."""
    inputs = {k.lower() for k in _declared_input_global_keys(payload)}
    outs = {}
    for v in (flow.get("variables") or {}).get("globals") or []:
        if v.get("direction") == "out" and v["id"].lower() not in inputs:
            outs[v["id"]] = (v.get("type"), _named_global(payload, v["id"])[0])
    return outs


def _amount_spellings(amount):
    spellings = {f"{amount:.2f}", f"{amount:,.2f}"}
    if float(amount).is_integer():
        spellings |= {str(int(amount)), f"{int(amount):,}"}
    return spellings


def _debug(flow_dispute):
    project_dir = find_project_dir()
    file_vars = read_flow_file_input_vars(project_dir)
    obj_vars = [v for v in read_flow_input_vars(project_dir) if v not in file_vars]
    if not obj_vars:
        sys.exit("FAIL: the flow declares no object input for the dispute submission")
    if not file_vars:
        sys.exit("FAIL: the flow declares no file input for the invoice PDF")
    payload_in = copy.deepcopy(WEBHOOK_PAYLOAD)
    payload_in["dispute"] = flow_dispute
    print(f"debug inputs: object={obj_vars[0]} attachment={file_vars[0]}")
    started = _now()
    payload = run_debug(inputs={obj_vars[0]: payload_in}, attachments={file_vars[0]: PDF}, timeout=840)
    return payload, {"startedAt": started, "endedAt": _now(), "jobKey": _get_ci(payload, "jobKey", "JobKey")}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stamp_window(case, window):
    """Leave the debug run's time window for the advisory job probe."""
    os.makedirs(".grading", exist_ok=True)
    with open(WINDOW_FILE.format(case=case), "w") as f:
        json.dump({"case": case, "invoice": INVOICE, **window}, f)


def check_overcharge(flow, payload):
    if not _completed(flow, payload, "uipath.ixp"):
        _fail_with_capture("the IxP extraction did not complete")
    reads = set()
    for hint in ENTITY_QUERY_HINTS:
        reads |= _completed(flow, payload, hint)
    if len(reads) < 2:
        _fail_with_capture(f"expected the ERP and CRM lookups to complete, completed reads: {sorted(reads)}")
    print("OK: IxP extraction and both lookups completed")

    posted = _completed(flow, payload, "uipath.core.api-workflow")
    if not posted:
        _fail_with_capture("FinancialPostingFunction did not complete: a valid overcharge was not posted")
    print(f"OK: FinancialPostingFunction completed ({sorted(posted)})")

    # The deployed function echoes the invoice it was sent ("Credit memo posted
    # successfully. Invoice: '<n>'. …"), so its live reply proves which invoice
    # the flow posted. Matched on the value, not a field name: the tenant copy
    # and the repo source name the field differently.
    replies = node_output_leaves(payload, posted)
    if not any(INVOICE in r for r in replies):
        _fail_with_capture(
            f"FinancialPostingFunction's reply does not cite {INVOICE}: {sorted(replies)[:5]}"
        )
    print(f"OK: FinancialPostingFunction replied for {INVOICE}: {sorted(replies)[:1]}")

    writers = _ids_of(flow, "uipath.agent.autonomous") & _downstream(flow, posted)
    if not writers & _executed_ids(payload, completed=True):
        _fail_with_capture("the writer agent after posting did not complete: no email was drafted")
    print(f"OK: writer agent completed ({sorted(writers)})")

    outs = _outputs(flow, payload)
    credits = [val for typ, val in outs.values()
               if isinstance(val, (int, float)) and not isinstance(val, bool) and val > 0]
    if not credits:
        _fail_with_capture(f"no positive credit amount among the returned outputs: {outs}")
    texts = [val for typ, val in outs.values() if isinstance(val, str)]
    drafts = [
        t for t in texts
        if INVOICE in t and any(s in t for c in credits for s in _amount_spellings(c))
    ]
    if not drafts:
        _fail_with_capture(
            f"no returned text cites both {INVOICE} and the credit amount {credits}: {outs}"
        )
    print(f"OK: returned email draft cites {INVOICE} and the credit amount {credits}")


def check_no_discrepancy(flow, payload):
    api = _ids_of(flow, "uipath.core.api-workflow")
    executed = _executed_ids(payload)
    if api & executed:
        _fail_with_capture(
            f"FinancialPostingFunction ran ({sorted(api & executed)}) for a line billed exactly at contract"
        )
    print("OK: nothing was posted")

    writers = _ids_of(flow, "uipath.agent.autonomous") & _downstream(flow, api)
    if writers & executed:
        _fail_with_capture(f"the writer agent ran ({sorted(writers & executed)}): an email was drafted")
    print("OK: no email was drafted")

    outs = _outputs(flow, payload)
    if not any(isinstance(val, str) and val.strip() for _t, val in outs.values()):
        _fail_with_capture(f"the flow returned no explanation: {outs}")
    print("OK: the flow returned an explanation")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in DISPUTES:
        sys.exit(f"usage: {os.path.basename(__file__)} {'|'.join(DISPUTES)}")
    case = sys.argv[1]
    flow = _flow()
    payload, window = _debug(DISPUTES[case])
    _stamp_window(case, window)
    (check_overcharge if case == "overcharge" else check_no_discrepancy)(flow, payload)


if __name__ == "__main__":
    main()
