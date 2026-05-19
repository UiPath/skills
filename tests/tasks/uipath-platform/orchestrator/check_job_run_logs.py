#!/usr/bin/env python3
"""Query tenant: job reached terminal state + has at least one log entry.

Reads only the job key from `job_key.txt`; everything else queried live."""

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


def uip_json(*args: str, timeout: int = 60) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    if not r.stdout.strip():
        sys.exit(f"FAIL: uip {' '.join(args)} no stdout: {r.stderr[:200]}")
    return json.loads(r.stdout)


p = Path("job_key.txt")
if not p.is_file():
    sys.exit("FAIL: job_key.txt not written by agent")
job_key = p.read_text().strip()
if not job_key:
    sys.exit("FAIL: job_key.txt empty")

# 1. Job is terminal
env = uip_json("or", "jobs", "get", job_key)
if env.get("Result") != "Success":
    sys.exit(f"FAIL: jobs get Result={env.get('Result')!r} Message={env.get('Message')!r}")
state = _pick(env.get("Data") or {}, "State")
if state not in ("Successful", "Faulted", "Stopped"):
    sys.exit(f"FAIL: job state={state!r}, expected Successful/Faulted/Stopped")

# 2. Logs non-empty
logs = uip_json("or", "jobs", "logs", job_key)
if logs.get("Result") != "Success":
    sys.exit(f"FAIL: jobs logs Result={logs.get('Result')!r}")
log_data = logs.get("Data") or []
if isinstance(log_data, dict):
    log_data = _pick(log_data, "Value", "Items", "Results") or []
if not log_data:
    sys.exit("FAIL: jobs logs returned empty")

print(f"OK: job {job_key} state={state} logs={len(log_data)}")
