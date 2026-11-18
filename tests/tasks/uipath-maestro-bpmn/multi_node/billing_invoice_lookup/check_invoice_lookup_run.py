#!/usr/bin/env python3
"""BillingInvoiceLookup: debug the process against the live BillingDisputeERP
entity, once per messy input, and assert what each run did and returned.

Three messy forms of two real invoices. On the live tenant MCS-2026-04872 has
8 rows and MCS-2026-05128 has 5 (an agent's whole-entity read in run
2026-11-17_04-23-38 listed 95 rows with those counts, and agents' own debug
runs returned `LineItemCount: 8` and `LineItemCount: 5` for them), so the
counts differ per invoice and a hardcoded answer cannot pass every case.

Each run must:
- complete with no incidents;
- complete a Data Service step (the lookup really ran against the tenant);
- return `matchedInvoiceNumber` = the cleaned-up invoice number and
  `lineItemCount` = that invoice's row count, read by those names. The old
  grader searched every runtime value, and the query's own rows carry both
  the invoice number and `LineNumber: 8`, so it passed a process that
  returned neither.

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
    debug_evidence,
    element_output_records,
    get_ci,
    import_exact,
    index_runtime_connectors,
    normalized_identifier,
    q,
    require_clean_run,
    root_scope,
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


def locate_bpmn() -> Path:
    try:
        return bpmn_check.resolve_bpmn_file(f"{NAME}.bpmn", exclude_under=[LIVE_RUN_DIR])
    except SystemExit:
        return Path(bpmn_check.find_bpmn_file(None))


def declarations(process: ET.Element) -> list[ET.Element]:
    variables = process.find(f"./{q(BPMN_NS, 'extensionElements')}/{q(UIPATH_NS, 'variables')}")
    return [] if variables is None else list(variables)


def input_name(process: ET.Element) -> str:
    names = [d.attrib["name"] for d in declarations(process) if d.tag == q(UIPATH_NS, "input") and d.attrib.get("name")]
    if not names:
        raise CheckFailure("the process declares no input for the invoice number")
    return next((n for n in names if n.lower() == "invoicenumber"), names[0])


def named_values(process: ET.Element, variables_data, name: str) -> list:
    """Every non-null runtime value of the output called `name`: its declared
    ids in Globals (the runtime may re-case them), any Globals key whose
    GlobalDefinitions Name is `name`, and the `name` output of the element the
    declaration belongs to (the end event)."""
    wanted = normalized_identifier(name)
    decls = [d for d in declarations(process) if normalized_identifier(d.attrib.get("name", "")) == wanted]
    scope = root_scope(variables_data)
    globals_ = get_ci(scope, "Globals", {}) or {}
    definitions = get_ci(scope, "GlobalDefinitions", {}) or {}
    ids = {normalized_identifier(d.attrib.get("id", "")) for d in decls} | {wanted}
    keys = {k for k in globals_ if normalized_identifier(k) in ids}
    keys |= {k for k, d in definitions.items() if normalized_identifier(get_ci(d, "Name", "")) == wanted}
    values = [globals_[k] for k in sorted(keys) if globals_.get(k) is not None]
    owners = tuple(d.attrib["elementId"] for d in decls if d.attrib.get("elementId"))
    for record in element_output_records(variables_data, owners) if owners else []:
        value = get_ci(record, name)
        if value is not None:
            values.append(value)
    return values


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


def completed_ids(debug_data) -> set[str]:
    return {
        get_ci(item, "ElementId")
        for item in get_ci(debug_data, "ElementExecutions", []) or []
        if isinstance(item, dict) and str(get_ci(item, "Status") or "").casefold() == "completed"
    }


def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def check_run(process, query_ids, debug_data, variables_data, invoice, count, label) -> None:
    ran = completed_ids(debug_data) & query_ids
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
    bpmn_path = locate_bpmn()
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
