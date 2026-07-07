#!/usr/bin/env python3
"""Assert an AgedInvoicePayment SDD captures the full PDD-derived design.

This is the deterministic companion to the LLM judge. It intentionally checks
business shape, not exact prose: the design must keep the long-form aged-invoice
case as one Maestro case with the expected primary stages, exception lanes, task
type mix, triage scoring, payment-risk gating, and child payment tracking case.
"""

from __future__ import annotations

import re
import sys


PRIMARY_STAGE_PATTERNS = {
    "Intake": r"intake|registration",
    "Enrichment": r"enrichment|context",
    "Triage": r"triage",
    "AP Review": r"ap review|accounts payable|ownership",
    "Exception Resolution": r"exception resolution|resolution",
    "Supplier Collaboration": r"supplier collaboration|supplier",
    "Payment Risk": r"payment risk|risk",
    "Approval": r"approval",
    "Closure": r"closure|close",
}

EXCEPTION_PATTERNS = {
    "SLA Escalation": r"sla.*escalation|escalation",
    "Automation Incident": r"automation.*incident|incident|automation failure|failed (api|rpa|automation)",
    "Reopen": r"reopen|supplier dispute",
    "Compliance Hold": r"compliance.*hold|payment.?risk.*hold|hold",
}

TASK_TYPE_PATTERNS = {
    "api-workflow": r"api[- ]workflow",
    "connector": r"execute-connector-activity|wait-for-connector|connector|outlook|servicenow|slack|sap",
    "agent": r"\bagent\b",
    "action": r"\baction\b|hitl|human",
    "wait-for-timer": r"wait-for-timer|\btimer\b|reminder",
    "rpa": r"\brpa\b|robot",
    "case-management": r"case-management|child case|sub-case|subcase|payment tracking",
}


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _read(path: str) -> str:
    try:
        return open(path, encoding="utf-8").read()
    except OSError as exc:
        _fail(f"could not read {path}: {exc}")


def _heading_names(text: str, pattern: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(pattern, text, re.M)]


def _has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.I | re.S) is not None


def main() -> None:
    if len(sys.argv) != 2:
        _fail("usage: check_aged_invoice_sdd.py <sdd.md|sdd.draft.md>")

    text = _read(sys.argv[1])
    lowered = text.lower()

    primary_headings = _heading_names(text, r"^### +Stage +[0-9]+: +(.+)$")
    if len(primary_headings) < 8:
        _fail(
            f"expected >=8 primary stages from the PDD's 9-stage design; "
            f"found {len(primary_headings)}: {primary_headings}"
        )

    missing_primary = [
        name
        for name, pattern in PRIMARY_STAGE_PATTERNS.items()
        if not _has(" ".join(primary_headings), pattern)
    ]
    if missing_primary:
        _fail(
            "missing primary stage family/families: "
            + ", ".join(missing_primary)
            + f"; headings={primary_headings}"
        )

    secondary_headings = _heading_names(
        text, r"^### +(?:Secondary Stage|Exception Stage): +(.+)$"
    )
    exception_text = " ".join(secondary_headings) + "\n" + text
    missing_exception = [
        name
        for name, pattern in EXCEPTION_PATTERNS.items()
        if not _has(exception_text, pattern)
    ]
    if missing_exception:
        _fail(
            "missing exception lane(s): "
            + ", ".join(missing_exception)
            + f"; secondary headings={secondary_headings}"
        )

    missing_task_types = [
        name for name, pattern in TASK_TYPE_PATTERNS.items() if not _has(text, pattern)
    ]
    if missing_task_types:
        _fail("missing task-type signal(s): " + ", ".join(missing_task_types))

    if not ("rootcause" in lowered or "root cause" in lowered):
        _fail("triage must capture root-cause classification")
    if not ("priorityscore" in lowered or "priority score" in lowered or "sla score" in lowered):
        _fail("triage must capture priority/SLA scoring")
    if not ("paymentrisk" in lowered or "payment risk" in lowered):
        _fail("payment risk stage/gate is missing")
    if not ("paymenttracking" in lowered or "payment tracking" in lowered):
        _fail("payment tracking child case is missing")

    for system in ("mock erp", "outlook", "servicenow", "slack", "sap"):
        if system not in lowered:
            _fail(f"missing external system/integration signal: {system}")

    print(
        "OK: AgedInvoicePayment SDD preserves the PDD-derived 9-stage design, "
        "exception lanes, task-type mix, triage scoring, payment-risk gate, "
        "payment tracking child case, and integration footprint"
    )


if __name__ == "__main__":
    main()
