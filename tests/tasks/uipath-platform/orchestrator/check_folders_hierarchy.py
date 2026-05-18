#!/usr/bin/env python3
"""Verify folder hierarchy: ParentKey chain pre-move, then ParentKey updated post-move."""

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


def data(env, label):
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r}")
    return env.get("Data") or {}


top = data(load("get_top.json"), "get_top")
a = data(load("get_a.json"), "get_a")
b = data(load("get_b.json"), "get_b")
b_after = data(load("get_b_after_move.json"), "get_b_after_move")

# Folder envelope uses numeric ID + ParentID (not Key + ParentKey). Compare by ID.
top_id = _pick(top, "ID", "Id")
a_id = _pick(a, "ID", "Id")
b_id = _pick(b, "ID", "Id")
if not (top_id and a_id and b_id):
    sys.exit(f"FAIL: missing IDs — top={top_id} a={a_id} b={b_id}")

a_parent = _pick(a, "ParentID", "ParentId")
b_parent_before = _pick(b, "ParentID", "ParentId")
b_parent_after = _pick(b_after, "ParentID", "ParentId")

if a_parent != top_id:
    sys.exit(f"FAIL: A.ParentID={a_parent!r} expected top.ID={top_id!r}")
if b_parent_before != a_id:
    sys.exit(f"FAIL: B.ParentID (pre-move)={b_parent_before!r} expected a.ID={a_id!r}")
if b_parent_after != top_id:
    sys.exit(f"FAIL: B.ParentID (post-move)={b_parent_after!r} expected top.ID={top_id!r}")

print(f"OK: chain top({top_id})->A({a_id})->B({b_id}) verified; B moved to sibling of A (ParentID now {top_id})")
