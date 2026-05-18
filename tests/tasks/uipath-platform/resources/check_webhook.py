#!/usr/bin/env python3
"""Verify webhook lifecycle: events non-empty, subset matches, ping ok, disable reflected."""

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


def ok(env: dict, label: str):
    if env.get("Result") != "Success":
        sys.exit(f"FAIL: {label} Result={env.get('Result')!r} Message={env.get('Message')!r}")
    return env.get("Data")


# 1. Event types non-empty
et = ok(load("event_types.json"), "event_types")
items = et if isinstance(et, list) else (_pick(et or {}, "Value", "Items") or [])
if not items:
    sys.exit(f"FAIL: event_types Data empty")

# 2. After-create Events matches chosen subset
chosen_file = Path("chosen_events.txt")
if not chosen_file.is_file():
    sys.exit(f"FAIL: chosen_events.txt not written")
chosen = [e.strip() for e in chosen_file.read_text().strip().split(",") if e.strip()]
if not chosen:
    sys.exit(f"FAIL: chosen_events.txt is empty")

after = ok(load("get_after_create.json"), "get_after_create") or {}
events = _pick(after, "Events", "EventTypes")
if events is None:
    sys.exit(f"FAIL: get_after_create has no Events field; keys={list(after.keys()) if isinstance(after, dict) else 'not dict'}")
# Events may be list of strings or list of objects with Name
event_names = []
if isinstance(events, list):
    for e in events:
        event_names.append(e if isinstance(e, str) else (_pick(e, "Name", "EventType") or ""))
elif isinstance(events, str):
    event_names = [s.strip() for s in events.split(",") if s.strip()]
missing = [e for e in chosen if e not in event_names]
if missing:
    sys.exit(f"FAIL: chosen events {chosen} not all in subscription Events {event_names} — missing {missing}")

# 3. Ping returned Success
ping = load("ping.json")
if ping.get("Result") != "Success":
    sys.exit(f"FAIL: ping Result={ping.get('Result')!r} Message={ping.get('Message')!r}")

# 4. Disable reflected
disabled = ok(load("get_after_disable.json"), "get_after_disable") or {}
enabled = _pick(disabled, "Enabled")
if enabled is not False:
    sys.exit(f"FAIL: post-disable Enabled = {enabled!r}, expected False")

print(f"OK: {len(items)} event types listed, subset {chosen} subscribed, ping Success, disabled flag flipped")
