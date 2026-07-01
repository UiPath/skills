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


def find_entity_id(name: str) -> tuple[str | None, str | None]:
    """Return (entity_id, folder_key) — folder_key is empty string for tenant-scoped."""
    # Try with --include-folders first (sees both tenant and folder-scoped entities).
    # If the CLI version doesn't support the flag, fall back to plain --native-only.
    for extra in (["--include-folders"], []):
        code, out, err = run_uip("df", "entities", "list", "--native-only", *extra)
        if code != 0 or not out.strip():
            continue
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            continue
        inner = data.get("Data") if isinstance(data, dict) else None
        recs = inner if isinstance(inner, list) else (inner or {}).get("Records") or (inner or {}).get("records") or []
        for ent in recs:
            if not isinstance(ent, dict):
                continue
            if (ent.get("Name") or ent.get("name")) == name:
                folder_key = ent.get("FolderKey") or ent.get("folderKey") or ""
                return (ent.get("ID") or ent.get("Id") or ent.get("id"), folder_key)
    return None, None


def total_count(entity_id: str, folder_key: str = "") -> int | None:
    args = ["df", "records", "list", entity_id, "--limit", "1"]
    if folder_key:
        args += ["--folder-key", folder_key]
    code, out, err = run_uip(*args)
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
        description="Assert an entity's record count is exactly --expected, or within [--min, --max]."
    )
    parser.add_argument("--entity-name", required=True)
    parser.add_argument("--expected", type=int, help="Exact count required.")
    parser.add_argument("--min", type=int, dest="min_count", help="Lower bound (inclusive) for range check.")
    parser.add_argument("--max", type=int, dest="max_count", help="Upper bound (inclusive) for range check.")
    args = parser.parse_args()

    if args.expected is None and args.min_count is None and args.max_count is None:
        parser.error("provide --expected or a --min/--max range")
    if args.expected is not None and (args.min_count is not None or args.max_count is not None):
        parser.error("--expected is mutually exclusive with --min/--max")

    entity_id, folder_key = find_entity_id(args.entity_name)
    if not entity_id:
        print(f"FAIL: entity '{args.entity_name}' not found (searched tenant + folders)", file=sys.stderr)
        sys.exit(1)

    actual = total_count(entity_id, folder_key)
    if actual is None:
        sys.exit(1)

    if args.expected is not None:
        if actual != args.expected:
            print(
                f"FAIL: entity '{args.entity_name}' has {actual} record(s), expected {args.expected} "
                f"(agent likely inserted/deleted records — brownfield contract violated)",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"OK: '{args.entity_name}' has {actual} record(s) — matches expected {args.expected}")
        sys.exit(0)

    lo = args.min_count if args.min_count is not None else 0
    hi = args.max_count if args.max_count is not None else float("inf")
    if actual < lo or actual > hi:
        bound = f"{lo}..{args.max_count if args.max_count is not None else '∞'}"
        print(
            f"FAIL: entity '{args.entity_name}' has {actual} record(s), expected in {bound}",
            file=sys.stderr,
        )
        sys.exit(1)
    bound = f"{lo}..{args.max_count if args.max_count is not None else '∞'}"
    print(f"OK: '{args.entity_name}' has {actual} record(s) — within {bound}")
    sys.exit(0)


if __name__ == "__main__":
    main()
