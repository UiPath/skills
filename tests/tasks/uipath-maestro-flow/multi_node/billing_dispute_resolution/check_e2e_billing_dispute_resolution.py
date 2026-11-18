#!/usr/bin/env python3
"""Effects check for BillingDisputeResolution.

Debugs the flow once against the live tenant and asserts what the run DID, read
from the debug trace. Both cases use rows the tenant's BillingDisputeERP really
holds, and the invoice PDF that matches them, so the right outcome follows from
the tenant's own Billing Dispute SOP (its "Incorrect rate" rule compares the
billed unitPrice with the row's contractedRate):

  overcharge       Invoice MCS-2026-04903, line 2 (DevOps Engineering): 90 hours
                   billed at $290 against a contracted $235, so the customer is
                   owed (290 - 235) x 90 = $4,950. The run must: extract the
                   invoice (IxP), complete both lookups, POST through
                   FinancialPostingFunction (whose live reply must cite the
                   invoice), run the writer, and return a credit of 4950 and an
                   email draft that cites the invoice number and that credit.

  no-discrepancy   Invoice MCS-2026-04872, line 4 (Solutions Architect
                   Consulting): 4 hours billed at $325, exactly the contract.
                   There is nothing to credit, so the run must complete WITHOUT
                   posting and without running the writer (no email drafted),
                   and still return an explanation.

The email is never sent: the structural check forbids a send-email node.

Usage: check_e2e_billing_dispute_resolution.py overcharge|no-discrepancy
"""
import copy
import glob
import json
import os
import sys

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

_HERE = os.path.dirname(os.path.abspath(__file__))

# A billing-dispute submission event (the shape the prompt's helper block
# describes). Each case replaces customer, invoice and dispute.
WEBHOOK_PAYLOAD = {
    "event": "billing_dispute_submitted",
    "timestamp": "2026-04-02T15:04:05Z",
    "disputeId": "DSP-2026-00341",
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

CASES = {
    "overcharge": {
        "invoice": "MCS-2026-04903",
        "credit": 4950,
        "customer": {"companyName": "Atlas Manufacturing Group", "accountNumber": "ACCT-71044-AT"},
        "invoiceDetails": {"invoiceDate": "2026-03-31", "dueDate": "2026-04-30",
                           "totalAmount": 27796.00, "currency": "USD"},
        "dispute": {
            "type": "pricing",
            "disputedLineItems": [
                {"lineNumber": 2, "description": "DevOps Engineering",
                 "quantity": 90, "unitPrice": 290, "amount": 26100,
                 "reason": "Billed at $290/hour; our SOW AT-2026-008 contracts $235/hour"},
            ],
            "disputedAmount": 26100,
            "customerStatement": "We were billed a higher hourly rate than our contract specifies.",
        },
    },
    "no-discrepancy": {
        "invoice": "MCS-2026-04872",
        "credit": None,
        "customer": {"companyName": "Northwind Electronics Corp.", "accountNumber": "ACCT-98201-NE"},
        "invoiceDetails": {"invoiceDate": "2026-03-01", "dueDate": "2026-03-31",
                           "totalAmount": 30425.00, "currency": "USD"},
        "dispute": {
            "type": "pricing",
            "disputedLineItems": [
                {"lineNumber": 4, "description": "Solutions Architect Consulting",
                 "quantity": 4, "unitPrice": 325, "amount": 1300,
                 "reason": "We believe this rate is too high"},
            ],
            "disputedAmount": 1300,
            "customerStatement": "The consulting rate looks higher than we expected.",
        },
    },
}


def submission(case):
    """The dispute submission for a case, in the helper block's shape."""
    c = CASES[case]
    payload = copy.deepcopy(WEBHOOK_PAYLOAD)
    payload["customer"] = copy.deepcopy(c["customer"])
    payload["invoice"] = {"invoiceNumber": c["invoice"], **c["invoiceDetails"]}
    payload["dispute"] = copy.deepcopy(c["dispute"])
    return payload


def invoice_pdf(case):
    return os.path.join(_HERE, f"invoice-{CASES[case]['invoice']}.pdf")


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


def _as_number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except ValueError:
        return None


def _amount_spellings(amount):
    spellings = {f"{amount:.2f}", f"{amount:,.2f}"}
    if float(amount).is_integer():
        spellings |= {str(int(amount)), f"{int(amount):,}"}
    return spellings


def _debug(case):
    project_dir = find_project_dir()
    file_vars = read_flow_file_input_vars(project_dir)
    obj_vars = [v for v in read_flow_input_vars(project_dir) if v not in file_vars]
    if not obj_vars:
        sys.exit("FAIL: the flow declares no object input for the dispute submission")
    if not file_vars:
        sys.exit("FAIL: the flow declares no file input for the invoice PDF")
    print(f"debug inputs: object={obj_vars[0]} attachment={file_vars[0]} invoice={CASES[case]['invoice']}")
    return run_debug(
        inputs={obj_vars[0]: submission(case)},
        attachments={file_vars[0]: invoice_pdf(case)},
        timeout=840,
    )


def check_overcharge(flow, payload):
    invoice, credit = CASES["overcharge"]["invoice"], CASES["overcharge"]["credit"]
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
    if not any(invoice in r for r in replies):
        _fail_with_capture(
            f"FinancialPostingFunction's reply does not cite {invoice}: {sorted(replies)[:5]}"
        )
    print(f"OK: FinancialPostingFunction replied for {invoice}: {sorted(replies)[:1]}")

    writers = _ids_of(flow, "uipath.agent.autonomous") & _downstream(flow, posted)
    if not writers & _executed_ids(payload, completed=True):
        _fail_with_capture("the writer agent after posting did not complete: no email was drafted")
    print(f"OK: writer agent completed ({sorted(writers)})")

    outs = _outputs(flow, payload)
    numbers = [n for _t, val in outs.values() if (n := _as_number(val)) is not None]
    if not any(abs(n - credit) < 0.005 for n in numbers):
        _fail_with_capture(f"no returned output is the credit of {credit} (90 h x $55): {outs}")
    texts = [val for _t, val in outs.values() if isinstance(val, str)]
    if not any(invoice in t and any(s in t for s in _amount_spellings(credit)) for t in texts):
        _fail_with_capture(f"no returned text cites both {invoice} and the credit of {credit}: {outs}")
    print(f"OK: the flow returned a credit of {credit} and a draft citing {invoice} and that credit")


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
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit(f"usage: {os.path.basename(__file__)} {'|'.join(CASES)}")
    case = sys.argv[1]
    flow = _flow()
    payload = _debug(case)
    (check_overcharge if case == "overcharge" else check_no_discrepancy)(flow, payload)


if __name__ == "__main__":
    main()
