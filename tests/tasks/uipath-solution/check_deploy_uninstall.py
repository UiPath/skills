#!/usr/bin/env python3
"""Query tenant: the e2e deploy is GONE from the list and its provisioned
folder is removed (i.e. `solution deploy uninstall` succeeded).

`deploy uninstall` is eventually-consistent — the command can return before
the backend has finished tearing the deployment + folder down. So poll for
the end-state (deploy absent AND folder absent) for a bounded window rather
than checking once."""

import json
import subprocess
import sys
import time
from pathlib import Path

POLL_ATTEMPTS = 8
POLL_INTERVAL_S = 15


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


def deploy_present() -> bool:
    dl = uip_json("solution", "deploy", "list")
    if dl.get("Result") != "Success":
        sys.exit(f"FAIL: deploy list Result={dl.get('Result')!r}")
    items = dl.get("Data") or []
    if isinstance(items, dict):
        items = _pick(items, "Value", "Items", "Results") or []
    names = [_pick(d, "Name") or _pick(d, "DeploymentName") for d in items if isinstance(d, dict)]
    return deploy_name in names


def folder_present() -> bool:
    fg = uip_json("or", "folders", "get", folder_path, required=False)
    return fg.get("Result") == "Success"


# Poll for the teardown to complete (uninstall is eventually-consistent).
last = "unknown"
for attempt in range(1, POLL_ATTEMPTS + 1):
    dp, fp = deploy_present(), folder_present()
    if not dp and not fp:
        print(f"OK: deploy {deploy_name!r} gone from list and folder {folder_path!r} removed (after {attempt} poll(s))")
        sys.exit(0)
    last = f"deploy_present={dp}, folder_present={fp}"
    if attempt < POLL_ATTEMPTS:
        time.sleep(POLL_INTERVAL_S)

sys.exit(f"FAIL: uninstall did not complete within ~{POLL_ATTEMPTS * POLL_INTERVAL_S}s — {last} (deploy {deploy_name!r}, folder {folder_path!r})")
