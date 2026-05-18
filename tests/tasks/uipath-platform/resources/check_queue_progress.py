#!/usr/bin/env python3
"""Verify queue-item state machine: New → InProgress, progress text updated."""

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


def get_data(env: dict, label: str) -> dict:
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    data = env.get("Data") or {}
    if not isinstance(data, dict):
        sys.exit(f"FAIL: {label} Data is {type(data).__name__}, expected dict")
    return data


new = get_data(load("get_new.json"), "get_new")
status_new = _pick(new, "Status")
if status_new != "New":
    sys.exit(f"FAIL: initial status = {status_new!r}, expected 'New'")

after = get_data(load("get_after_progress.json"), "get_after_progress")
status_after = _pick(after, "Status")
progress_after = _pick(after, "Progress")
if status_after != "InProgress":
    sys.exit(f"FAIL: post set-progress status = {status_after!r}, expected 'InProgress'")
if progress_after != "starting":
    sys.exit(f"FAIL: post set-progress text = {progress_after!r}, expected 'starting'")

after_update = get_data(load("get_after_update.json"), "get_after_update")
status_final = _pick(after_update, "Status")
progress_final = _pick(after_update, "Progress")
if status_final != "InProgress":
    sys.exit(f"FAIL: post-update status = {status_final!r}, expected 'InProgress'")
if progress_final != "halfway":
    sys.exit(f"FAIL: post-update progress = {progress_final!r}, expected 'halfway'")

print(f"OK: state machine New -> InProgress verified; progress updated 'starting' -> 'halfway'")
