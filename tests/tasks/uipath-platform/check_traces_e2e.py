#!/usr/bin/env python3
"""Assert spans.json (raw uip traces spans get output) has Data with >= 1 span."""
import json
import sys
from pathlib import Path

spans_path = Path("spans.json")
if not spans_path.is_file():
    sys.exit("FAIL: spans.json not found")

try:
    data = json.loads(spans_path.read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: spans.json is not valid JSON: {e}")

if data.get("Result") != "Success":
    sys.exit(f"FAIL: Result={data.get('Result')!r}, Message={data.get('Message')!r}")

spans = data.get("Data", [])
if not isinstance(spans, list) or len(spans) < 1:
    sys.exit(f"FAIL: span_count={len(spans)} — expected >= 1")

print(f"OK: {len(spans)} span(s) returned")
