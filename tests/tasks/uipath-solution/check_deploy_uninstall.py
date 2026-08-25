#!/usr/bin/env python3
"""Query tenant: `solution deploy uninstall` tore down the deployment's
provisioned Orchestrator FOLDER (and the resources inside it).

Per references/activate-and-manage.md, uninstall "removes the Orchestrator
folder and all resources inside it" — it does NOT remove the deployment
record from `deploy list` (that entry persists, just no longer provisioned).
So the reliable success signal is the folder being gone. Uninstall is also
eventually-consistent, so poll for the teardown rather than checking once."""

import json
import subprocess
import sys
import time
from pathlib import Path

POLL_ATTEMPTS = 8
POLL_INTERVAL_S = 15


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

parent = seed.get("parent_folder_path") or "Shared"
folder_path = f"{parent}/e2e-deploy-folder-{uuid8}"


def folder_status() -> str:
    """A genuinely-missing folder returns a structured Failure envelope
    (verified: Result=Failure, "Folder not found: ..."). A present folder
    returns Result=Success. Anything else (empty/unparseable stdout) is a
    transient/ambiguous response — do NOT treat it as "absent", or a flaky
    `folders get` could false-pass the uninstall check."""
    fg = uip_json("or", "folders", "get", folder_path, required=False)
    result = fg.get("Result")
    if result == "Success":
        return "present"
    if result == "Failure":
        return "absent"
    return "unknown"


# Poll for the folder teardown to complete (uninstall is eventually-consistent).
# Pass only on a definitive "absent" (a real Failure envelope); never on an
# ambiguous/empty response.
last = "unknown"
for attempt in range(1, POLL_ATTEMPTS + 1):
    last = folder_status()
    if last == "absent":
        print(f"OK: uninstall removed folder {folder_path!r} (after {attempt} poll(s))")
        sys.exit(0)
    if attempt < POLL_ATTEMPTS:
        time.sleep(POLL_INTERVAL_S)

sys.exit(
    f"FAIL: folder {folder_path!r} not confirmed removed ~{POLL_ATTEMPTS * POLL_INTERVAL_S}s "
    f"after uninstall (last status={last!r}; 'present'=still there, 'unknown'=ambiguous CLI response)"
)
