#!/usr/bin/env python3
"""post_run: delete every tenant resource whose name contains seed.json's uuid8.

Best-effort, idempotent (NotFound = OK), exits 0 always. Per-task uuid8
makes this parallel-safe — siblings don't touch each other's resources.
"""
import json
import os
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


def items_of(env):
    data = env.get("Data") or []
    if isinstance(data, dict):
        return data.get("Value") or data.get("Items") or data.get("Results") or []
    return data


def has_uuid(item, uuid8):
    return uuid8 in (item.get("Name") or item.get("DisplayName") or item.get("DeploymentName") or "").lower()


if not os.path.exists("seed.json"):
    sys.exit(0)

try:
    uuid8 = json.load(open("seed.json")).get("uuid8", "").lower()
except Exception:
    sys.exit(0)

if not uuid8:
    sys.exit(0)


# 1) Tenant-scoped roles
for r in items_of(uip("or", "roles", "list")):
    if has_uuid(r, uuid8):
        key = r.get("Key") or r.get("Id")
        if key:
            uip("or", "roles", "delete", str(key))

# 2) Tenant-scoped webhooks
for w in items_of(uip("resource", "webhooks", "list")):
    if has_uuid(w, uuid8):
        key = w.get("Key") or w.get("Id")
        if key:
            uip("resource", "webhooks", "delete", str(key))

# 3) Solution deploys (uninstall by name; cascades to folder + processes)
for d in items_of(uip("solution", "deploy", "list")):
    name = d.get("Name") or d.get("DeploymentName") or ""
    if uuid8 in name.lower():
        uip("solution", "deploy", "uninstall", name)

# 4) Folders — delete recursively (cascades to child assets/queues/buckets/triggers)
for f in items_of(uip("or", "folders", "list", "--limit", "200")):
    name = f.get("Name") or f.get("DisplayName") or ""
    if uuid8 in name.lower():
        key = f.get("Key")
        if key:
            uip("or", "folders", "delete", str(key))

sys.exit(0)
