#!/usr/bin/env python3
"""BillingDiscrepancyDetector: debug the flow against the live tenant and grade
what the run did and returned.

The prompt names no variables, so the seeded values are mapped onto the flow's
declared inputs by meaning (`flow_io_roles.map_inputs`) and the results are
found among its declared outputs by value.

  overcharge        Invoice MCS-2026-04872, account ACCT-98201-NE, line 5.
                    The live ERP row for line 5 is 14 h contracted at $185
                    (2,590); billed 300 x 14 = 4,200, so the overcharge is 1610
                    and there is 1 discrepancy. The live CRM row for
                    ACCT-98201-NE is the Enterprise tier. The ERP and CRM reads
                    must each complete.
  unknown-line      The same invoice and account, line 99 (the invoice has 8).
  unknown-customer  Line 5 of the same invoice, account ACCT-00000-ZZ (no CRM row).

The prompt says a missing line or customer must not fail the run: it returns 0
for the overcharge and the discrepancies and empty text for the invoice number
and the tier. Those outputs must be declared and set: an output the run never
set is not empty text.

Usage: check_billing_discrepancy_detector.py overcharge|unknown-line|unknown-customer
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared import flow_io_roles as io  # noqa: E402
from _shared.advisory_flow_utils import entity_name, entity_reads  # noqa: E402
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    _fail,
    _fail_with_capture,
    _iter_flow_nodes,
    _load_flow,
    assert_flow_has_any_node_type,
    completed_node_ids_of_type,
    run_debug,
)

INVOICE = "MCS-2026-04872"
TIER = "Enterprise"
ENTITIES = ("BillingDisputeERP", "BillingDisputeCRM")

CASES = {
    "overcharge": {"account": "ACCT-98201-NE", "line": 5},
    "unknown-line": {"account": "ACCT-98201-NE", "line": 99},
    "unknown-customer": {"account": "ACCT-00000-ZZ", "line": 5},
}


def roles(case):
    """What the prompt says the automation receives, by meaning."""
    c = CASES[case]
    return {
        "invoice number": {"value": INVOICE, "keywords": [
            "invoicenumber", "invoiceno", "invoiceid", "invoiceref", "invoice"]},
        "account number": {"value": c["account"], "keywords": [
            "accountnumber", "accountno", "accountid", "account", "acct", "customer", "client"]},
        "disputed line": {"value": c["line"], "keywords": [
            "linenumber", "lineno", "linenum", "lineitem", "line"]},
        "billed unit price": {"value": 300, "keywords": [
            "unitprice", "billedprice", "price", "rate", "unitcost"]},
        "billed quantity": {"value": 14, "keywords": ["quantity", "qty", "hours", "units"]},
    }


def read_ids_by_entity():
    shape, reads = entity_reads(list(_iter_flow_nodes("**/project.uiproj")))
    by_entity = {}
    for node in reads:
        by_entity.setdefault(entity_name(node, shape), set()).add(node.get("id"))
    missing = [e for e in ENTITIES if e not in by_entity]
    if missing:
        _fail(f"no entity read on {missing}; reads found: {sorted(by_entity)}")
    return by_entity


def check_overcharge(payload, outs, by_entity):
    completed = set()
    for hint in ENTITY_QUERY_HINTS:
        completed |= completed_node_ids_of_type(payload, hint)
    for entity in ENTITIES:
        if not by_entity[entity] & completed:
            _fail_with_capture(f"the {entity} read {sorted(by_entity[entity])} did not complete in the debug run")
    print("OK: the ERP and CRM reads both completed")

    expected = {
        "the overcharge 1610": io.equals_number(1610, 0.005),
        "the discrepancy count 1": io.equals_number(1, 0.0),
        f"the invoice number {INVOICE} exactly": io.equals_exact(INVOICE),
        f"the tier {TIER} exactly": io.equals_exact(TIER),
    }
    for label, predicate in expected.items():
        if not io.find_out(outs, predicate):
            _fail_with_capture(f"no declared output is {label}: {outs}")
    print(f"OK: the outputs carry 1610, 1, {INVOICE} and {TIER}")


def check_not_found(case, outs):
    matched = [v for _t, v in outs.values()
               if io.equals_exact(INVOICE)(v) or io.equals_exact(TIER)(v) or io.equals_number(1610, 0.005)(v)]
    if matched:
        _fail_with_capture(f"[{case}] the flow returned a match {matched} for a line or customer that does not exist: {outs}")
    zeros = io.find_out(outs, io.equals_number(0, 0.0))
    empties = io.find_out(outs, io.is_empty_text)
    if len(zeros) < 2 or len(empties) < 2:
        _fail_with_capture(
            f"[{case}] expected 0 for the overcharge and the discrepancies and empty text for the "
            f"invoice number and the tier; zero outputs {zeros}, empty outputs {empties}: {outs}"
        )
    print(f"OK: [{case}] the run completed and returned 0, 0 and empty text (zeros {zeros}, empty {empties})")


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in CASES:
        sys.exit(f"usage: {os.path.basename(__file__)} {'|'.join(CASES)}")
    case = sys.argv[1]
    flow = _load_flow("**/project.uiproj")
    assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
    by_entity = read_ids_by_entity()

    inputs, _attachments, unmapped = io.map_inputs(flow, roles(case), object_fallback=None, file_path=None)
    if problem := io.unmapped_error(flow, unmapped, inputs):
        _fail(problem)
    print(f"debug inputs: {inputs}")
    payload = run_debug(inputs=inputs, timeout=360)
    outs = io.out_values(flow, payload)
    print(f"outputs: { {k: v for k, (_t, v) in outs.items()} }")

    if case == "overcharge":
        check_overcharge(payload, outs, by_entity)
    else:
        check_not_found(case, outs)


if __name__ == "__main__":
    main()
