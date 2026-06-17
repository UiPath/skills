#!/usr/bin/env python3
"""Query tenant: the e2e deploy is GONE from the list and its provisioned
folder is removed (i.e. `solution deploy uninstall` succeeded)."""

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


def uip_json(*args: str, required: bool = True) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    if not r.stdout.strip():
        if required:
            sys.exit(f"FAIL: uip {' '.join(args)} no stdout")
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed.get("uuid8")
if not uuid8:
    sys.exit("FAIL: seed.json missing uuid8")

deploy_name = f"e2e-deploy-{uuid8}"
parent = seed.get("parent_folder_path") or "Shared"
folder_path = f"{parent}/e2e-deploy-folder-{uuid8}"

# Deploy must NOT be in the list anymore.
dl = uip_json("solution", "deploy", "list")
if dl.get("Result") != "Success":
    sys.exit(f"FAIL: deploy list Result={dl.get('Result')!r}")
items = dl.get("Data") or []
if isinstance(items, dict):
    items = _pick(items, "Value", "Items", "Results") or []
names = [_pick(d, "Name") or _pick(d, "DeploymentName") for d in items if isinstance(d, dict)]
if deploy_name in names:
    sys.exit(f"FAIL: deploy {deploy_name!r} still present after uninstall; saw {names[:5]}")

# The provisioned folder should be gone too (uninstall removes it). A missing
# folder returns a non-Success envelope (or nothing) — that's the pass case.
fg = uip_json("or", "folders", "get", folder_path, required=False)
if fg.get("Result") == "Success":
    sys.exit(f"FAIL: folder {folder_path!r} still present after uninstall")

print(f"OK: deploy {deploy_name!r} gone from list and folder {folder_path!r} removed")
