#!/usr/bin/env python3
"""post_run: best-effort sweep of BYOG configurations created by this task.

Deletes every BYO guardrail configuration whose ValidatorName contains the
marker. Exits 0 always — feature flag off, auth failure, and nothing-to-delete
are all fine. Mirrors tests/tasks/uipath-platform/cleanup.py's posture.
"""
import argparse
import json
import subprocess
import sys


def uip(*args):
    r = subprocess.run(
        ["uip", *args, "--output", "json"],
        capture_output=True, text=True, timeout=120,
    )
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


parser = argparse.ArgumentParser()
parser.add_argument("--marker", required=True)
marker = parser.parse_args().marker.lower()

env = uip("guardrails", "byo-configurations", "list")
data = env.get("Data") or []
if isinstance(data, list):
    for c in data:
        name = (c.get("ValidatorName") or "").lower()
        if marker in name and c.get("Id"):
            uip("guardrails", "byo-configurations", "delete", str(c["Id"]), "--force")

sys.exit(0)
