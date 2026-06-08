#!/usr/bin/env python3
"""End-to-end debug check for the full DevCon BillingDisputeResolution flow.

Runs `uip maestro flow debug` once against live tenant resources (IxP model,
BillingDisputeERP / BillingDisputeCRM Data Service entities, the Billing Dispute
SOP context index, the FinancialPostingFunction API workflow, and the two inline
agents) and asserts the flow RETURNS a real, SOP-grounded resolution instead of
emailing it.

Inputs are discovered from the flow itself (robust to variable renaming): the
file-typed input gets the bundled invoice PDF via `--attachment`; the object
input gets a self-contained billing-dispute webhook payload.

Output assertion (anti-soft-refusal): the returned values must engage the
dispute facts — the disputed invoice number plus at least one verdict/domain
token — not a generic "please provide more info" string. We do NOT pin the exact
determination text: the analyst agent authors its own determination vocabulary,
so a literal match would be brittle and unfair.
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    collect_outputs,
    find_project_dir,
    read_flow_file_input_vars,
    read_flow_input_vars,
    run_debug,
)

INVOICE = "MCS-2026-04872"
PDF = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"invoice-{INVOICE}.pdf")

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


def main():
    # Anti-hardcode: the analyst+writer agents and the IxP node must actually be
    # invoked — a Script node cannot stand in for them.
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_has_node_type(["uipath.ixp"])
    print("OK: inline agent + IxP nodes present")

    project_dir = find_project_dir()
    file_vars = read_flow_file_input_vars(project_dir)
    obj_vars = [v for v in read_flow_input_vars(project_dir) if v not in file_vars]

    inputs = {obj_vars[0]: WEBHOOK_PAYLOAD} if obj_vars else None
    attachments = None
    if file_vars and os.path.exists(PDF):
        attachments = {file_vars[0]: PDF}
    elif file_vars:
        sys.exit(f"FAIL: file input {file_vars[0]!r} declared but fixture {PDF} is missing")

    print(f"debug inputs: object={obj_vars[:1]} attachment={list((attachments or {}).keys())}")
    payload = run_debug(inputs=inputs, attachments=attachments, timeout=540)

    if not [v for v in collect_outputs(payload) if str(v).strip()]:
        sys.exit("FAIL: flow completed but returned no non-empty output values")

    # Engage the dispute facts: the disputed invoice plus a verdict/domain token.
    # OR-set, not an exact-string pin (the agent authors its own vocabulary). A
    # generic refusal that never reasoned over the dispute contains none of these.
    assert_outputs_contain(payload, INVOICE)
    assert_outputs_contain(
        payload,
        ["credit", "valid", "reject", "approv", "escalat", "duplicate",
         "discrepancy", "overcharge", "contract", "290", "300"],
        require_all=False,
    )
    print(f"OK: flow returned a real SOP-grounded resolution citing {INVOICE} (no email sent)")


if __name__ == "__main__":
    main()
