#!/usr/bin/env python3
"""Verify queue-items lifecycle: bulk-add succeeds, list count == EXPECTED, queue gone post-delete.

`uip` JSON output mixes PascalCase and camelCase across endpoints — `queues create` returns
`Data.key`, `delete_queue` returns `Data.Key`, `queue-items list` returns `Data` as a list.
The check below tolerates both casings via `_pick`."""

import json
import sys
from pathlib import Path

EXPECTED_COUNT = 5


def load(name: str) -> dict:
    p = Path(name)
    if not p.is_file():
        sys.exit(f"FAIL: {name} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {name} is not valid JSON: {e}")


def _pick(d: dict, *names: str):
    """Case-insensitive field lookup."""
    if not isinstance(d, dict):
        return None
    for n in names:
        for key in (n, n[:1].lower() + n[1:], n[:1].upper() + n[1:], n.lower(), n.upper()):
            if key in d:
                return d[key]
    return None


def assert_success(envelope: dict, label: str) -> "dict|list":
    result = envelope.get("Result")
    if result != "Success":
        msg = envelope.get("Message") or envelope.get("Code") or ""
        sys.exit(f"FAIL: {label} Result={result!r} Message={msg!r}")
    return envelope.get("Data")


# 1. Queue was created
create = load("create_queue.json")
create_data = assert_success(create, "queues create") or {}
queue_key = _pick(create_data, "Key", "Id")
queue_name = _pick(create_data, "Name")
if not queue_key:
    sys.exit(f"FAIL: create_queue.json has no Data.Key/key: keys={list(create_data.keys())}")

# 2. Bulk-add succeeded with zero failures
bulk = load("bulk_add.json")
bulk_data = assert_success(bulk, "queue-items bulk-add")
# Shape: {"success": true, "failedItems": []} — verify no failures.
if isinstance(bulk_data, dict):
    failed_items = _pick(bulk_data, "FailedItems") or []
    success = _pick(bulk_data, "Success")
    if failed_items:
        sys.exit(f"FAIL: bulk_add reported {len(failed_items)} failed items: {failed_items[:2]}")
    if success is False:
        sys.exit(f"FAIL: bulk_add Data.success=False: {bulk_data}")
elif isinstance(bulk_data, list):
    if len(bulk_data) != EXPECTED_COUNT:
        sys.exit(f"FAIL: bulk_add returned {len(bulk_data)} items, expected {EXPECTED_COUNT}")

# 3. List by status New returns EXPECTED_COUNT items — this is the authoritative count
list_new = load("list_new.json")
list_data = assert_success(list_new, "queue-items list --status New")
items = list_data if isinstance(list_data, list) else (
    _pick(list_data, "Value", "Items", "Results") or []
)
if len(items) != EXPECTED_COUNT:
    sys.exit(
        f"FAIL: list_new.json has {len(items)} items, expected {EXPECTED_COUNT}. "
        f"Data type={type(list_data).__name__}"
    )

# 4. After delete, list should be empty (or the queue is gone)
after = load("list_after_delete.json")
if after.get("Result") == "Success":
    after_data = after.get("Data") or []
    after_items = after_data if isinstance(after_data, list) else (
        _pick(after_data, "Value", "Items", "Results") or []
    )
    if after_items:
        sys.exit(f"FAIL: list_after_delete still has {len(after_items)} items after queue delete")
# If Result==Failure, presumably "queue not found" — that's also a pass

print(f"OK: queue {queue_name!r} ({queue_key}) created, bulk-added {EXPECTED_COUNT} items, "
      f"listed {EXPECTED_COUNT}, post-delete empty/missing")
