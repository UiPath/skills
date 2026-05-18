#!/usr/bin/env python3
"""Verify asset share/unshare flow: folder count goes 1 → 2 → 1."""

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


def assert_ok(env: dict, label: str):
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    return env.get("Data")


def folder_count(env: dict, label: str) -> int:
    data = assert_ok(env, label)
    # Observed shape: {"accessibleFolders": [...], "totalFoldersCount": N}
    if isinstance(data, dict):
        if "totalFoldersCount" in data:
            return int(data["totalFoldersCount"])
        items = (
            data.get("accessibleFolders")
            or data.get("Value")
            or data.get("Items")
            or data.get("Results")
            or []
        )
        return len(items)
    if isinstance(data, list):
        return len(data)
    sys.exit(f"FAIL: {label} Data shape unexpected: {type(data).__name__}")


before = folder_count(load("folders_before_share.json"), "folders_before_share")
if before != 1:
    sys.exit(f"FAIL: pre-share folder count = {before}, expected 1")

after_share = folder_count(load("folders_after_share.json"), "folders_after_share")
if after_share != 2:
    sys.exit(f"FAIL: post-share folder count = {after_share}, expected 2")

after_unshare = folder_count(load("folders_after_unshare.json"), "folders_after_unshare")
if after_unshare != 1:
    sys.exit(f"FAIL: post-unshare folder count = {after_unshare}, expected 1")

print(f"OK: folder count round-trip 1 -> 2 -> 1 verified")
