#!/usr/bin/env python3
"""Assert report.json has outcome=success and span_count >= 1."""
import json
import sys
from pathlib import Path

report_path = Path("report.json")
if not report_path.is_file():
    sys.exit("FAIL: report.json not found")

try:
    r = json.loads(report_path.read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: report.json is not valid JSON: {e}")

if r.get("outcome") != "success":
    sys.exit(f"FAIL: outcome={r.get('outcome')!r}, error={r.get('error')!r}")

count = r.get("span_count", 0)
if not isinstance(count, int) or count < 1:
    sys.exit(f"FAIL: span_count={count!r} — expected >= 1")

print(f"OK: {count} spans returned for job {r.get('job_key')}")
