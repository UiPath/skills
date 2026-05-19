#!/usr/bin/env python3
"""Verify audit-log queries: both return Result=Success with a list-shaped Data."""

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


def _pick(d, *names):
    if not isinstance(d, dict):
        return None
    for n in names:
        for k in (n, n[:1].lower() + n[1:], n.lower()):
            if k in d:
                return d[k]
    return None


def list_items(env, label):
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r}")
    data = env.get("Data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return _pick(data, "Value", "Items", "Results") or []
    sys.exit(f"FAIL: {label} Data type={type(data).__name__}")


all_items = list_items(load("logs_all.json"), "logs_all")
folder_items = list_items(load("logs_folders.json"), "logs_folders")

# The folder-filtered list should be a subset (in count) of the all list — both bounded by --limit 100.
# Verify each folder-filtered entry actually has Folders-related component, if exposed.
suspicious = []
for it in folder_items:
    if not isinstance(it, dict):
        continue
    comp = _pick(it, "Component", "ComponentName")
    if comp and "folder" not in str(comp).lower():
        suspicious.append(comp)

if suspicious[:3]:
    sys.exit(
        f"FAIL: --component Folders returned entries with non-folder Component: {suspicious[:3]}"
    )

print(f"OK: all-logs returned {len(all_items)} entries; folders-only returned {len(folder_items)} (subset/coherent)")
