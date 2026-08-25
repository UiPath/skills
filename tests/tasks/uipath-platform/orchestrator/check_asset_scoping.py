#!/usr/bin/env python3
"""Query tenant: asset by name in folder A only, never in B."""

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


def list_asset_names(folder_path: str) -> list[str]:
    env = uip_json("or", "assets", "list", "--folder-path", folder_path)
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: assets list {folder_path!r}: {env.get('Result')!r}")
    items = env.get("Data") or []
    if isinstance(items, dict):
        items = _pick(items, "Value", "Items", "Results") or []
    return [_pick(a, "Name") for a in items if isinstance(a, dict)]


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
folder_a = seed.get("folder_a_path")
folder_b_file = Path("folder_b.txt")
if not folder_b_file.exists():
    sys.exit("FAIL: folder_b.txt not found — agent must create folder B and write its path")
folder_b = folder_b_file.read_text().strip()
if not (uuid8 and folder_a and folder_b):
    sys.exit("FAIL: seed.json or folder_b.txt missing required fields")

asset_name = f"e2e-asset-scoping-{uuid8}"

names_a = list_asset_names(folder_a)
names_b = list_asset_names(folder_b)

if asset_name not in names_a:
    sys.exit(f"FAIL: {asset_name!r} not in A list: {names_a}")
if asset_name in names_b:
    sys.exit(f"FAIL: {asset_name!r} leaked into B list — scoping broken")

print(f"OK: {asset_name!r} scoped to A only")
