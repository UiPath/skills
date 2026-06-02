#!/usr/bin/env python3
"""Verify the billing-discrepancy-detector e2e computed the right result.

The agent builds a Flow that queries `BillingDisputeERP` (invoice line items)
and `BillingDisputeCRM` (account) in parallel, merges, and compares a disputed
line against its contracted ERP amount. It runs `uip maestro flow debug` with a
fixed input and saves `debug-output.json`.

Against the seeded data, the input
  { invoiceNumber: MCS-2026-04872, accountNumber: ACCT-98201-NE,
    disputedLineNumber: 5, disputedUnitPrice: 300, disputedQuantity: 14 }
must produce:
  - totalOvercharge   = 1610   (invoiced 300*14=4200 - contracted ERP line 5 = 2590)
  - discrepancyCount  = 1
  - matchedInvoiceNumber = "MCS-2026-04872"
  - accountTier       = "Enterprise"

Wrong `$vars` output paths, a dropped merge branch, or a bad comparison all
validate clean but fail here, because the flow actually ran.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RESULTS = Path("debug-output.json")

EXPECTED = {
    "totalOvercharge": 1610,
    "discrepancyCount": 1,
    "matchedInvoiceNumber": "MCS-2026-04872",
    "accountTier": "Enterprise",
}


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load() -> dict:
    if not RESULTS.is_file():
        _fail(f"missing {RESULTS} — the agent did not save the debug run")
    try:
        doc = json.loads(RESULTS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"{RESULTS} is not valid JSON: {e}")
    if not isinstance(doc, dict):
        _fail(f"{RESULTS} should be a JSON object, got {type(doc).__name__}")
    return doc


def _output_value(globals_map: dict, name: str):
    if name not in globals_map:
        return None
    val = globals_map[name]
    if isinstance(val, dict):
        for k in ("output", "value", name):
            if k in val:
                return val[k]
    return val


def _num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f.is_integer() else f


def main() -> None:
    doc = _load()
    if doc.get("Result") != "Success":
        _fail(f"Result={doc.get('Result')!r} Message={doc.get('Message')!r}")
    data = doc.get("Data") or {}
    if not isinstance(data, dict):
        _fail("Data is not an object")
    if data.get("finalStatus") != "Completed":
        _fail(f"finalStatus={data.get('finalStatus')!r} (expected Completed)")

    gmap = (data.get("variables") or {}).get("globals")
    if not isinstance(gmap, dict):
        _fail("Data.variables.globals missing or not an object")

    failures: list[str] = []
    for name, expected in EXPECTED.items():
        actual = _output_value(gmap, name)
        if isinstance(expected, int):
            if _num(actual) != expected:
                failures.append(f"{name}={actual!r} (expected {expected})")
        else:
            if actual != expected:
                failures.append(f"{name}={actual!r} (expected {expected!r})")

    if failures:
        _fail(" | ".join(failures))
    print("OK: overcharge=1610, count=1, invoice MCS-2026-04872, tier Enterprise — all correct at runtime")


if __name__ == "__main__":
    main()
