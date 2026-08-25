#!/usr/bin/env python3
"""Check config_final.json: chosen resource's description is e2e-test-edit."""

import json
import sys
from pathlib import Path


name_file = Path("resource_name.txt")
if not name_file.is_file():
    sys.exit("FAIL: resource_name.txt not written")
resource_name = name_file.read_text().strip()
if not resource_name:
    sys.exit("FAIL: resource_name.txt empty")

p = Path("config_final.json")
if not p.is_file():
    sys.exit("FAIL: config_final.json not written")
try:
    cfg = json.loads(p.read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: config_final.json invalid JSON: {e}")

resources = cfg.get("resources") or []
match = next((r for r in resources if r.get("name") == resource_name), None)
if not match:
    sys.exit(f"FAIL: resource {resource_name!r} not in config_final.json — saw {[r.get('name') for r in resources]}")

actual = (match.get("configuration") or {}).get("description")
if actual != "e2e-test-edit":
    sys.exit(f"FAIL: description = {actual!r}, expected 'e2e-test-edit'")

print(f"OK: {resource_name}.configuration.description == {actual!r}")
