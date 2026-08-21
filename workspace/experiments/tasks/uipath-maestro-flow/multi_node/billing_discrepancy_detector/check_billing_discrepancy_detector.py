#!/usr/bin/env python3
"""BillingDiscrepancyDetector: the agent builds + validates only; this check
runs `uip maestro flow debug` itself once against seeded data and asserts the
computed overcharge, discrepancy count, matched invoice, and account tier.

Inputs map to ERP line 5 (Custom Integration Build): contracted amount 2590,
disputed at 300*14 = 4200 -> overcharge 1610. CRM account ACCT-98201-NE is the
Enterprise tier. A Data Service query node is required (anti-hardcode): 1610 and
"Enterprise" cannot be produced without querying ERP and CRM for real.
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
    run_debug,
)

INPUTS = {
    "invoiceNumber": "MCS-2026-04872",
    "accountNumber": "ACCT-98201-NE",
    "disputedLineNumber": 5,
    "disputedUnitPrice": 300,
    "disputedQuantity": 14,
}


def main():
    # Must query Data Service (ERP + CRM) — blocks hardcoding 1610 / Enterprise.
    # The two lookups are independent, so the flow must fan them out as parallel
    # branches joined by a merge (not chained serially) — require the merge node.
    assert_flow_has_node_type(["uipath-dataservice.query", "core.logic.merge"])

    print(f"debug inputs: {INPUTS}")
    payload = run_debug(inputs=INPUTS, timeout=240)

    assert_output_value(payload, 1610)              # overcharge: 4200 - 2590
    assert_output_value(payload, 1)                 # discrepancyCount
    assert_output_value(payload, "MCS-2026-04872")  # matchedInvoiceNumber
    assert_output_value(payload, "Enterprise")      # accountTier
    print("OK: overcharge=1610, count=1, invoice MCS-2026-04872, tier Enterprise")


if __name__ == "__main__":
    main()
