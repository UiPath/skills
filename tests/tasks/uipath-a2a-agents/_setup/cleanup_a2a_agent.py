#!/usr/bin/env python3
"""
Post-run cleanup: delete the remote A2A agent an e2e task created.

Reads report.json (CWD), written by the agent:
  {"slug": "<agent-slug>", "folder_path": "Shared"}   # or "folder_key": "<guid>"

Deletes via the authed CLI: `uip agenthub remote-a2a-agent delete <slug> --yes --folder-path|--folder-key ...`
(`--yes` is required: without it the CLI refuses the delete instead of prompting).
Idempotent — a missing agent counts as already-clean. Exit 0 ALWAYS: cleanup failures never
fail the test (as tests/tasks/uipath-mcp-servers/_setup/cleanup_mcp_server.py). Locally without a
tenant this is a no-op.
"""

import json
import os
import subprocess
import sys


def load_report():
    path = os.path.join(os.getcwd(), "report.json")
    if not os.path.exists(path):
        print(f"SKIP: no report.json at {path}")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"SKIP: could not parse report.json: {e}")
        return None


def main():
    report = load_report()
    if not report:
        sys.exit(0)

    slug = report.get("slug")
    if not slug:
        print("SKIP: no 'slug' key in report.json")
        sys.exit(0)

    cmd = ["uip", "agenthub", "remote-a2a-agent", "delete", slug, "--yes"]
    if report.get("folder_key"):
        cmd += ["--folder-key", report["folder_key"]]
    else:
        cmd += ["--folder-path", report.get("folder_path", "Shared")]
    cmd += ["--output", "json"]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except Exception as e:
        print(f"WARN: delete invocation failed: {e}")
        sys.exit(0)

    out = (proc.stdout or proc.stderr or "").strip()
    if proc.returncode == 0:
        print(f"OK: deleted remote A2A agent '{slug}'")
    elif "not found" in out.lower() or "404" in out:
        print(f"SKIP: remote A2A agent '{slug}' not found (already deleted / never created)")
    else:
        print(f"WARN: could not delete '{slug}' (exit {proc.returncode}): {out[:200]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
