#!/usr/bin/env python3
"""pre_run (after _setup/seed.py): create a folder with no robots and a process in it.

Adds `noruntime_folder_path` and `noruntime_process_name` to seed.json. The folder
name carries the uuid8, so _setup/cleanup.py deletes it (and the process and any
trigger in it). Exits non-zero, after deleting the folder it created, when the
folder turns out to have an Unattended runtime, since the task would then test
nothing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def uip_json(*args: str) -> dict:
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        return {}


def fail(msg: str, folder_path: str = "") -> None:
    if folder_path:  # don't rely on post_run cleanup after a failed pre_run
        uip_json("or", "folders", "delete", folder_path, "--yes")
    print(f"seed_no_runtime_folder.py: {msg}", file=sys.stderr)
    sys.exit(1)


seed = json.loads(Path("seed.json").read_text())
uuid8 = seed["uuid8"]
parent = seed["parent_folder_path"]
source_key = seed.get("process_key") or fail("seed.json has no process_key; export E2E_PROCESS_KEY")

source = uip_json("or", "processes", "get", source_key).get("Data") or {}
package_key, package_version = source.get("ProcessKey"), source.get("ProcessVersion")
if not package_key or not package_version:
    fail(f"could not read the package of process {source_key}")

folder_name = f"e2e-noruntime-{uuid8}"
folder_path = f"{parent}/{folder_name}"
created = uip_json("or", "folders", "create", folder_name, "--parent", parent)
if created.get("Result") != "Success":
    fail(f"folders create failed: {created.get('Message')}")

process_name = f"e2e-noruntime-report-{uuid8}"
process = uip_json("or", "processes", "create", "--name", process_name,
                   "--package-key", package_key, "--package-version", package_version,
                   "--folder-path", folder_path)
if process.get("Result") != "Success":
    fail(f"processes create failed: {process.get('Message')}", folder_path)

runtimes = uip_json("or", "folders", "runtimes", folder_path).get("Data") or []
# A tenant may omit a runtime type it has none of; that counts as none.
unattended = next((r for r in runtimes if r.get("Type") == "Unattended"), {})
if unattended.get("Total", 0) != 0:
    fail(f"expected no Unattended runtime in {folder_path}, got {unattended}", folder_path)

seed["noruntime_folder_path"] = folder_path
seed["noruntime_process_name"] = process_name
Path("seed.json").write_text(json.dumps(seed))
