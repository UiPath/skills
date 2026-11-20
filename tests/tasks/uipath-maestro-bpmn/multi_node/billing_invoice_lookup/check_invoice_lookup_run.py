#!/usr/bin/env python3
"""BillingInvoiceLookup: debug the process against the live BillingDisputeERP
entity, once per messy input, and assert what each run did and returned.

Three messy forms of two real invoices. On the live tenant MCS-2026-04872 has
8 rows and MCS-2026-05128 has 5, so the counts differ per invoice and a
hardcoded answer cannot pass every case.

Each run must:
- complete with no incidents;
- complete a Data Service step (the lookup really ran against the tenant);
- return `matchedInvoiceNumber` = the cleaned-up invoice number and
  `lineItemCount` = that invoice's row count, read by those names, not
  found among every runtime value (the query's own rows carry both the
  invoice number and `LineNumber: 8`).

The Data Service step is found by its connector key, whatever its object,
element type or id.
"""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from _shared import bpmn_check  # noqa: E402
from _shared.bpmn_live import (  # noqa: E402
    BPMN_NS,
    UIPATH_NS,
    CheckFailure,
    DebugRetry,
    completed_ids,
    debug_evidence,
    declarations,
    import_exact,
    index_runtime_connectors,
    named_values,
    q,
    require_clean_run,
    run_debug,
)

NAME = "BillingInvoiceLookup"
CONNECTOR_KEY = "uipath-uipath-dataservice"
LIVE_RUN_DIR = Path("billing-invoice-lookup-live")
# raw input the caller sends -> (invoice it must resolve to, its live row count, label)
CASES = [
    ("2026-04872", "MCS-2026-04872", 8, "missing MCS- prefix"),
    ("mcs-2026-05128", "MCS-2026-05128", 5, "wrong casing"),
    ("  MCS-2026-04872 ", "MCS-2026-04872", 8, "surrounding whitespace"),
]


def input_name(process: ET.Element) -> str:
    names = [d.attrib["name"] for d in declarations(process) if d.tag == q(UIPATH_NS, "input") and d.attrib.get("name")]
    if not names:
        raise CheckFailure("the process declares no input for the invoice number")
    return next((n for n in names if n.lower() == "invoicenumber"), names[0])


def data_service_ids(process: ET.Element) -> set[str]:
    ids = {
        element_id
        for (key, _path, _obj), element_ids in index_runtime_connectors(process).items()
        if key == CONNECTOR_KEY
        for element_id in element_ids
    }
    if not ids:
        raise CheckFailure(f"the process has no {CONNECTOR_KEY} (Data Service) step")
    return ids


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def check_run(process, query_ids, debug_data, variables_data, invoice, count, label) -> None:
    ran = set(completed_ids(debug_data)) & query_ids
    if not ran:
        raise CheckFailure(f"[{label}] no Data Service step {sorted(query_ids)} completed in the run")
    matched = named_values(process, variables_data, "matchedInvoiceNumber")
    if invoice not in [str(v).strip() for v in matched]:
        raise CheckFailure(f"[{label}] matchedInvoiceNumber: expected {invoice!r}, got {matched!r}")
    counts = named_values(process, variables_data, "lineItemCount")
    if float(count) not in [_number(v) for v in counts]:
        raise CheckFailure(f"[{label}] lineItemCount: expected {count}, got {counts!r}")
    print(f"OK: [{label}] Data Service step {sorted(ran)} completed -> {invoice}, {count} line items")


def main() -> None:
    bpmn_path = bpmn_check.locate_bpmn(f"{NAME}.bpmn", [LIVE_RUN_DIR])
    process = ET.parse(bpmn_path).getroot().find(q(BPMN_NS, "process"))
    if process is None:
        raise CheckFailure(f"{bpmn_path} has no bpmn:process")
    var = input_name(process)
    query_ids = data_service_ids(process)

    imported = import_exact(bpmn_path, bpmn_path.parent, LIVE_RUN_DIR / f"{NAME}LiveEval")
    for raw, invoice, count, label in CASES:
        print(f"[{label}] debug inputs: {{{var!r}: {raw!r}}}")
        # A read-only lookup, so a transient CLI failure may be retried.
        debug_data, instance_id = run_debug(
            imported,
            {var: raw},
            LIVE_RUN_DIR / f"debug-{label.replace(' ', '-')}.log",
            timeout=180,
            retry=DebugRetry.TRANSIENT,
        )
        evidence = debug_evidence(instance_id)
        try:
            require_clean_run(debug_data, evidence)
        except CheckFailure as error:
            raise CheckFailure(f"[{label}] {error}") from error
        check_run(process, query_ids, debug_data, evidence.variables, invoice, count, label)
    print(f"OK: all {len(CASES)} messy forms were cleaned up and looked up correctly")


if __name__ == "__main__":
    try:
        main()
    except CheckFailure as error:
        raise SystemExit(f"FAIL: {error}") from error
