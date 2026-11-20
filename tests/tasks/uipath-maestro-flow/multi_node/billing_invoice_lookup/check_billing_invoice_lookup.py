#!/usr/bin/env python3
"""BillingInvoiceLookup: debug the flow against the live BillingDisputeERP
entity and grade what each run did and returned.

The prompt names no variables, so the raw invoice number is mapped onto the
flow's declared input by meaning (`flow_io_roles.map_inputs`; a flow with a
single text input gets it whatever its name), and the results are found among
its declared outputs by value.

  found      Three messy forms of three real invoices. The live entity holds
             8 line items for MCS-2026-04872, 4 for MCS-2026-04903 and 5 for
             MCS-2026-05128 (one row per line item), so a hardcoded answer
             cannot pass every case. Each run must complete an entity read and
             return the invoice number exactly as the records hold it and the
             invoice's line count.
  not-found  "mcs-2026-99999", which no row holds. The prompt says the run must
             not fail: an entity read completes and the flow returns empty text
             and 0.

Usage: check_billing_invoice_lookup.py found|not-found
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared import flow_io_roles as io  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    _fail,
    _fail_with_capture,
    _load_flow,
    assert_flow_has_any_node_type,
    completed_node_ids_of_type,
    run_debug,
)

# raw input the caller sends -> (invoice it must resolve to, its live line-item count, label)
FOUND = [
    ("2026-04872", "MCS-2026-04872", 8, "missing MCS- prefix"),
    ("mcs-2026-04903", "MCS-2026-04903", 4, "lowercase"),
    ("  mcs-2026-05128 ", "MCS-2026-05128", 5, "spaces and lowercase"),
]
MISSING = "mcs-2026-99999"
KEYWORDS = ["invoicenumber", "invoiceno", "invoiceid", "invoiceref", "invoice", "number", "reference"]


def map_invoice(flow, raw):
    """{input id: raw}, by meaning, or onto the flow's only text input."""
    roles = {"invoice number": {"value": raw, "keywords": KEYWORDS}}
    inputs, _attachments, unmapped = io.map_inputs(flow, roles, object_fallback=None, file_path=None)
    if unmapped:
        scalars = [v for v in io.declared(flow, "in") if str(v.get("type") or "").lower() in ("string", "")]
        if len(scalars) == 1:
            return {scalars[0]["id"]: raw}
        _fail(io.unmapped_error(flow, unmapped, inputs))
    return inputs


def lookup(flow, raw, label):
    inputs = map_invoice(flow, raw)
    print(f"[{label}] debug inputs: {inputs}")
    payload = run_debug(inputs=inputs, timeout=300)
    queried = set()
    for hint in ENTITY_QUERY_HINTS:
        queried |= completed_node_ids_of_type(payload, hint)
    if not queried:
        _fail_with_capture(f"[{label}] no entity read completed in the debug run")
    outs = io.out_values(flow, payload)
    print(f"[{label}] outputs: { {k: v for k, (_t, v) in outs.items()} }")
    return outs


def check_found(flow):
    for raw, invoice, count, label in FOUND:
        outs = lookup(flow, raw, label)
        if not io.find_out(outs, io.equals_exact(invoice)):
            _fail_with_capture(f"[{label}] no declared output is {invoice} exactly: {outs}")
        if not io.find_out(outs, io.equals_number(count, 0.0)):
            _fail_with_capture(f"[{label}] no declared output is the line count {count}: {outs}")
        print(f"OK: [{label}] {raw!r} -> {invoice}, {count} line items")
    print(f"OK: all {len(FOUND)} messy forms were cleaned up and looked up correctly")


def check_not_found(flow):
    outs = lookup(flow, MISSING, "not found")
    empty = io.find_out(outs, io.is_empty_text)  # set to "", not left unset
    zero = io.find_out(outs, io.equals_number(0, 0.0))
    if not empty or not zero:
        _fail_with_capture(f"[not found] expected empty text and 0; empty outputs {empty}, zero outputs {zero}: {outs}")
    print(f"OK: [not found] the run completed and returned empty text ({empty}) and 0 ({zero})")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ("found", "not-found"):
        sys.exit(f"usage: {os.path.basename(__file__)} found|not-found")
    flow = _load_flow("**/project.uiproj")
    assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
    if sys.argv[1] == "found":
        check_found(flow)
    else:
        check_not_found(flow)


if __name__ == "__main__":
    main()
