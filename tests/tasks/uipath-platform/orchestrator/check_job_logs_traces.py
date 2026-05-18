#!/usr/bin/env python3
"""Verify the agent reported a terminal job + non-empty logs + non-empty traces."""

import json
import sys
from pathlib import Path


p = Path("job_outcome.json")
if not p.is_file():
    sys.exit("FAIL: job_outcome.json not written")
try:
    o = json.loads(p.read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: job_outcome.json invalid JSON: {e}")

state = o.get("terminal_state")
if state not in ("Successful", "Faulted", "Stopped"):
    sys.exit(f"FAIL: terminal_state={state!r}, expected Successful/Faulted/Stopped")

log_count = o.get("log_count")
if not isinstance(log_count, int) or log_count < 1:
    sys.exit(f"FAIL: log_count={log_count!r}, expected positive int")

span_count = o.get("span_count")
if not isinstance(span_count, int) or span_count < 1:
    sys.exit(f"FAIL: span_count={span_count!r}, expected positive int")

print(f"OK: job {o.get('job_key')!r} terminal={state} logs={log_count} spans={span_count}")
