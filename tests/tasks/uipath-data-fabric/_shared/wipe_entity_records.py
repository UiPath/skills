#!/usr/bin/env python3
"""Wipe every record from a Data Fabric entity, identified by name.

Intended for use in a task's ``pre_run``: the orchestrator pages through
all records and bulk-deletes them via ``uip df records delete`` before the
agent starts, so the agent's per-turn budget isn't spent on cleanup.

Usage:
    wipe_entity_records.py --entity-name LargePaginationTest

Optional flags:
    --batch-size N  Records per CLI delete call (default 50).
    --page-size N   Records per list page (default 200).

Exit code:
    0 when the entity ends with zero records (success, or no-op if already
      empty, or entity does not exist).
    1 on any CLI error or non-zero residual record count.
"""

import argparse
import json
import subprocess
import sys


UIP_TIMEOUT_SECONDS = 60


def uip(*args: str) -> dict:
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True,
            text=True,
            timeout=UIP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(
            f"FAIL: uip {' '.join(args)} timed out after {UIP_TIMEOUT_SECONDS}s",
            file=sys.stderr,
        )
        sys.exit(1)
    if result.returncode != 0 and not result.stdout.strip():
        print(
            f"FAIL: uip {' '.join(args)} exited {result.returncode}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(
            f"FAIL: uip {' '.join(args)} did not return JSON: {e}\n{result.stdout[:200]}",
            file=sys.stderr,
        )
        sys.exit(1)


def resolve_entity_id(name: str) -> str | None:
    resp = uip("df", "entities", "list", "--native-only")
    for entity in resp.get("Data", []):
        if entity.get("Name") == name:
            return entity["ID"]
    return None


def collect_all_ids(entity_id: str, page_size: int) -> list[str]:
    ids: list[str] = []
    cursor: str | None = None
    while True:
        args = ["df", "records", "list", entity_id, "--limit", str(page_size)]
        if cursor:
            args += ["--cursor", cursor]
        resp = uip(*args)
        data = resp.get("Data", {})
        ids.extend(r["Id"] for r in data.get("Records", []))
        if not data.get("HasNextPage"):
            break
        cursor = data.get("NextCursor")
        if not cursor:
            break
    return ids


def delete_batches(entity_id: str, ids: list[str], batch_size: int) -> tuple[int, int]:
    success = fail = 0
    for i in range(0, len(ids), batch_size):
        batch_num = i // batch_size + 1
        batch = ids[i : i + batch_size]
        resp = uip(
            "df",
            "records",
            "delete",
            entity_id,
            *batch,
            "--yes",
            "--reason",
            "automated test cleanup",
        )
        if resp.get("Result") != "Success":
            print(
                f"FAIL: batch {batch_num} returned Result={resp.get('Result')!r} "
                f"({resp.get('Message','')}: {resp.get('Instructions','')})",
                file=sys.stderr,
            )
            sys.exit(1)
        data = resp.get("Data", {})
        batch_success = data.get("SuccessCount", 0)
        batch_fail = data.get("FailureCount", 0)
        success += batch_success
        fail += batch_fail
        if batch_fail:
            failures = data.get("FailureRecords", [])
            print(
                f"WARN: batch {batch_num} reported {batch_fail} record-level failure(s): "
                f"{failures[:3]}{' ...' if len(failures) > 3 else ''}",
                file=sys.stderr,
            )
    return success, fail


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--entity-name", required=True)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--page-size", type=int, default=200)
    args = parser.parse_args()

    entity_id = resolve_entity_id(args.entity_name)
    if entity_id is None:
        print(f"OK: entity {args.entity_name!r} not found — nothing to wipe")
        return 0

    ids = collect_all_ids(entity_id, args.page_size)
    if not ids:
        print(f"OK: entity {args.entity_name!r} ({entity_id}) already empty")
        return 0

    print(f"Wiping {len(ids)} record(s) from {args.entity_name!r} ({entity_id})")
    success, fail = delete_batches(entity_id, ids, args.batch_size)
    print(f"Deleted: {success} success / {fail} fail")

    residual = collect_all_ids(entity_id, args.page_size)
    if residual:
        print(f"FAIL: {len(residual)} record(s) still present after wipe", file=sys.stderr)
        return 1
    print(f"OK: entity {args.entity_name!r} now empty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
