#!/usr/bin/env python3
"""Query tenant: 3 typed assets exist in folder with the expected final values."""

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
folder_path = seed.get("folder_a_path")
if not (uuid8 and folder_path):
    sys.exit("FAIL: seed.json missing uuid8 or folder_a_path")

EXPECTED = {
    f"e2e-asset-{uuid8}-text": ("Text", "stringValue", "updated-hello"),
    f"e2e-asset-{uuid8}-int": ("Integer", "intValue", 42),
    f"e2e-asset-{uuid8}-bool": ("Bool", "boolValue", True),
}

env = uip_json("resource", "assets", "list", "--folder-path", folder_path)
if env.get("Result") != "Success":
    sys.exit(f"FAIL: assets list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []

by_name = {_pick(a, "Name"): a for a in items if isinstance(a, dict)}

for name, (typ, field, expected) in EXPECTED.items():
    asset = by_name.get(name)
    if not asset:
        sys.exit(f"FAIL: asset {name!r} not in folder {folder_path!r}; saw {list(by_name)}")
    val_type = _pick(asset, "ValueType")
    if val_type != typ:
        sys.exit(f"FAIL: {name} ValueType={val_type!r}, expected {typ!r}")
    actual = _pick(asset, field)
    if str(actual).lower() != str(expected).lower():
        sys.exit(f"FAIL: {name} {field}={actual!r}, expected {expected!r}")

print(f"OK: 3 assets exist in {folder_path} with expected final values")
