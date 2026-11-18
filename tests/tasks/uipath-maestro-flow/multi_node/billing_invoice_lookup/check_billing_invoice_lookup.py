#!/usr/bin/env python3
"""BillingInvoiceLookup: debug the flow against the live BillingDisputeERP
entity and assert what each run DID and returned.

Three messy forms of two real invoices. The live entity holds 8 line items for
MCS-2026-04872 and 4 for MCS-2026-04903 (one row per line item), so the counts
differ per invoice and a hardcoded answer cannot pass every case.

Each run must:
- complete an entity query (the lookup really ran against the tenant);
- return `matchedInvoiceNumber` = the cleaned-up invoice number, read by name
  (the raw input is also in the payload, so a whole-payload search would match
  the echo);
- return `lineItemCount` = the number of rows that invoice has.
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    _fail_with_capture,
    assert_flow_has_any_node_type,
    _fail,
    assert_named_equals,
    assert_output_nonempty,
    completed_node_ids_of_type,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)

# raw input the caller sends -> (invoice it must resolve to, its live line-item count, label)
CASES = [
    ("2026-04872", "MCS-2026-04872", 8, "missing MCS- prefix"),
    ("mcs-2026-04903", "MCS-2026-04903", 4, "wrong casing"),
    ("  MCS-2026-04872 ", "MCS-2026-04872", 8, "surrounding whitespace"),
]


def input_var():
    in_vars = read_flow_input_vars(find_project_dir())
    if not in_vars:
        sys.exit("FAIL: the flow declares no input for the invoice number")
    return next((v for v in in_vars if v.lower() == "invoicenumber"), in_vars[0])


def check_run(payload, invoice, count, label):
    queried = set()
    for hint in ENTITY_QUERY_HINTS:
        queried |= completed_node_ids_of_type(payload, hint)
    if not queried:
        _fail_with_capture(f"[{label}] no entity query completed in the debug run")
    assert_named_equals(payload, "matchedInvoiceNumber", invoice, case_sensitive=True)
    got = assert_output_nonempty(payload, "lineItemCount")
    try:
        ok = float(str(got).strip()) == count
    except ValueError:
        ok = False
    if not ok:
        _fail(f"[{label}] output 'lineItemCount': expected {count}, got {got!r}")
    print(f"OK: [{label}] query {sorted(queried)} completed -> {invoice}, {count} line items")


def main():
    assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
    var = input_var()
    for raw, invoice, count, label in CASES:
        print(f"[{label}] debug inputs: {{{var!r}: {raw!r}}}")
        check_run(run_debug(inputs={var: raw}, timeout=180), invoice, count, label)
    print(f"OK: all {len(CASES)} messy forms were cleaned up and looked up correctly")


if __name__ == "__main__":
    main()
