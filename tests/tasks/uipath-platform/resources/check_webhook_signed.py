#!/usr/bin/env python3
"""Webhook exists on tenant + agent verified the inbound signature."""

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

# State: webhook exists
env = uip_json("resource", "webhooks", "list")
if env.get("Result") != "Success":
    sys.exit(f"FAIL: webhooks list Result={env.get('Result')!r}")
items = env.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
if not any(_pick(w, "Name") == expected_name for w in items):
    sys.exit(f"FAIL: webhook {expected_name!r} not found on tenant")

# Behavioral artifact: signature verified
p = Path("signature_verified.txt")
if not p.is_file():
    sys.exit("FAIL: signature_verified.txt not written")
verdict = p.read_text().strip().lower()
if verdict not in ("true", "1", "yes", "ok"):
    sys.exit(f"FAIL: signature verification reported {verdict!r}, expected truthy")

print(f"OK: webhook {expected_name!r} exists; signature verified={verdict!r}")
