#!/usr/bin/env python3
"""
Brownfield end-state assertion: confirm an entity has exactly the expected
record count after the agent finishes.

Used as a `run_command` success criterion to replace pattern-based negative
guards ("agent must NOT call records insert/delete"). Pattern guards fail
on intent (any attempted command) even when the command was rejected by
the server. This script validates the actual entity state, so a server-side
rejection (isUnique violation, required-field missing, etc.) doesn't fail
the test as long as the entity ends up unchanged.

Usage (as a success_criteria run_command):
    assert_record_count.py --entity-name IntegrationOrders --expected 4

Exit codes:
    0  — entity exists and TotalCount == --expected
    1  — entity exists but TotalCount differs, OR entity not found, OR uip
         call failed (the criterion will FAIL, surfacing the mismatch)
"""

import argparse
import json
import subprocess
import sys


UIP_TIMEOUT_SECONDS = 60


def run_uip(*args: str) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {UIP_TIMEOUT_SECONDS}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return result.returncode, result.stdout, result.stderr


def find_entity_id(name: str) -> str | None:
    code, out, err = run_uip("df", "entities", "list", "--native-only")
    if code != 0 or not out.strip():
        print(f"FAIL: uip df entities list failed: {err.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        print("FAIL: could not parse entities list output", file=sys.stderr)
        return None
    inner = data.get("Data") if isinstance(data, dict) else None
    recs = inner if isinstance(inner, list) else (inner or {}).get("Records") or (inner or {}).get("records") or []
    for ent in recs:
        if not isinstance(ent, dict):
            continue
        if (ent.get("Name") or ent.get("name")) == name:
            return ent.get("ID") or ent.get("Id") or ent.get("id")
    return None


def total_count(entity_id: str) -> int | None:
    code, out, err = run_uip("df", "records", "list", entity_id, "--limit", "1")
    if code != 0 or not out.strip():
        print(f"FAIL: uip df records list failed: {err.strip()}", file=sys.stderr)
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        print("FAIL: could not parse records list output", file=sys.stderr)
        return None
    inner = (data.get("Data") if isinstance(data, dict) else None) or {}
    tc = inner.get("TotalCount")
    return int(tc) if isinstance(tc, int) else None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Assert an entity has exactly the expected record count."
    )
    parser.add_argument("--entity-name", required=True)
    parser.add_argument("--expected", required=True, type=int)
    args = parser.parse_args()

    entity_id = find_entity_id(args.entity_name)
    if not entity_id:
        print(f"FAIL: entity '{args.entity_name}' not found", file=sys.stderr)
        sys.exit(1)

    actual = total_count(entity_id)
    if actual is None:
        sys.exit(1)

    if actual != args.expected:
        print(
            f"FAIL: entity '{args.entity_name}' has {actual} record(s), expected {args.expected} "
            f"(agent likely inserted/deleted records — brownfield contract violated)",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"OK: '{args.entity_name}' has {actual} record(s) — matches expected {args.expected}")
    sys.exit(0)


if __name__ == "__main__":
    main()
