#!/usr/bin/env python3
"""Validator for licensing_read_e2e.yaml artifacts.

Each emitted JSON file must be a well-formed `uip platform` response envelope
with `Result == "Success"` and a `Data` field. `available.json` must have a
non-empty `Data` list (every account owns at least one user bundle).
`details.json` is conditional — required only when `rules.json` lists at least
one group; if rules is empty, details is skipped.

Exit 0 on pass, 1 on fail. Reads from the task sandbox cwd (coder_eval invokes
run_command criteria with cwd set to the sandbox root).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load(name: str) -> dict | None:
    path = Path(name)
    if not path.exists():
        print(f"FAIL: {name} does not exist", file=sys.stderr)
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"FAIL: {name} is not valid JSON: {e}", file=sys.stderr)
        return None


def _check_envelope(name: str, data: dict) -> bool:
    if data.get("Result") != "Success":
        print(
            f"FAIL: {name} Result != 'Success' (got {data.get('Result')!r})",
            file=sys.stderr,
        )
        return False
    if "Data" not in data:
        print(f"FAIL: {name} missing 'Data' field", file=sys.stderr)
        return False
    return True


def main() -> int:
    errors = 0

    for fname in ["available.json", "rules.json", "consumables.json"]:
        data = _load(fname)
        if data is None or not _check_envelope(fname, data):
            errors += 1

    available = _load("available.json")
    if available is not None and not available.get("Data"):
        print(
            "FAIL: available.json Data is empty — expected at least one user bundle",
            file=sys.stderr,
        )
        errors += 1

    rules = _load("rules.json")
    if rules is not None and rules.get("Data"):
        details = _load("details.json")
        if details is None or not _check_envelope("details.json", details):
            errors += 1
    else:
        print(
            "INFO: skipping details.json check — rules.json has no groups",
            file=sys.stderr,
        )

    if errors:
        return 1
    print("OK: all licensing JSON envelopes valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
