#!/usr/bin/env python3
"""post_run: delete the Orchestrator folder recorded in report.json.

Deploy-running coded-app tests provision a fresh folder per run (name pattern
`codedapp-<taskslug>-<uuid8>`), deploy the app into it, and write the folder
name into report.json under the `folder` key. Deleting that folder cascades
to the coded-app deployment inside (verified empirically: post-delete the
app URL returns HTTP 404). The published-package registry entry lives at
tenant scope and is not cleaned by this script.

Read priority for folder name:
  1. report.json `folder` key
  2. report.json `folder_name` key (legacy)
  3. `.folder_to_cleanup` marker file

Exits 0 always — cleanup failures never fail the test.
"""
import json
import os
import subprocess
import sys


def load_folder_name() -> str:
    if os.path.exists("report.json"):
        try:
            r = json.load(open("report.json"))
            name = (r.get("folder") or r.get("folder_name") or "").strip()
            if name:
                return name
        except Exception:
            pass
    if os.path.exists(".folder_to_cleanup"):
        try:
            return open(".folder_to_cleanup").read().strip()
        except Exception:
            pass
    return ""


folder = load_folder_name()
if not folder:
    sys.exit(0)

# Guardrail: never touch tenant-default folders. Test folders must use the
# `codedapp-` prefix — anything else is either a test authoring bug or an
# attempt to run this against something it shouldn't touch.
if not folder.lower().startswith("codedapp-"):
    print(f"SKIP: folder '{folder}' does not start with 'codedapp-' — refusing to delete", file=sys.stderr)
    sys.exit(0)

try:
    subprocess.run(
        ["uip", "or", "folders", "delete", folder, "--yes", "--output", "json"],
        capture_output=True, timeout=60,
    )
except subprocess.TimeoutExpired:
    print(f"TIMEOUT: folder delete for '{folder}' exceeded 60s (tenant slow); leaving folder in place", file=sys.stderr)
except Exception as e:
    # Any other failure — network, CLI crash, non-zero exit — is non-fatal.
    # Docstring contract: cleanup failures never fail the test.
    print(f"WARN: folder delete for '{folder}' failed: {e}", file=sys.stderr)
sys.exit(0)
