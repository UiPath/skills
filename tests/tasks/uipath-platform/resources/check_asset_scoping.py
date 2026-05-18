#!/usr/bin/env python3
"""Verify asset folder scoping: created-in-A asset is in list_in_a, absent from list_in_b."""

import json
import sys
from pathlib import Path


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


create = load("create.json")
if create.get("Result") != "Success":
    sys.exit(f"FAIL: create Result={create.get('Result')!r}")
asset_key = _pick(create.get("Data") or {}, "Key", "Id")
if not asset_key:
    sys.exit("FAIL: create.json has no Data.Key/key")


def list_keys(env: dict, label: str) -> list[str]:
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r}")
    data = env.get("Data")
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = _pick(data, "Value", "Items", "Results") or []
    else:
        items = []
    return [_pick(it, "Key", "Id") for it in items if isinstance(it, dict)]


in_a = list_keys(load("list_in_a.json"), "list_in_a")
in_b = list_keys(load("list_in_b.json"), "list_in_b")

if asset_key not in in_a:
    sys.exit(f"FAIL: asset {asset_key} not in folder A list; got {len(in_a)} keys")
if asset_key in in_b:
    sys.exit(f"FAIL: asset {asset_key} leaked into folder B list — folder scoping broken")

print(f"OK: asset {asset_key} visible in A ({len(in_a)} total), absent from B ({len(in_b)} total)")
