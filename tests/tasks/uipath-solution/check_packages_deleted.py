#!/usr/bin/env python3
"""Query the feed: the local package was downloaded AND no published package
carries this run's uuid8 anymore (i.e. `solution packages delete` succeeded)."""

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
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        sys.exit(f"FAIL: uip {' '.join(args)} non-JSON stdout")


seed = json.loads(Path("seed.json").read_text())
uuid8 = (seed.get("uuid8") or "").lower()
if not uuid8:
    sys.exit("FAIL: seed.json missing uuid8")

# Download step: the local artifact must exist.
if not Path("downloaded.zip").is_file():
    sys.exit("FAIL: downloaded.zip not present — packages download did not produce the file")

# Delete step: no package in the feed should carry this run's uuid8.
pl = uip_json("solution", "packages", "list")
if pl.get("Result") != "Success":
    sys.exit(f"FAIL: packages list Result={pl.get('Result')!r}")
items = pl.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
leftover = [
    (_pick(d, "Name") or _pick(d, "Id") or "")
    for d in items
    if isinstance(d, dict) and uuid8 in str(_pick(d, "Name") or _pick(d, "Id") or "").lower()
]
if leftover:
    sys.exit(f"FAIL: package(s) with uuid8 still in feed after delete: {leftover[:5]}")

print("OK: downloaded.zip present and no uuid8 package remains in the feed (delete succeeded)")
