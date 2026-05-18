#!/usr/bin/env python3
"""Query tenant state to verify the trigger lifecycle outcome.

We don't read any sandbox-emitted files — the agent's CLI choices are
irrelevant. We query `triggers list` in the seeded folder, find the one with
the expected name pattern, and assert its cron + enabled flag."""

import json
import subprocess
import sys
from pathlib import Path

EXPECTED_CRON = "0 30 4 * * ?"


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
    sys.exit(f"FAIL: seed.json missing uuid8 or folder_path: {seed}")

expected_name = f"e2e-trigger-time-{uuid8}"

envelope = uip_json("resource", "triggers", "list", "--type", "time", "--folder-path", folder_path)
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

enabled = _pick(match, "Enabled")
cron = _pick(match, "StartProcessCron", "Cron", "CronExpression")
release_key = _pick(match, "ReleaseKey")

if enabled is not True:
    sys.exit(f"FAIL: trigger {expected_name!r} Enabled={enabled!r}, expected True")
if cron != EXPECTED_CRON:
    sys.exit(f"FAIL: trigger {expected_name!r} cron={cron!r}, expected {EXPECTED_CRON!r}")
if release_key and release_key.lower() != seed.get("process_key", "").lower():
    sys.exit(f"FAIL: trigger release_key={release_key!r}, expected {seed.get('process_key')!r}")

print(f"OK: trigger {expected_name!r} exists in {folder_path}, enabled=True, cron={cron!r}")
