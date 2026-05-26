#!/usr/bin/env python3
"""Query tenant: 2 jobs on the seeded process; first stop-related, second terminal."""

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


p = Path("job_keys.txt")
if not p.is_file():
    sys.exit("FAIL: job_keys.txt not written")
keys = [line.strip() for line in p.read_text().splitlines() if line.strip()]
if len(keys) != 2:
    sys.exit(f"FAIL: expected 2 job keys in job_keys.txt, got {len(keys)}")


def fetch_state(key: str) -> str:
    env = uip_json("or", "jobs", "get", key)
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: jobs get {key!r} Result={env.get('Result')!r}")
    return _pick(env.get("Data") or {}, "State")


first_state = fetch_state(keys[0])
second_state = fetch_state(keys[1])

STOP_RELATED = {"Stopping", "Stopped", "Faulted", "Killed"}
TERMINAL = {"Successful", "Faulted", "Stopped"}

if first_state not in STOP_RELATED:
    sys.exit(f"FAIL: first job state={first_state!r}, expected one of {STOP_RELATED}")
if second_state not in TERMINAL:
    sys.exit(f"FAIL: second job state={second_state!r}, expected one of {TERMINAL}")

print(f"OK: first job → {first_state!r} (stop-related); second job → {second_state!r} (terminal)")
