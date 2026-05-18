#!/usr/bin/env python3
"""Query tenant: webhook by expected name exists, has subscribed events, is disabled."""

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


def uip_json(*args: str) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        sys.exit(f"FAIL: uip {' '.join(args)} no stdout")
    return json.loads(r.stdout)


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json has no uuid8")

expected_name = f"e2e-webhook-{uuid8}"

env = uip_json("resource", "webhooks", "list")
if env.get("Result") != "Success":
    sys.exit(f"FAIL: webhooks list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []

match = next((w for w in items if _pick(w, "Name") == expected_name), None)
if not match:
    names = [_pick(w, "Name") for w in items]
    sys.exit(f"FAIL: webhook {expected_name!r} not found; saw {names}")

# `webhooks list` only exposes Key/Name/Url/Enabled — Events requires `get`.
webhook_key = _pick(match, "Key", "Id")
get_env = uip_json("resource", "webhooks", "get", str(webhook_key))
if get_env.get("Result") != "Success":
    sys.exit(f"FAIL: webhooks get {webhook_key!r} Result={get_env.get('Result')!r}")
detail = get_env.get("Data") or {}
enabled = _pick(detail, "Enabled")
events = _pick(detail, "Events", "EventTypes")
event_names: list[str] = []
if isinstance(events, list):
    for e in events:
        event_names.append(e if isinstance(e, str) else (_pick(e, "Name", "EventType") or ""))
elif isinstance(events, str):
    event_names = [s.strip() for s in events.split(",") if s.strip()]

if not event_names:
    sys.exit(f"FAIL: webhook {expected_name!r} has no Events; saw {events!r}")
if enabled is not False:
    sys.exit(f"FAIL: webhook {expected_name!r} Enabled={enabled!r}, expected False")

print(f"OK: webhook {expected_name!r} subscribes to {event_names}, Enabled=False")
