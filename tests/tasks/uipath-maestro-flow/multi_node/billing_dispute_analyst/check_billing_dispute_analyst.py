#!/usr/bin/env python3
"""BillingDisputeAnalyst: debug the flow against the live tenant and grade
what the SOP-grounded agent decided.

The prompt names no variables, so the seeded values are mapped onto the flow's
declared inputs by meaning (`flow_io_roles.map_inputs`) and the decision and
reasoning are found among its declared outputs by value.

The live "Billing Dispute SOP Index" is a numbered SOP: §5.4 "Incorrect rate"
compares the billed unit price with the contracted rate, and §7 routes a credit
under $500 to auto-resolve, $500 to $5,000 to manager review, and anything
without a variance to reject. The prompt states none of those rules.

  overcharge   Invoice MCS-2026-04903 line 2 (DevOps Engineering): 90 h billed
               at $290 against a contracted $235. Credit (290 - 235) x 90 =
               $4,950, inside §7's $500-$5,000 band, so "manager_review". The
               description carries both rates; only the SOP says where $4,950
               lands, so the decision proves the agent read it.
  reject       Invoice MCS-2026-04872 line 5 (Custom Integration Build): 14 h
               billed at $185 and contracted at $185. No variance, so "reject".
  thin         A description with no figures at all. The prompt says a
               description too thin to check goes to "manager_review".

Each run must complete the agent node, return the decision exactly as the
prompt spells it, and return reasoning that names an SOP rule.

Usage: check_billing_dispute_analyst.py overcharge|reject|thin
"""
import json
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared import flow_io_roles as io  # noqa: E402
from _shared.billing_sop import NAMES_A_RULE  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    _fail,
    _fail_with_capture,
    _load_flow,
    completed_node_ids_of_type,
    run_debug,
)

# An inline agent, or an existing tenant agent (`uipath.core.agent.<key>`).
AGENT_TYPES = ("uipath.agent.autonomous", "uipath.core.agent.")
DECISIONS = ("credit", "reject", "manager_review")

CASES = {
    "overcharge": {
        "invoice": "MCS-2026-04903",
        "description": (
            "Atlas Manufacturing Group (account ACCT-71044-AT) disputes line 2 of "
            "invoice MCS-2026-04903, DevOps Engineering: 90 hours billed at $290 per "
            "hour. Our SOW AT-2026-008 contracts this work at $235 per hour."
        ),
        "decision": "manager_review",
        # check_analyst_band.py grades the band.
        "accept": ("manager_review", "credit"),
    },
    "reject": {
        "invoice": "MCS-2026-04872",
        "description": (
            "Northwind Electronics Corp. (account ACCT-98201-NE) disputes line 5 of "
            "invoice MCS-2026-04872, Custom Integration Build: 14 hours billed at $185 "
            "per hour. Our contract rate for this work is $185 per hour, but we feel "
            "the hourly rate is too high."
        ),
        "decision": "reject",
    },
    "thin": {
        "invoice": "MCS-2026-04872",
        "description": "Something on this invoice looks wrong to us. Please check it.",
        "decision": "manager_review",
    },
}


def roles(case):
    c = CASES[case]
    return {
        "invoice number": {"value": c["invoice"], "keywords": [
            "invoicenumber", "invoiceno", "invoiceid", "invoiceref", "invoice"]},
        "dispute description": {"value": c["description"], "keywords": [
            "description", "complaint", "problem", "issue", "statement", "details", "dispute",
            "message", "reason", "claim", "text"]},
    }


DECISION_FILE = ".grading/analyst_overcharge_decision.json"


def check(case, flow, payload):
    expected = CASES[case]["decision"]
    accepted = CASES[case].get("accept", (expected,))
    agents = set()
    for hint in AGENT_TYPES:
        agents |= completed_node_ids_of_type(payload, hint)
    if not agents:
        _fail_with_capture("no agent node completed in the debug run")
    print(f"OK: the agent completed ({sorted(agents)})")

    outs = io.out_values(flow, payload)
    print(f"outputs: { {k: v for k, (_t, v) in outs.items()} }")
    # Text nested in an object output counts too: {decision, reasoning} is one result pair.
    found = [(k, t) for k, (_t, v) in outs.items() for t in io.texts(v)]
    matched = sorted({t.strip() for _k, t in found if any(io.equals_exact(a)(t) for a in accepted)})
    if not matched:
        returned = [t for _k, t in found if t.strip().lower() in DECISIONS]
        _fail_with_capture(
            f"no declared output is the decision {' or '.join(map(repr, accepted))} (the SOP's answer "
            f"for this dispute); decisions returned: {returned}; outputs: {outs}"
        )
    print(f"OK: the decision is {matched}")
    if case == "overcharge":
        os.makedirs(os.path.dirname(DECISION_FILE), exist_ok=True)
        with open(DECISION_FILE, "w") as f:
            json.dump({"decisions": matched}, f)

    reasons = [t for _k, t in found if not any(io.equals_exact(a)(t) for a in accepted) and len(t.split()) >= 5]
    if not any(NAMES_A_RULE.search(t) for t in reasons):
        _fail_with_capture(f"no returned reasoning names an SOP rule (by § or section number, or its title): {reasons}")
    print("OK: the reasoning names an SOP rule")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit(f"usage: {os.path.basename(__file__)} {'|'.join(CASES)}")
    case = sys.argv[1]
    flow = _load_flow("**/project.uiproj")
    if not any(h in str(n.get("type", "")) for n in flow.get("nodes") or [] for h in AGENT_TYPES):
        _fail("the flow has no agent node (inline or existing tenant agent)")
    inputs, _attachments, unmapped = io.map_inputs(flow, roles(case), object_fallback=None, file_path=None)
    if problem := io.unmapped_error(flow, unmapped, inputs):
        _fail(problem)
    print(f"debug inputs: {inputs}")
    check(case, flow, run_debug(inputs=inputs, timeout=540))


if __name__ == "__main__":
    main()
