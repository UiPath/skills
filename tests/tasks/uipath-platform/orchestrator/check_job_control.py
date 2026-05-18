#!/usr/bin/env python3
"""Verify state-transition observations from job_control.json."""

import json
import sys
from pathlib import Path


p = Path("job_control.json")
if not p.is_file():
    sys.exit("FAIL: job_control.json not written")
try:
    o = json.loads(p.read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: job_control.json invalid JSON: {e}")

state_stop = o.get("state_after_stop") or ""
if state_stop not in ("Stopping", "Stopped", "Faulted", "Killed"):
    sys.exit(f"FAIL: state_after_stop={state_stop!r}, expected Stopping/Stopped/Faulted/Killed")

term = o.get("restart_terminal") or ""
if term not in ("Successful", "Faulted", "Stopped"):
    sys.exit(f"FAIL: restart_terminal={term!r}, expected terminal state")

first = o.get("first_job_key")
restart = o.get("restart_job_key")
if not first or not restart:
    sys.exit(f"FAIL: missing job keys — first={first!r} restart={restart!r}")

print(f"OK: stop reached {state_stop!r}, restart reached {term!r}")
