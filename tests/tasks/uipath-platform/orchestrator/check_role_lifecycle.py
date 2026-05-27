#!/usr/bin/env python3
"""Query tenant: role exists; permission from permission.txt is granted."""

import json
import subprocess
import sys
from pathlib import Path


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def uip_json(*args: str) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        sys.exit(f"FAIL: uip {' '.join(args)} no stdout")
    return json.loads(r.stdout)


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json has no uuid8")
expected_name = f"e2e-role-{uuid8}"

p = Path("permission.txt")
if not p.is_file():
    sys.exit("FAIL: permission.txt not written")
chosen_perm = p.read_text().strip()
if not chosen_perm:
    sys.exit("FAIL: permission.txt empty")

env = uip_json("or", "roles", "list")
if env.get("Result") != "Success":
    sys.exit(f"FAIL: roles list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
match = next((r for r in items if _pick(r, "Name") == expected_name), None)
if not match:
    sys.exit(f"FAIL: role {expected_name!r} not in roles list")
role_key = _pick(match, "Key", "Id")

g = uip_json("or", "roles", "get", str(role_key))
if g.get("Result") != "Success":
    sys.exit(f"FAIL: roles get Result={g.get('Result')!r}")
data = g.get("Data") or {}
raw = _pick(data, "Permissions", "RolePermissions")
perms: list[str] = []
if isinstance(raw, str):
    perms = [s.strip() for s in raw.split(",") if s.strip()]
elif isinstance(raw, list):
    perms = [p if isinstance(p, str) else (_pick(p, "Name") or "") for p in raw]
if chosen_perm not in perms:
    sys.exit(f"FAIL: role {expected_name!r} permissions = {perms}; expected to include {chosen_perm!r}")

print(f"OK: role {expected_name!r} exists; permission {chosen_perm!r} granted")
