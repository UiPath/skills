#!/usr/bin/env python3
"""Assert feedback round-trip: create → get returns same ID with IsPositive=True."""
import json
import sys
from pathlib import Path


def load(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        sys.exit(f"FAIL: {path} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


spans = load("spans.json")
if spans.get("Result") != "Success":
    sys.exit(f"FAIL: spans get Result={spans.get('Result')!r}")
if not spans.get("Data"):
    sys.exit("FAIL: spans.json has no spans — job produced no trace")

create = load("feedback_create.json")
if create.get("Result") != "Success":
    sys.exit(f"FAIL: feedback create Result={create.get('Result')!r}, Message={create.get('Message')!r}")
def get_id(data: dict) -> str | None:
    return data.get("Id") or data.get("id")

def get_is_positive(data: dict) -> bool | None:
    v = data.get("IsPositive")
    return v if v is not None else data.get("isPositive")

feedback_id = get_id(create.get("Data") or {})
if not feedback_id:
    sys.exit("FAIL: feedback_create.json has no Data.Id")

get_data = load("feedback_get.json")
if get_data.get("Result") != "Success":
    sys.exit(f"FAIL: feedback get Result={get_data.get('Result')!r}")
got_id = get_id(get_data.get("Data") or {})
if got_id != feedback_id:
    sys.exit(f"FAIL: ID mismatch — create={feedback_id!r}, get={got_id!r}")
if get_is_positive(get_data.get("Data") or {}) is not True:
    sys.exit(f"FAIL: IsPositive not True in feedback_get.json")

print(f"OK: round-trip verified (id={feedback_id}, IsPositive=True, spans={len(spans['Data'])})")
