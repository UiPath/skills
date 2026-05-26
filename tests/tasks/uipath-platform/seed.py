#!/usr/bin/env python3
"""pre_run: generate seed.json with uuid8 and optional process/folder context."""
import json, os, subprocess, sys, uuid

def uip_json(*args):
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}

seed = {
    "uuid8": uuid.uuid4().hex[:8],
    # Parent folder under which tests place any new folder they create
    # (folders_hierarchy's tree, deploy_round_trip's deploy folder, etc.).
    # Defaults to Shared for local dev; CI sets it to an isolated subfolder
    # like `Shared/uipath-platform-e2e` so all test junk stays out of Shared
    # root.
    "parent_folder_path": os.environ.get("E2E_TEST_PARENT_FOLDER", "Shared"),
}

key = os.environ.get("E2E_PROCESS_KEY", "")
if key:
    seed["process_key"] = key
    # `or processes get` doesn't populate FolderPath — use list and match by Key.
    items = (uip_json("or", "processes", "list").get("Data") or [])
    if isinstance(items, dict):
        items = items.get("Value") or items.get("Items") or items.get("Results") or []
    match = next((p for p in items if (p.get("Key") or "").lower() == key.lower()), None)
    fp = (match or {}).get("FolderPath") or (match or {}).get("FolderName") or ""
    if not fp:
        print(f"seed.py: could not resolve folder for E2E_PROCESS_KEY={key} via 'or processes list' — check the key is correct and the process exists.", file=sys.stderr)
        sys.exit(1)
    seed["folder_path"] = fp
    seed["folder_a_path"] = fp

json.dump(seed, open("seed.json", "w"))
