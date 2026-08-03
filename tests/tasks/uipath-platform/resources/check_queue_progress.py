#!/usr/bin/env python3
"""Query tenant state: the queue holds a single item that has been triaged
(High priority + specific content status=triaged).

The New -> InProgress -> Successful/Failed transitions are driven by a robot
dequeuing the item (Orchestrator's StartTransaction), which has no management
CLI surface, so this verifies the metadata lifecycle the CLI/skill actually
exposes: create queue, add item, reprioritize, edit content."""

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
        sys.exit(f"FAIL: uip {' '.join(args)} returned no stdout (stderr={r.stderr[:200]})")
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: uip {' '.join(args)} non-JSON: {e}: {r.stdout[:200]}")


def as_list(env: dict, label: str) -> list:
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    data = env.get("Data")
    if isinstance(data, dict):
        data = _pick(data, "Value", "Items", "Results") or []
    return data or []


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
folder = seed.get("folder_a_path") or seed.get("folder_path")
if not uuid8 or not folder:
    sys.exit("FAIL: seed.json missing uuid8 or folder_a_path")
queue_name = f"e2e-q-{uuid8}"

items = as_list(
    uip_json("or", "queue-items", "list", "--queue-name", queue_name, "--folder-path", folder),
    "queue-items list",
)
if not items:
    sys.exit(f"FAIL: no items in queue {queue_name!r} in {folder!r}")

# `list` is curated and omits SpecificContent — read the full item via `get`.
item_key = _pick(items[0], "Key", "UniqueKey", "Id")
env = uip_json("or", "queue-items", "get", str(item_key), "--folder-path", folder)
if env.get("Result") != "Success":
    sys.exit(f"FAIL: queue-items get Result={env.get('Result')!r} Message={env.get('Message')!r}")
item = env.get("Data") or {}

priority = _pick(item, "Priority")
if priority != "High":
    sys.exit(f"FAIL: item priority={priority!r}, expected 'High'")

content = _pick(item, "SpecificContent") or {}
# Orchestrator normalizes content keys, so match case-insensitively.
lc = {str(k).lower(): v for k, v in content.items()} if isinstance(content, dict) else {}
if str(lc.get("status")).lower() != "triaged":
    sys.exit(f"FAIL: item specific content status={lc.get('status')!r}, expected 'triaged' (content={content})")

print(f"OK: queue {queue_name!r} has a High-priority item with status=triaged")
