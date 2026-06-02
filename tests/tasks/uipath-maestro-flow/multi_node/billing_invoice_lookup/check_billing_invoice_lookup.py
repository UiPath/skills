#!/usr/bin/env python3
"""Verify the billing-invoice-lookup e2e resolved all three malformed inputs.

The agent builds a Flow that normalizes a raw `invoiceNumber` (trim, uppercase,
ensure the "MCS-" prefix) and queries the seeded `BillingDisputeERP` Data
Fabric entity. It then runs `uip maestro flow debug` three times — once per
malformed form — saving each run's `--output json` payload to a file.

This checker reads those three files and asserts, for every one:

  1. The CLI envelope reports `Result == "Success"`.
  2. `Data.finalStatus == "Completed"` (the run actually finished).
  3. Output `matchedInvoiceNumber == "MCS-2026-04872"` — normalization worked.
  4. Output `lineItemCount == 8` — the query hit the right rows against the
     seeded entity (8 line items exist for that invoice).

Each assertion is on a runtime side effect, so a flow that validates clean but
is misconfigured (bad query expression, wrong connection/folder key, dropped
normalization) fails here even though `uip maestro flow validate` passed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# file -> the raw input form it was debugged with (for error messages)
CASES = {
    "debug-prefix.json": "2026-04872 (missing MCS- prefix)",
    "debug-casing.json": "mcs-2026-04872 (wrong casing)",
    "debug-whitespace.json": " MCS-2026-04872 (leading whitespace)",
}
EXPECTED_INVOICE = "MCS-2026-04872"
EXPECTED_LINE_COUNT = 8


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load(path: Path) -> dict:
    if not path.is_file():
        _fail(f"missing {path} — the agent did not save this debug run")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fail(f"{path} is not valid JSON: {e}")
    if not isinstance(doc, dict):
        _fail(f"{path} should be a JSON object, got {type(doc).__name__}")
    return doc


def _globals(data: dict) -> dict:
    g = (data.get("variables") or {}).get("globals")
    return g if isinstance(g, dict) else {}


def _output_value(globals_map: dict, name: str):
    """A global may surface as a bare value or wrapped as {"output": ...} /
    {"value": ...}. Return whatever scalar it carries."""
    if name not in globals_map:
        return None
    val = globals_map[name]
    if isinstance(val, dict):
        for k in ("output", "value", name):
            if k in val:
                return val[k]
    return val


def main() -> None:
    failures: list[str] = []

    for fname, form in CASES.items():
        doc = _load(Path(fname))
        if doc.get("Result") != "Success":
            failures.append(
                f"{form}: Result={doc.get('Result')!r} Message={doc.get('Message')!r}"
            )
            continue
        data = doc.get("Data") or {}
        if not isinstance(data, dict):
            failures.append(f"{form}: Data is not an object")
            continue
        if data.get("finalStatus") != "Completed":
            failures.append(f"{form}: finalStatus={data.get('finalStatus')!r} (expected Completed)")
            continue

        gmap = _globals(data)
        matched = _output_value(gmap, "matchedInvoiceNumber")
        count = _output_value(gmap, "lineItemCount")

        if matched != EXPECTED_INVOICE:
            failures.append(
                f"{form}: matchedInvoiceNumber={matched!r} (expected {EXPECTED_INVOICE!r}) "
                f"— normalization or query filter is wrong"
            )
        try:
            count_num = int(count)
        except (TypeError, ValueError):
            count_num = None
        if count_num != EXPECTED_LINE_COUNT:
            failures.append(
                f"{form}: lineItemCount={count!r} (expected {EXPECTED_LINE_COUNT})"
            )

        if not any(f.startswith(form) for f in failures):
            print(f"OK: {form} -> {EXPECTED_INVOICE}, {EXPECTED_LINE_COUNT} line items")

    if failures:
        _fail(" | ".join(failures))
    print(f"OK: all {len(CASES)} malformed invoice-number forms resolved correctly at runtime")


if __name__ == "__main__":
    main()
