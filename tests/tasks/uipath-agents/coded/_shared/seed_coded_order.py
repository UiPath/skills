#!/usr/bin/env python3
"""Seed CE_CodedOrder entity with a CHOICE_SET_SINGLE Status field.

Two-phase seed:
  1. Seed `CE_CodedOrderStatus` choice set (idempotent via seed_choice_set.py).
  2. Look up the choice set ID.
  3. Create `CE_CodedOrder` entity with Status field bound to that choice set ID.
  4. Insert seed records (Status values written as NumberId integers).

Idempotent: skips entity creation if CE_CodedOrder already exists.

Usage (from pre_run):
    python3 seed_coded_order.py

Env:
    SKILLS_REPO_PATH — repo root (set by coder-eval Makefile)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parent / "seeds"
CHOICE_SET_SPEC = SEEDS_DIR / "coded_order_status.choice_set.json"
RECORDS_FILE = SEEDS_DIR / "coded_order.records.json"

ENTITY_NAME = "CE_CodedOrder"
CHOICE_SET_NAME = "CE_CodedOrderStatus"

# Status NumberId map matching the choice_set.json values list order (0-indexed)
STATUS_MAP = {"Open": 0, "Processing": 1, "Shipped": 2, "Delivered": 3, "Closed": 4}

UIP_TIMEOUT = 120
LIST_RETRY_ATTEMPTS = 3
LIST_RETRY_DELAY = 5


def run_uip(*args: str, timeout: int = UIP_TIMEOUT) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            ["uip", *args, "--output", "json"],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 124, "", f"timed out after {timeout}s"
    except FileNotFoundError:
        return 127, "", "uip CLI not on PATH"
    return r.returncode, r.stdout, r.stderr


def parse_json(text: str) -> dict:
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def seed_choice_set() -> str | None:
    """Seed the choice set and return its ID."""
    # Use the platform helper if available, otherwise do it inline
    platform_seeder = (
        Path(__file__).resolve().parents[3]
        / "uipath-platform" / "data-fabric" / "_shared" / "seed_choice_set.py"
    )
    if platform_seeder.is_file():
        r = subprocess.run(
            [sys.executable, str(platform_seeder), "--spec", str(CHOICE_SET_SPEC)],  # uses same python
            capture_output=True, text=True, timeout=180,
        )
        if r.returncode != 0:
            print(f"FAIL: seed_choice_set.py failed: {r.stderr.strip()}", file=sys.stderr)
            return None
        print(r.stdout.strip())
    else:
        # Inline fallback: create choice set directly
        spec = json.loads(CHOICE_SET_SPEC.read_text())
        code, out, err = run_uip("df", "choice-sets", "create", spec["name"],
                                  "--display-name", spec.get("displayName", spec["name"]))
        if code != 0 and "already exists" not in (out + err).lower():
            print(f"WARN: choice-sets create: {err.strip()}", file=sys.stderr)
        for val in spec.get("values", []):
            run_uip("df", "choice-sets", "add-value", spec["name"], "--value", val)

    # Look up ID (with retry for parallel pre_run races)
    for attempt in range(1, LIST_RETRY_ATTEMPTS + 1):
        code, out, err = run_uip("df", "choice-sets", "list")
        if code == 0:
            data = parse_json(out)
            raw = data.get("Data", [])
            items = raw if isinstance(raw, list) else raw.get("Items", []) if isinstance(raw, dict) else []
            for cs in items:
                if cs.get("Name") == CHOICE_SET_NAME:
                    cs_id = cs.get("Id") or cs.get("ID") or cs.get("id")
                    print(f"OK: choice set {CHOICE_SET_NAME} id={cs_id}")
                    return cs_id
            print(f"FAIL: choice set {CHOICE_SET_NAME} not found after seeding", file=sys.stderr)
            return None
        if attempt < LIST_RETRY_ATTEMPTS:
            print(f"WARN: choice-sets list attempt {attempt}/{LIST_RETRY_ATTEMPTS} failed; retrying in {LIST_RETRY_DELAY}s...", file=sys.stderr)
            time.sleep(LIST_RETRY_DELAY)
    print(f"FAIL: choice-sets list failed after {LIST_RETRY_ATTEMPTS} attempts: {err.strip()}", file=sys.stderr)
    return None


def entity_exists() -> str | None:
    """Return entity ID if CE_CodedOrder already exists, else None.

    Retries on transient failures from parallel pre_run races.
    """
    for attempt in range(1, LIST_RETRY_ATTEMPTS + 1):
        code, out, _ = run_uip("df", "entities", "list", "--include-folders")
        if code == 0:
            data = parse_json(out)
            raw = data.get("Data", [])
            entities = raw if isinstance(raw, list) else raw.get("Items", []) if isinstance(raw, dict) else []
            for e in entities:
                if e.get("Name") == ENTITY_NAME:
                    return e.get("Id") or e.get("ID") or e.get("id")
            return None  # list succeeded but entity not found
        if attempt < LIST_RETRY_ATTEMPTS:
            print(f"WARN: entities list attempt {attempt}/{LIST_RETRY_ATTEMPTS} failed; retrying in {LIST_RETRY_DELAY}s...", file=sys.stderr)
            time.sleep(LIST_RETRY_DELAY)
    return None


def create_entity(choice_set_id: str) -> str | None:
    """Create CE_CodedOrder with Status bound to the choice set."""
    schema = {
        "displayName": "Coded Order",
        "description": "Order entity for coded-agent Data Fabric evaluation",
        "fields": [
            {"fieldName": "OrderNumber", "type": "STRING", "isRequired": True, "lengthLimit": 50},
            {"fieldName": "CustomerName", "type": "STRING", "isRequired": True, "lengthLimit": 200},
            {"fieldName": "TotalAmount", "type": "DECIMAL", "decimalPrecision": 2, "minValue": 0, "maxValue": 1000000},
            {"fieldName": "Status", "type": "CHOICE_SET_SINGLE", "choiceSetId": choice_set_id},
        ],
    }
    body = json.dumps(schema)
    code, out, err = run_uip("df", "entities", "create", ENTITY_NAME, "--body", body,
                              timeout=180)
    if code != 0:
        # Check if it was created despite the error
        eid = entity_exists()
        if eid:
            print(f"OK: entity {ENTITY_NAME} exists after create (id={eid[:8]}...)")
            return eid
        print(f"FAIL: entities create failed: {err.strip()}", file=sys.stderr)
        return None
    data = parse_json(out)
    created = data.get("Data") or {}
    eid = created.get("Id") or created.get("ID") or created.get("id")
    if eid:
        print(f"OK: created entity {ENTITY_NAME} (id={eid[:8]}...)")
    return eid


def insert_records(entity_id: str) -> bool:
    """Insert seed records with Status as NumberId integers."""
    raw_records = json.loads(RECORDS_FILE.read_text())
    # Assign Status values round-robin from the map
    statuses = list(STATUS_MAP.keys())
    for i, rec in enumerate(raw_records):
        status_name = statuses[i % len(statuses)]
        rec["Status"] = STATUS_MAP[status_name]
    body = json.dumps(raw_records)
    code, out, err = run_uip("df", "records", "insert", entity_id, "--body", body)
    if code != 0:
        print(f"WARN: records insert failed: {err.strip()}", file=sys.stderr)
        return False
    data = parse_json(out)
    result = data.get("Result", "")
    if result == "Success":
        print(f"OK: inserted {len(raw_records)} records into {ENTITY_NAME}")
        return True
    print(f"WARN: records insert result={result}")
    return True  # non-fatal


def main() -> int:
    # Phase 1: seed choice set
    cs_id = seed_choice_set()
    if not cs_id:
        return 1

    # Phase 2: create entity (idempotent)
    eid = entity_exists()
    if eid:
        print(f"OK: entity {ENTITY_NAME} already exists (id={eid[:8]}...), skipping create")
    else:
        eid = create_entity(cs_id)
        if not eid:
            return 1
        # Phase 3: insert seed records (only on fresh entity)
        insert_records(eid)

    return 0


if __name__ == "__main__":
    sys.exit(main())
