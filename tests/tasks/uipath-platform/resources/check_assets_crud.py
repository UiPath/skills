#!/usr/bin/env python3
"""Verify asset CRUD via `assets list` (authoritative source for typed values).

`get-asset-value` 403s on non-robot accounts — use `assets list` instead, whose
Data[] entries inline `stringValue` / `intValue` / `boolValue` per item."""

import json
import sys
from pathlib import Path

EXPECTED = {
    "text": ("Text", "stringValue", "hello-world"),
    "int": ("Integer", "intValue", 42),
    "bool": ("Bool", "boolValue", True),
}
UPDATED_TEXT = "updated-hello"


def load(name: str) -> dict:
    p = Path(name)
    if not p.is_file():
        sys.exit(f"FAIL: {name} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {name} is not valid JSON: {e}")


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def ok(env, label):
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    return env.get("Data")


# 1. All three assets created — capture keys
keys_by_kind: dict[str, str] = {}
for kind in ("text", "int", "bool"):
    data = ok(load(f"create_{kind}.json"), f"create_{kind}") or {}
    key = _pick(data, "Key", "Id")
    if not key:
        sys.exit(f"FAIL: create_{kind}.json missing Data.Key/key")
    keys_by_kind[kind] = key


def items_from(env: dict) -> list[dict]:
    data = env.get("Data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return _pick(data, "Value", "Items", "Results") or []
    return []


def find_by_key(items: list[dict], key: str) -> dict:
    for it in items:
        if isinstance(it, dict) and (_pick(it, "Key", "Id") == key):
            return it
    return {}


# 2. Each value round-trips via list response
list_initial = items_from(load("list_after_create.json"))
for kind, (typ, val_field, expected) in EXPECTED.items():
    item = find_by_key(list_initial, keys_by_kind[kind])
    if not item:
        sys.exit(f"FAIL: {kind} asset {keys_by_kind[kind]} not in list_after_create")
    val_type = _pick(item, "ValueType")
    if val_type != typ:
        sys.exit(f"FAIL: {kind} ValueType={val_type!r}, expected {typ!r}")
    actual = _pick(item, val_field)
    if str(actual).lower() != str(expected).lower():
        sys.exit(f"FAIL: {kind} {val_field}={actual!r}, expected {expected!r}")

# 3. Update was reflected — text asset's stringValue should now match UPDATED_TEXT
list_after_update = items_from(load("list_after_update.json"))
text_after = find_by_key(list_after_update, keys_by_kind["text"])
if not text_after:
    sys.exit(f"FAIL: text asset missing from list_after_update")
new_val = _pick(text_after, "stringValue")
if new_val != UPDATED_TEXT:
    sys.exit(f"FAIL: text update not reflected; stringValue={new_val!r}, expected {UPDATED_TEXT!r}")

print(
    f"OK: 3 assets created, values round-tripped "
    f"(text=hello-world, int=42, bool=True); update reflected (text→{new_val!r})"
)
