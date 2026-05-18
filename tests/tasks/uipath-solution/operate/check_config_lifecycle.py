#!/usr/bin/env python3
"""Verify the solution config edit: the picked resource's description == 'e2e-test-edit'."""

import json
import sys
from pathlib import Path


def load(name: str) -> dict:
    p = Path(name)
    if not p.is_file():
        sys.exit(f"FAIL: {name} not found")
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {name} is not valid JSON: {e}")


name_file = Path("resource_name.txt")
if not name_file.is_file():
    sys.exit("FAIL: resource_name.txt not written")
resource_name = name_file.read_text().strip()
if not resource_name:
    sys.exit("FAIL: resource_name.txt empty")

cfg = load("config_initial.json")
resources = cfg.get("resources") or []
match = next((r for r in resources if r.get("name") == resource_name), None)
if not match:
    sys.exit(f"FAIL: resource {resource_name!r} not in config_initial.json — saw {[r.get('name') for r in resources]}")

actual = (match.get("configuration") or {}).get("description")
if actual != "e2e-test-edit":
    sys.exit(f"FAIL: description = {actual!r}, expected 'e2e-test-edit'")

print(f"OK: config edit reflected — {resource_name}.configuration.description == 'e2e-test-edit'")
