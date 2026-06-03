#!/usr/bin/env python3
"""BillingInvoiceLookup: the agent builds + validates only; this check runs
`uip maestro flow debug` itself for three malformed invoice-number forms and
asserts each resolves, via a real Data Service query, to invoice MCS-2026-04872
with 8 line items.

The flow normalizes a raw `invoiceNumber` (trim, uppercase, ensure the "MCS-"
prefix) and queries the seeded `BillingDisputeERP` entity. A Data Service query
node is required (anti-hardcode): you cannot fake `lineItemCount == 8` for three
different inputs without actually querying. The seeded invoice has exactly 8
line items, so the count is a deterministic oracle.
"""
import os
import sys

# Walk up to the skill's tests root (the dir holding the _shared package) so
# this resolves regardless of how deeply the task is nested under tests/tasks/.
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_output_value,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)

EXPECTED_INVOICE = "MCS-2026-04872"
EXPECTED_LINE_COUNT = 8

# raw input form the caller might send -> human label for failure messages
CASES = [
    ("2026-04872", "missing MCS- prefix"),
    ("mcs-2026-04872", "wrong casing"),
    (" MCS-2026-04872", "leading whitespace"),
]


def main():
    # Must actually query Data Service — blocks hardcoding the answer, which
    # would otherwise pass since all three cases expect the same output.
    assert_flow_has_node_type(["uipath-dataservice.query"])

    in_vars = read_flow_input_vars(find_project_dir())
    if not in_vars:
        sys.exit("FAIL: flow declares no input variable for the invoice number")
    var = in_vars[0]

    for raw, label in CASES:
        inputs = {var: raw}
        print(f"[{label}] debug inputs: {inputs}")
        payload = run_debug(inputs=inputs, timeout=180)
        assert_output_value(payload, EXPECTED_INVOICE)
        assert_output_value(payload, EXPECTED_LINE_COUNT)
        print(f"OK: [{label}] -> {EXPECTED_INVOICE}, {EXPECTED_LINE_COUNT} line items")

    print(f"OK: all {len(CASES)} malformed forms normalized and queried correctly")


if __name__ == "__main__":
    main()
