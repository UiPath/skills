#!/usr/bin/env python3
"""BillingInvoiceLookup: the agent builds + validates only; this check runs
`uip maestro flow debug` itself for three malformed invoice-number forms and
asserts each resolves, via a real Data Service query, to invoice MCS-2026-04872
with 8 line items. A fourth case supplies a normalized-but-absent invoice and
asserts the flow returns 0 line items — verifying it handles an empty result
set, not just the happy path.

The flow normalizes a raw `invoiceNumber` (trim, uppercase, ensure the "MCS-"
prefix) and queries the seeded `BillingDisputeERP` entity. A Data Service query
node is required (anti-hardcode): you cannot fake `lineItemCount == 8` for three
different inputs without actually querying. The seeded invoice has exactly 8
line items, so the count is a deterministic oracle; an absent invoice yields 0.
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

# A normalized-but-absent invoice: the query matches no rows. The flow must
# return 0 line items (empty result handled) rather than erroring on "first row
# of an empty set". MCS-9999-00000 is not seeded in BillingDisputeERP.
NOT_FOUND = (" mcs-9999-00000 ", "absent invoice (empty result set)")
EXPECTED_NOT_FOUND_COUNT = 0


def main():
    # Must actually query Data Service — blocks hardcoding the answer, which
    # would otherwise pass since all three happy cases expect the same output.
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

    # Empty-result case: normalized to a valid MCS- form that matches nothing.
    raw, label = NOT_FOUND
    inputs = {var: raw}
    print(f"[{label}] debug inputs: {inputs}")
    payload = run_debug(inputs=inputs, timeout=180)
    assert_output_value(payload, EXPECTED_NOT_FOUND_COUNT)
    print(f"OK: [{label}] -> {EXPECTED_NOT_FOUND_COUNT} line items (empty result handled)")

    print(
        f"OK: all {len(CASES)} malformed forms normalized and queried correctly, "
        "and the absent-invoice case returned 0 line items"
    )


if __name__ == "__main__":
    main()
