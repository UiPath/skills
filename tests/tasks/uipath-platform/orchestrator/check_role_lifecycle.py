#!/usr/bin/env python3
"""Verify role lifecycle: permission absent → present after add → absent after remove."""

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


perm_file = Path("perm.txt")
if not perm_file.is_file():
    sys.exit("FAIL: perm.txt not written")
perm = perm_file.read_text().strip()
if not perm:
    sys.exit("FAIL: perm.txt is empty")


def role_perms(env, label) -> list[str]:
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r}")
    data = env.get("Data") or {}
    raw = _pick(data, "Permissions", "RolePermissions", "PermissionsArray")
    # Observed shape: Permissions is a comma-separated string (e.g. "AgentMemory,Triggers.View").
    # Could also be a list[str] or list[{Name: str}] depending on the API surface.
    if isinstance(raw, str):
        return [p.strip() for p in raw.split(",") if p.strip()]
    if isinstance(raw, list):
        names = []
        for p in raw:
            if isinstance(p, str):
                names.append(p)
            elif isinstance(p, dict):
                n = _pick(p, "Name")
                if n:
                    names.append(n)
        return names
    return []


before = role_perms(load("get_before.json"), "get_before")
after_add = role_perms(load("get_after_add.json"), "get_after_add")
after_rm = role_perms(load("get_after_remove.json"), "get_after_remove")

if perm in before:
    sys.exit(f"FAIL: permission {perm!r} already present pre-add: {before[:5]}")
if perm not in after_add:
    sys.exit(f"FAIL: permission {perm!r} not in role post-add: {after_add[:10]}")
if perm in after_rm:
    sys.exit(f"FAIL: permission {perm!r} still present after remove: {after_rm[:10]}")

print(f"OK: permission {perm!r} cycle absent -> present -> absent verified")
