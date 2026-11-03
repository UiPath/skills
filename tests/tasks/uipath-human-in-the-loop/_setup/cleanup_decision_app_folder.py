#!/usr/bin/env python3
# post_run: delete the Orchestrator folder recorded in report.json (`folder` key).
# Mirrors uipath-coded-apps' cleanup_codedapp_folder.py. Always exits 0.
import json
import os
import subprocess
import sys


def load_folder_name() -> str:
    if os.path.exists("report.json"):
        try:
            r = json.load(open("report.json"))
            name = (r.get("folder") or "").strip()
            if name:
                return name
        except Exception:
            pass
    return ""


folder = load_folder_name()
if not folder:
    sys.exit(0)

# Allowlist, not a denylist: only ever delete a per-run disposable test folder.
if not folder.lower().startswith("decisionapp-"):
    print(f"SKIP: folder '{folder}' does not start with 'decisionapp-' — refusing to delete", file=sys.stderr)
    sys.exit(0)

try:
    subprocess.run(
        ["uip", "or", "folders", "delete", folder, "--yes", "--output", "json"],
        capture_output=True, timeout=60,
    )
except subprocess.TimeoutExpired:
    print(f"TIMEOUT: folder delete for '{folder}' exceeded 60s (tenant slow); leaving folder in place", file=sys.stderr)
except Exception as e:
    print(f"WARN: folder delete for '{folder}' failed: {e}", file=sys.stderr)
sys.exit(0)
