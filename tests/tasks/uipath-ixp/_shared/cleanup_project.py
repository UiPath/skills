#!/usr/bin/env python3
"""
Post-run cleanup for IXP e2e/integration tasks: delete THIS run's project.

Reads report.json (CWD), written by the agent right after creation:
  {"project_name": "<ProjectName from `uip ixp projects create` output>"}

and deletes that one project via `uip ixp projects delete <name> -y --output json`.
It only ever removes the project the current run created — it does NOT sweep or
touch any other (older / leftover) project.

Best-effort and ALWAYS exits 0 (a delete failure is logged as WARN, never fails
the test). Locally without a tenant this is a no-op.
"""

import json
import os
import subprocess
import sys


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        print(f"WARN: command failed to invoke ({' '.join(cmd)}): {e}")
        return None


def delete_project(name):
    """Delete one project by name. Best-effort."""
    proc = run(["uip", "ixp", "projects", "delete", name, "-y", "--output", "json"])
    if proc is None:
        return
    out = (proc.stdout or proc.stderr or "").strip()
    # Only rc==0 is success. Do NOT treat any error — including 404 — as benign:
    # `uip ixp projects delete <name>` 404s on a dataset-less project shell (the
    # delete resolves the dataset first), so a 404 does NOT mean the project is
    # gone. Surface every non-zero exit as WARN rather than masking it.
    if proc.returncode == 0:
        print(f"OK: deleted IXP project '{name}'")
    else:
        print(f"WARN: could not delete '{name}' (exit {proc.returncode}): {out[:200]}")


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


def cleanup_own_project():
    report = load_report()
    if not report:
        return
    name = (
        report.get("project_name")
        or report.get("name")
        or report.get("ProjectName")
    )
    if not name:
        print("SKIP: no 'project_name' key in report.json")
        return
    delete_project(name)


def main():
    cleanup_own_project()
    sys.exit(0)


if __name__ == "__main__":
    main()
