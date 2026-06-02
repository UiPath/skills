#!/usr/bin/env python3
"""Verify the billing-dispute-router e2e routed each amount to the right branch.

The agent builds a Flow with a switch on `disputedAmount`:
  > 5000  -> "manager_review"
  <= 500  -> "auto_resolve"
  else    -> "standard_review"
and runs `uip maestro flow debug` three times, saving each run's `--output json`
payload. This checker reads those files and asserts, for each:

  1. `Result == "Success"` and `Data.finalStatus == "Completed"`.
  2. Output `routingDecision` equals the branch the amount should hit.

A switch whose cases never match, are inverted, or are mis-wired validates
clean but routes wrong — caught here only because the flow actually runs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# file -> (amount that was debugged, expected routingDecision)
CASES = {
    "debug-high.json": (11000, "manager_review"),
    "debug-low.json": (300, "auto_resolve"),
    "debug-mid.json": (2500, "standard_review"),
}


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


def _routing_decision(data: dict):
    g = (data.get("variables") or {}).get("globals")
    if not isinstance(g, dict) or "routingDecision" not in g:
        return None
    val = g["routingDecision"]
    if isinstance(val, dict):
        for k in ("output", "value", "routingDecision"):
            if k in val:
                return val[k]
    return val


def main() -> None:
    failures: list[str] = []

    for fname, (amount, expected) in CASES.items():
        doc = _load(Path(fname))
        label = f"amount={amount}"
        if doc.get("Result") != "Success":
            failures.append(f"{label}: Result={doc.get('Result')!r} Message={doc.get('Message')!r}")
            continue
        data = doc.get("Data") or {}
        if not isinstance(data, dict) or data.get("finalStatus") != "Completed":
            fs = data.get("finalStatus") if isinstance(data, dict) else "<no Data>"
            failures.append(f"{label}: finalStatus={fs!r} (expected Completed)")
            continue
        decision = _routing_decision(data)
        if decision != expected:
            failures.append(f"{label}: routingDecision={decision!r} (expected {expected!r})")
        else:
            print(f"OK: {label} -> {expected!r}")

    if failures:
        _fail(" | ".join(failures))
    print(f"OK: all {len(CASES)} amounts routed to the correct branch at runtime")


if __name__ == "__main__":
    main()
