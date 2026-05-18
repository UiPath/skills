#!/usr/bin/env python3
"""Query tenant state to verify an API trigger exists with the expected fields."""

import json
import subprocess
import sys
from pathlib import Path


def load_seed() -> dict:
    p = Path("seed.json")
    if not p.is_file():
        sys.exit("FAIL: seed.json not found")
    return json.loads(p.read_text())


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def uip_json(*args: str, timeout: int = 60) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    if not r.stdout.strip():
        sys.exit(f"FAIL: uip {' '.join(args)} returned no stdout (stderr={r.stderr[:200]})")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: uip {' '.join(args)} non-JSON: {e}: {r.stdout[:200]}")


seed = load_seed()
uuid8 = seed.get("uuid8")
folder_path = seed.get("folder_path")
if not uuid8 or not folder_path:
    sys.exit(f"FAIL: seed.json missing uuid8 or folder_path")

expected_name = f"e2e-trigger-api-{uuid8}-renamed"
expected_slug = f"e2e-trigger-api-{uuid8}-slug"

envelope = uip_json("resource", "triggers", "list", "--type", "api", "--folder-path", folder_path)
if envelope.get("Result") != "Success":
    sys.exit(f"FAIL: triggers list Result={envelope.get('Result')!r}")
items = envelope.get("Data")
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
items = items or []

match = next((t for t in items if _pick(t, "Name") == expected_name), None)
if not match:
    names = [_pick(t, "Name") for t in items]
    sys.exit(f"FAIL: no trigger named {expected_name!r} in {folder_path!r}; saw {names}")

slug = _pick(match, "Slug")
method = _pick(match, "Method")
if slug != expected_slug:
    sys.exit(f"FAIL: trigger slug={slug!r}, expected {expected_slug!r}")
if str(method).lower() != "post":
    sys.exit(f"FAIL: trigger method={method!r}, expected 'Post'")

print(f"OK: API trigger {expected_name!r} exists with slug={slug!r}, method={method!r}")
