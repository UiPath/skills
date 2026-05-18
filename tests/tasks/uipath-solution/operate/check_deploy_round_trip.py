#!/usr/bin/env python3
"""Query tenant: deploy with expected name is in list; folder + process exist."""

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
    sys.exit("FAIL: seed.json missing uuid8")

deploy_name = f"e2e-deploy-{uuid8}"
folder_name = f"e2e-deploy-folder-{uuid8}"

# Deploy in list
dl = uip_json("solution", "deploy", "list")
if dl.get("Result") != "Success":
    sys.exit(f"FAIL: deploy list Result={dl.get('Result')!r}")
items = dl.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
names = [_pick(d, "Name") or _pick(d, "DeploymentName") for d in items if isinstance(d, dict)]
if deploy_name not in names:
    sys.exit(f"FAIL: deploy {deploy_name!r} not in deploy list; saw {names[:5]}")

# Folder exists
folder_path = f"Shared/{folder_name}"
fg = uip_json("or", "folders", "get", folder_path)
if fg.get("Result") != "Success":
    sys.exit(f"FAIL: folder {folder_path!r} not present: {fg.get('Message')!r}")

# Process in folder
pl = uip_json("or", "processes", "list", "--folder-path", folder_path)
if pl.get("Result") != "Success":
    sys.exit(f"FAIL: processes list in {folder_path!r}: {pl.get('Message')!r}")
procs = pl.get("Data") or []
if isinstance(procs, dict):
    procs = _pick(procs, "Value", "Items", "Results") or []
if not procs:
    sys.exit(f"FAIL: folder {folder_path!r} has no processes")

print(f"OK: deploy {deploy_name!r} in list; folder {folder_path!r} has {len(procs)} process(es)")
