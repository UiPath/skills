#!/usr/bin/env python3
"""BillingDisputeAnalyst: debug the flow against the live tenant and assert
what the SOP-grounded agent decided, read by the output names the prompt gives.

The live "Billing Dispute SOP Index" is a numbered SOP: §5.4 "Incorrect rate"
compares the billed unit price with the contracted rate, and §7 routes a credit
under $500 to auto-resolve and $500 to $5,000 to manager review. The prompt
states none of those rules, so the routing below follows only from the SOP.
Both cases are real ERP rows (the same ones billing_dispute_resolution uses):

  overcharge   Invoice MCS-2026-04903 line 2 (DevOps Engineering): 90 h billed
               at $290 against a contracted $235. Credit (290 - 235) x 90 =
               $4,950, inside §7's $500-$5,000 band, so manager review.

  reject       Invoice MCS-2026-04872 line 5 (Custom Integration Build): 14 h
               billed at $185 and contracted at $185. No rate error, no credit,
               so reject.

Each run must complete the inline agent node and return `recommendedAction` in
the right category and `creditAmount` (4950, or no positive credit). The
dispute text carries both rates, so the credit alone does not prove retrieval;
the category for $4,950 does, since only the SOP says where $4,950 lands.

Usage: check_billing_dispute_analyst.py overcharge|reject
"""
import os
import re
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    _fail_with_capture,
    _named_global,
    assert_flow_has_node_type,
    assert_output_nonempty,
    completed_node_ids_of_type,
    run_debug,
)

AGENT_TYPE = "uipath.agent.autonomous"

CASES = {
    "overcharge": {
        "inputs": {
            "invoiceNumber": "MCS-2026-04903",
            "disputeDescription": (
                "Atlas Manufacturing Group (account ACCT-71044-AT) disputes line 2 of "
                "invoice MCS-2026-04903, DevOps Engineering: 90 hours billed at $290 per "
                "hour. Our SOW AT-2026-008 contracts this work at $235 per hour."
            ),
        },
        "action": "review",
        "credit": 4950,
    },
    "reject": {
        "inputs": {
            "invoiceNumber": "MCS-2026-04872",
            "disputeDescription": (
                "Northwind Electronics Corp. (account ACCT-98201-NE) disputes line 5 of "
                "invoice MCS-2026-04872, Custom Integration Build: 14 hours billed at $185 "
                "per hour. Our contract rate for this work is $185 per hour, but we feel "
                "the hourly rate is too high."
            ),
        },
        "action": "reject",
        "credit": 0,
    },
}

# A recommendedAction value -> category. The prompt asks for auto_resolve,
# manager_review or reject; close spellings of the same choice also count.
CATEGORY_WORDS = {
    "auto": ("auto",),
    "review": ("manager", "review", "escalat"),
    "reject": ("reject", "deny", "denied"),
}


def action_category(value):
    text = re.sub(r"[^a-z]+", "_", str(value or "").lower())
    hits = {c for c, words in CATEGORY_WORDS.items() if any(w in text for w in words)}
    return hits.pop() if len(hits) == 1 else None


def as_number(value):
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("$", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def check(case, payload):
    expected = CASES[case]
    if not completed_node_ids_of_type(payload, AGENT_TYPE):
        _fail_with_capture("the inline agent node did not complete in the debug run")
    print("OK: the inline agent completed")

    action = assert_output_nonempty(payload, "recommendedAction")
    if action_category(action) != expected["action"]:
        _fail_with_capture(
            f"recommendedAction={action!r}; the SOP routes this dispute to {expected['action']}"
        )
    print(f"OK: recommendedAction={action!r} ({expected['action']})")

    raw_credit, _ = _named_global(payload, "creditAmount")
    credit = as_number(raw_credit)
    if expected["credit"]:
        if credit is None or abs(credit - expected["credit"]) >= 0.005:
            _fail_with_capture(f"creditAmount={raw_credit!r}; expected {expected['credit']}")
    elif credit is not None and credit > 0.005:
        _fail_with_capture(f"creditAmount={raw_credit!r} for a line billed at the contracted rate")
    print(f"OK: creditAmount={raw_credit!r}")

    assert_output_nonempty(payload, "rationale")
    print("OK: the agent returned a rationale")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit(f"usage: {os.path.basename(__file__)} {'|'.join(CASES)}")
    case = sys.argv[1]
    assert_flow_has_node_type([AGENT_TYPE])
    assert_flow_has_node_type(["uipath.agent.resource.context.index"])
    print("OK: the flow has an inline agent and a context-index resource")
    inputs = CASES[case]["inputs"]
    print(f"debug inputs: {inputs}")
    check(case, run_debug(inputs=inputs, timeout=540))


if __name__ == "__main__":
    main()
