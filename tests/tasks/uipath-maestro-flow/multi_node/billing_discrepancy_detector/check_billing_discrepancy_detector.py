#!/usr/bin/env python3
"""BillingDiscrepancyDetector: debug the flow once against
the seeded tenant and assert what the run DID, not only what it returned.

Inputs map to ERP line 5 (Custom Integration Build, contracted 14 x 185 = 2590),
disputed at 300 x 14 = 4200, so the overcharge is 1610. CRM account
ACCT-98201-NE is the Enterprise tier.

Effects asserted on the debug trace:
- the ERP query and the CRM query each completed (both lookups really ran);
- the merge that joins them completed.

Outputs asserted by the names the prompt gives them. `matchedInvoiceNumber` is
also a flow input, so it is read by name rather than searched for among all
values, where the input would echo it.
"""
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
sys.path.insert(0, os.path.join(_d, "_shared"))
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    _fail_with_capture,
    _iter_flow_nodes,
    assert_flow_has_any_node_type,
    assert_named_equals,
    assert_node_type_executed,
    completed_node_ids_of_type,
    run_debug,
)
from advisory_flow_utils import entity_name, entity_reads  # noqa: E402

INPUTS = {
    "invoiceNumber": "MCS-2026-04872",
    "accountNumber": "ACCT-98201-NE",
    "disputedLineNumber": 5,
    "disputedUnitPrice": 300,
    "disputedQuantity": 14,
}
ENTITIES = ("BillingDisputeERP", "BillingDisputeCRM")


def read_ids_by_entity():
    shape, reads = entity_reads(list(_iter_flow_nodes("**/project.uiproj")))
    by_entity = {}
    for node in reads:
        by_entity.setdefault(entity_name(node, shape), set()).add(node.get("id"))
    missing = [e for e in ENTITIES if e not in by_entity]
    if missing:
        sys.exit(f"FAIL: no entity read on {missing}; reads found: {sorted(by_entity)}")
    return by_entity


def main():
    assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
    by_entity = read_ids_by_entity()

    print(f"debug inputs: {INPUTS}")
    payload = run_debug(inputs=INPUTS, timeout=240)

    completed = set()
    for hint in ENTITY_QUERY_HINTS:
        completed |= completed_node_ids_of_type(payload, hint)
    for entity in ENTITIES:
        if not by_entity[entity] & completed:
            _fail_with_capture(
                f"the {entity} query {sorted(by_entity[entity])} did not complete in the debug run"
            )
    print("OK: the ERP and CRM queries both completed in the debug run")

    assert_node_type_executed(payload, "core.logic.merge")
    print("OK: the merge joining the two lookups completed")

    assert_named_equals(payload, "totalOvercharge", 1610)
    assert_named_equals(payload, "discrepancyCount", 1)
    assert_named_equals(payload, "matchedInvoiceNumber", "MCS-2026-04872", case_sensitive=True)
    assert_named_equals(payload, "accountTier", "Enterprise")
    print("OK: totalOvercharge=1610, discrepancyCount=1, matchedInvoiceNumber=MCS-2026-04872, accountTier=Enterprise")


if __name__ == "__main__":
    main()
