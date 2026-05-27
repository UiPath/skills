#!/usr/bin/env python3
"""
Idempotent pre-seed / post-reset helper for brownfield Data Fabric tests.

Brownfield tests reuse a fixed-name entity across runs. The harness must:
  - **Pre-run**: ensure the entity exists with its seed records (skip if
    already present — no-op for steady-state, set up on first run).
  - **Post-run**: revert the entity to its seed state (wipe whatever the
    agent inserted/updated and re-insert the canonical seed records). The
    entity itself is preserved.

Usage:
    # Pre-run: ensure entity + seed data exist; skip if entity already present.
    seed_entity.py --entity-name IntegrationOrders \
        --schema-file seeds/integration_orders.schema.json \
        --records-file seeds/integration_orders.records.json

    # Post-run: wipe records and re-insert seed. Creates the entity if missing
    # (same first-time setup as pre-run).
    seed_entity.py --entity-name IntegrationOrders \
        --schema-file seeds/integration_orders.schema.json \
        --records-file seeds/integration_orders.records.json \
        --reset

Schema file format (passed verbatim as the body of `uip df entities create`):
    {
      "displayName": "Integration Orders",
      "fields": [
        {"fieldName": "Code",   "type": "STRING"},
        {"fieldName": "Value",  "type": "DECIMAL"},
        {"fieldName": "Status", "type": "STRING"}
      ]
    }

Records file format (passed verbatim as the body of `uip df records insert`):
    [
      {"Code": "ORD-001", "Value": 100.00, "Status": "Pending"},
      ...
    ]

Auth: uses the active `uip` login. If `uip` calls fail, prints WARN and
exits 0 — pre-seed must never block a test from running.

Exit 0 on success or skip; exit 1 only on argument errors.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


UIP_TIMEOUT_SECONDS = 60
UIP_LONG_TIMEOUT_SECONDS = 180  # entities create can be slow server-side


def run_uip(*args: str, input_text: str | None = None, timeout: int = UIP_TIMEOUT_SECONDS) -> tuple[int, str, str]:
    """Run `uip <args> --output json`. Return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
            input=input_text,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return result.returncode, result.stdout, result.stderr


def count_records(entity_id: str) -> int:
    """Return TotalCount from `records list --limit 1`, or -1 if the call failed."""
    code, out, err = run_uip("df", "records", "list", entity_id, "--limit", "1")
    if code != 0 or not out.strip():
        return -1
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return -1
    inner = (data.get("Data") if isinstance(data, dict) else None) or {}
    tc = inner.get("TotalCount")
    return int(tc) if isinstance(tc, int) else -1


def list_native_entities() -> list[dict]:
    code, out, err = run_uip("df", "entities", "list", "--native-only")
    if code != 0 or not out.strip():
        print(f"WARN: uip df entities list failed (exit {code}): {err.strip()}", file=sys.stderr)
        return []
    try:
        data = json.loads(out)
    except json.JSONDecodeError as e:
        print(f"WARN: could not parse entities list output: {e}", file=sys.stderr)
        return []
    inner = data.get("Data") if isinstance(data, dict) else None
    if isinstance(inner, dict):
        return inner.get("Records") or inner.get("records") or []
    if isinstance(inner, list):
        return inner
    return []


def find_entity_id(entities: list[dict], name: str) -> str | None:
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        if (ent.get("Name") or ent.get("name")) == name:
            return ent.get("ID") or ent.get("Id") or ent.get("id")
    return None


def create_entity(name: str, schema: dict) -> str | None:
    """Create the entity and return its new ID, or None on failure.

    `entities create` can be slow server-side and occasionally outlasts the
    CLI timeout even though the entity is created. On timeout (exit 124),
    re-list and look up by name as a fallback.
    """
    body = json.dumps(schema)
    code, out, err = run_uip(
        "df", "entities", "create", name, "--body", body,
        timeout=UIP_LONG_TIMEOUT_SECONDS,
    )
    if code == 0:
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            print(f"WARN: could not parse entities create output: {out[:200]}", file=sys.stderr)
            return None
        if isinstance(data, dict):
            return (data.get("Data") or {}).get("ID")
        return None

    if code == 124:
        # CLI gave up but the create may have landed server-side. Look it up by name.
        print(f"WARN: uip df entities create {name} timed out; checking if it landed server-side...", file=sys.stderr)
        eid = find_entity_id(list_native_entities(), name)
        if eid:
            print(f"OK: entity {name} found after timeout ({eid}) — using it")
            return eid

    print(f"WARN: uip df entities create {name} failed (exit {code}): {err.strip()}", file=sys.stderr)
    return None


def insert_records(entity_id: str, records: list[dict]) -> bool:
    """Batch-insert records; return True on success."""
    body = json.dumps(records)
    code, _out, err = run_uip("df", "records", "insert", entity_id, "--body", body)
    if code != 0:
        print(f"WARN: uip df records insert {entity_id} failed (exit {code}): {err.strip()}", file=sys.stderr)
        return False
    return True


def wipe_records(entity_id: str) -> None:
    """Page through and delete every record on the entity.

    Uses --limit 200 batches. Continues on per-batch failures so a transient
    error doesn't leave the entity half-wiped without surfacing the issue.
    """
    deleted = 0
    while True:
        code, out, err = run_uip("df", "records", "list", entity_id, "--limit", "200")
        if code != 0 or not out.strip():
            print(f"WARN: uip df records list during wipe failed (exit {code}): {err.strip()}", file=sys.stderr)
            return
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            print("WARN: could not parse records list output during wipe", file=sys.stderr)
            return
        records_body = (data.get("Data") if isinstance(data, dict) else None) or {}
        records = records_body.get("Records") or records_body.get("records") or []
        if not records:
            break
        ids = [r.get("Id") or r.get("ID") for r in records if isinstance(r, dict)]
        ids = [i for i in ids if i]
        if not ids:
            break
        del_code, _del_out, del_err = run_uip("df", "records", "delete", entity_id, *ids)
        if del_code != 0:
            print(f"WARN: uip df records delete batch failed (exit {del_code}): {del_err.strip()}", file=sys.stderr)
            return
        deleted += len(ids)
        if not records_body.get("HasNextPage"):
            # No more pages — but more records may exist if delete shifted pagination.
            # Loop once more to be safe; the next list will return empty if truly clean.
            continue
    if deleted:
        print(f"OK: wiped {deleted} record(s) from entity {entity_id}")


def load_json(path: Path) -> dict | list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"FAIL: could not read JSON from {path}: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Idempotent pre-seed / post-reset for brownfield Data Fabric tests."
    )
    parser.add_argument("--entity-name", required=True)
    parser.add_argument(
        "--schema-file", required=True, type=Path,
        help="JSON file with entity-create body (fields + optional displayName).",
    )
    parser.add_argument(
        "--records-file", type=Path, default=None,
        help=(
            "Optional JSON file with a records array. Omit for schema-only mode "
            "(entity is created if missing; --reset wipes records but inserts none)."
        ),
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Wipe existing records and re-insert seed even if entity is already present.",
    )
    args = parser.parse_args()

    schema = load_json(args.schema_file)
    if not isinstance(schema, dict):
        print(f"FAIL: schema file {args.schema_file} must be a JSON object", file=sys.stderr)
        sys.exit(1)

    # Schema-only mode when --records-file is omitted: entity is ensured /
    # reset to *zero* records. Used by tests where the agent's job is to
    # populate records itself (e.g. CSV import).
    if args.records_file is None:
        records: list = []
    else:
        records = load_json(args.records_file)
        if not isinstance(records, list):
            print(f"FAIL: records file {args.records_file} must be a JSON array", file=sys.stderr)
            sys.exit(1)

    entities = list_native_entities()
    entity_id = find_entity_id(entities, args.entity_name)

    # Decide whether to seed:
    #   - --reset: always wipe + re-seed (post-run revert path).
    #   - No entity: create + seed.
    #   - Entity exists: check record count. If schema-only test (empty seed
    #     list), skip. If seeded test and record count matches expected, skip.
    #     Otherwise wipe + re-seed (e.g. prior run drained the entity).
    if entity_id and not args.reset:
        if len(records) == 0:
            print(f"OK: entity {args.entity_name} exists ({entity_id}); schema-only — skipping seed")
            sys.exit(0)
        existing = count_records(entity_id)
        if existing == len(records):
            print(f"OK: entity {args.entity_name} exists with {existing} record(s); skipping seed")
            sys.exit(0)
        print(
            f"INFO: entity {args.entity_name} exists but has {existing} record(s) "
            f"(expected {len(records)}); wiping and re-seeding",
            file=sys.stderr,
        )
        wipe_records(entity_id)

    elif entity_id is None:
        entity_id = create_entity(args.entity_name, schema)
        if entity_id is None:
            sys.exit(0)
        print(f"OK: created entity {args.entity_name} ({entity_id})")
    else:
        # --reset path: wipe whatever the agent left behind.
        wipe_records(entity_id)

    if records:
        if insert_records(entity_id, records):
            print(f"OK: seeded {len(records)} record(s) into {args.entity_name}")
    else:
        print(f"OK: no seed records configured for {args.entity_name} (schema-only)")
    sys.exit(0)


if __name__ == "__main__":
    main()
