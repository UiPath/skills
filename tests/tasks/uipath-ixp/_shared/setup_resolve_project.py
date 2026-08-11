#!/usr/bin/env python3
"""
Pre-run setup for skill-ixp-integration-name-resolution: create THIS run's
project on the live tenant and hand the agent only its TITLE.

Setup creates it, not the agent, because `projects create` returns
`Data.ProjectName` — an agent that creates its own project already holds the Name
and has no Title to resolve, which is what the task grades.

Writes to the sandbox CWD:
  project_title.txt  the Title, and only the Title — the agent's starting point
  report.json        {"project_name": "<Name>"} for cleanup_project.py post_run

Exits non-zero on any failure (pre_run defaults to fail_on_error=True): the agent
must not run against a half-built fixture.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid


INVOICES = ("csi_tower_invoice.png", "hp_tax_invoice.png", "york_solutions_invoice.png")
TAXONOMY = "taxonomy.json"


def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def run(cmd, timeout=180):
    print("+ " + " ".join(cmd))
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        die(f"could not invoke {' '.join(cmd)}: {e}")
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()[:300]
        die(f"exit {proc.returncode} from {' '.join(cmd)}: {detail}")
    return proc.stdout or ""


def stage_invoices(root):
    """Copy the three invoices into a directory of their own.

    `projects create <title> <folder>` bulk-uploads the folder's top level, so
    staging pins the upload set even if the fixture template later grows another
    supported document at the sandbox root.
    """
    staged = tempfile.mkdtemp(prefix="ixp_resolve_")
    for name in INVOICES:
        src = os.path.join(root, name)
        if not os.path.exists(src):
            die(f"fixture missing: {src}")
        shutil.copy2(src, os.path.join(staged, name))
    return staged


def main():
    root = os.getcwd()
    title = f"codereval-integ-resolve-{uuid.uuid4().hex[:8]}"

    out = run(["uip", "ixp", "projects", "create", title, stage_invoices(root), "--skip-taxonomy", "--output", "json"])
    try:
        name = json.loads(out)["Data"]["ProjectName"]
    except Exception as e:
        die(f"no Data.ProjectName in create output ({e}): {out.strip()[:300]}")

    # Before anything else can fail: a project that exists must stay cleanable.
    with open(os.path.join(root, "report.json"), "w") as f:
        json.dump({"project_name": name}, f)

    taxonomy = os.path.join(root, TAXONOMY)
    if not os.path.exists(taxonomy):
        die(f"fixture missing: {taxonomy}")
    run(["uip", "ixp", "projects", "import-taxonomy", name, taxonomy, "--output", "json"])

    # Written LAST: its presence means the fixture is complete.
    with open(os.path.join(root, "project_title.txt"), "w") as f:
        f.write(title + "\n")

    print(f"OK: seeded title={title} name={name}")
    sys.exit(0)


if __name__ == "__main__":
    main()
