#!/usr/bin/env python3
"""Query tenant: queue with expected name exists in folder, contains 5 items (New)."""

import json
import subprocess
import sys
from pathlib import Path

EXPECTED_COUNT = 5


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

expected_name = f"e2e-queue-{uuid8}"

env = uip_json("resource", "queues", "list", "--folder-path", folder_path)
if env.get("Result") != "Success":
    sys.exit(f"FAIL: queues list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
match = next((q for q in items if _pick(q, "Name") == expected_name), None)
if not match:
    names = [_pick(q, "Name") for q in items]
    sys.exit(f"FAIL: no queue named {expected_name!r} in {folder_path!r}; saw {names}")

env2 = uip_json("resource", "queue-items", "list", "--folder-path", folder_path, "--queue-name", expected_name, "--status", "New")
if env2.get("Result") != "Success":
    sys.exit(f"FAIL: queue-items list Result={env2.get('Result')!r}")
qi = env2.get("Data") or []
if isinstance(qi, dict):
    qi = _pick(qi, "Value", "Items", "Results") or []
if len(qi) != EXPECTED_COUNT:
    sys.exit(f"FAIL: queue {expected_name!r} has {len(qi)} New items, expected {EXPECTED_COUNT}")

print(f"OK: queue {expected_name!r} exists in {folder_path} with {EXPECTED_COUNT} items in New state")
