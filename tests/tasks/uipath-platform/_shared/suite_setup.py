#!/usr/bin/env python3
"""Suite-level setup: publish + deploy the e2e-stub solution ONCE for all
process-dependent tests. Prints `export TRACES_SMOKE_PROCESS_KEY=...`,
`export E2E_SUITE_DEPLOY=...` so the shell can `eval` them.

Idempotent on re-run — if the deployment with the expected name already
exists, reuses it. Otherwise deploys.

Usage:
    eval "$(python3 tests/tasks/uipath-platform/_shared/suite_setup.py)"
    # ... run coder-eval with TRACES_SMOKE_PROCESS_KEY already in env ...
    python3 tests/tasks/uipath-platform/_shared/suite_teardown.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import uuid
from pathlib import Path

SHARED = Path(__file__).resolve().parent
FIXTURES = SHARED.parent.parent.parent / "fixtures"


def uip(*args: str, check: bool = True) -> dict:
    import json
    r = subprocess.run(["uip", *args, "--output", "json"], capture_output=True, text=True, timeout=420)
    try:
        env = json.loads(r.stdout) if r.stdout.strip() else {}
    except json.JSONDecodeError:
        env = {}
    if check and env.get("Result") != "Success":
        msg = (env.get("Message") or "").lower()
        if "already exists" not in msg and "duplicate" not in msg:
            print(f"# uip {' '.join(args)} FAILED: {env}", file=sys.stderr)
            sys.exit(1)
    return env


def log(msg: str) -> None:
    print(f"# suite: {msg}", file=sys.stderr)


def main() -> int:
    deploy_name = os.environ.get("E2E_SUITE_DEPLOY_NAME", "e2e-suite-shared-deploy")
    folder_name = f"{deploy_name}-folder"

    # Is the deployment already present?
    import json
    existing = uip("solution", "deploy", "list", check=False)
    if existing.get("Result") == "Success":
        items = existing.get("Data") or []
        if isinstance(items, dict):
            items = items.get("Value") or items.get("Items") or items.get("Results") or []
        match = next((d for d in items if (d.get("Name") or d.get("DeploymentName")) == deploy_name), None)
        if match:
            status = (match.get("Status") or "").lower()
            if "uninstall" not in status and "fail" not in status:
                # Already deployed; just find the process key
                folder_path = f"Shared/{folder_name}"
                procs = uip("or", "processes", "list", "--folder-path", folder_path, check=False)
                if procs.get("Result") == "Success":
                    plist = procs.get("Data") or []
                    if isinstance(plist, dict):
                        plist = plist.get("Value") or plist.get("Items") or plist.get("Results") or []
                    if plist:
                        pkey = plist[0].get("Key") or plist[0].get("Id")
                        log(f"reusing existing deploy {deploy_name!r} → process {pkey}")
                        print(f"export TRACES_SMOKE_PROCESS_KEY={pkey}")
                        print(f"export E2E_SUITE_DEPLOY={deploy_name}")
                        return 0

    # Fresh deploy
    stub = FIXTURES / "packages" / "e2e-stub-1.0.0.zip"
    if not stub.is_file():
        log(f"FAIL: stub fixture not at {stub}")
        return 1

    log(f"publishing {stub.name}…")
    uip("solution", "publish", str(stub), check=False)  # 409 = ok

    log(f"deploying {deploy_name} → Shared/{folder_name}…")
    res = uip(
        "solution", "deploy", "run",
        "--name", deploy_name,
        "--package-name", "e2e-stub",
        "--package-version", "1.0.0",
        "--folder-name", folder_name,
        "--folder-path", "Shared",
    )
    log(f"deploy succeeded ({res.get('Data', {}).get('Status')})")

    folder_path = f"Shared/{folder_name}"
    procs = uip("or", "processes", "list", "--folder-path", folder_path)
    items = procs.get("Data") or []
    if isinstance(items, dict):
        items = items.get("Value") or items.get("Items") or items.get("Results") or []
    if not items:
        log(f"FAIL: no processes in {folder_path}")
        return 1
    pkey = items[0].get("Key") or items[0].get("Id")
    log(f"process key {pkey}")

    print(f"export TRACES_SMOKE_PROCESS_KEY={pkey}")
    print(f"export E2E_SUITE_DEPLOY={deploy_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
