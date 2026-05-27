#!/usr/bin/env python3
"""Webhook with secret + Job.Completed subscription exists; ping delivered."""

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
expected_name = f"e2e-webhook-signed-{uuid8}"

secret_file = Path("secret.txt")
if not secret_file.is_file():
    sys.exit("FAIL: secret.txt not written by agent")
secret = secret_file.read_text().strip()
if not secret:
    sys.exit("FAIL: secret.txt empty")

# 1) Webhook present with right config
env = uip_json("resource", "webhooks", "list")
if env.get("Result") != "Success":
    sys.exit(f"FAIL: webhooks list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
match = next((w for w in items if _pick(w, "Name") == expected_name), None)
if not match:
    sys.exit(f"FAIL: webhook {expected_name!r} not on tenant")

if _pick(match, "Enabled") is False:
    sys.exit(f"FAIL: webhook {expected_name!r} is not Enabled")

# Note: tenant API masks Secret in list responses for security — we trust the
# agent recorded the secret it used and rely on `webhooks ping` succeeding as
# delivery proof.

events_raw = _pick(match, "Events", "SubscribeToAllEvents") or []
event_names = []
if isinstance(events_raw, list):
    event_names = [e if isinstance(e, str) else (_pick(e, "EventType", "Name") or "") for e in events_raw]
elif isinstance(events_raw, str):
    event_names = [s.strip() for s in events_raw.split(",") if s.strip()]
if not any("job.completed" in n.lower() for n in event_names):
    sys.exit(f"FAIL: webhook events do not include Job.Completed; saw {event_names}")

# 2) Ping envelope captured + Success
ping_file = Path("ping.json")
if not ping_file.is_file():
    sys.exit("FAIL: ping.json not written by agent")
try:
    ping = json.loads(ping_file.read_text())
except json.JSONDecodeError as e:
    sys.exit(f"FAIL: ping.json not valid JSON: {e}")
if ping.get("Result") != "Success":
    sys.exit(f"FAIL: ping.json Result={ping.get('Result')!r} Message={ping.get('Message')!r}")

print(f"OK: webhook {expected_name!r} configured; ping delivered")
