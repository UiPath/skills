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
    seed = json.load(open("seed.json"))
    uuid8 = seed.get("uuid8", "").lower()
except Exception:
    sys.exit(0)

if not uuid8:
    sys.exit(0)

# 0) Folder-scoped debris in the seeded folder. Tasks create uuid-tagged
# assets/queues/buckets/triggers inside the pre-existing folder_a_path
# (usually 'Shared'); the folder itself is never deleted, so without this
# step they pile up across runs.
folder = seed.get("folder_a_path") or seed.get("folder_path") or ""
if folder:
    for a in items_of(uip("or", "assets", "list", "--folder-path", folder)):
        if has_uuid(a, uuid8) and a.get("Key"):
            uip("or", "assets", "delete", str(a["Key"]), "--yes")
    for q in items_of(uip("or", "queues", "list", "--folder-path", folder)):
        if has_uuid(q, uuid8) and q.get("Key"):
            uip("or", "queues", "delete", str(q["Key"]), "--yes", "--force")
    for b in items_of(uip("or", "buckets", "list", "--folder-path", folder)):
        if has_uuid(b, uuid8) and (b.get("Identifier") or b.get("Key")):
            uip("or", "buckets", "delete", str(b.get("Identifier") or b["Key"]),
                "--folder-path", folder, "--yes", "--force")
    for tr in items_of(uip("or", "triggers", "list", "--folder-path", folder)):
        if has_uuid(tr, uuid8) and tr.get("Key"):
            uip("or", "triggers", "delete", str(tr["Key"]),
                "--folder-path", folder, "--yes")


# 1) Tenant-scoped roles
for r in items_of(uip("or", "roles", "list")):
    if has_uuid(r, uuid8):
        key = r.get("Key") or r.get("Id")
        if key:
            uip("or", "roles", "delete", str(key), "--yes")

# 2) Tenant-scoped webhooks
for w in items_of(uip("or", "webhooks", "list")):
    if has_uuid(w, uuid8):
        key = w.get("Key") or w.get("Id")
        if key:
            uip("or", "webhooks", "delete", str(key), "--yes")

# 3) Solution deploys (uninstall by name; cascades to folder + processes)
for d in items_of(uip("solution", "deploy", "list")):
    name = d.get("Name") or d.get("DeploymentName") or ""
    if uuid8 in name.lower():
        uip("solution", "deploy", "uninstall", name, "--yes")

# 4) Folders — delete recursively (cascades to child assets/queues/buckets/triggers)
for f in items_of(uip("or", "folders", "list", "--limit", "200")):
    name = f.get("Name") or f.get("DisplayName") or ""
    if uuid8 in name.lower():
        key = f.get("Key")
        if key:
            uip("or", "folders", "delete", str(key), "--yes")

sys.exit(0)
