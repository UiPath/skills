#!/usr/bin/env python3
"""Post-run cleanup for IXP tasks: delete THIS run's project.

Two sources, read from CWD, whichever are present:

  report.json  {"project_name": "<ProjectName>"} — the agent created the project
  seed.json    {"uuid8": "<run id>", ...} — pre_run created it; the slug is
               withheld from the sandbox, so it is recovered from `projects
               list` by the run id the backend carried into the ProjectName

Only projects this run recorded are deleted — never a sweep. Best-effort and
ALWAYS exits 0; without a tenant this is a no-op.
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
    # Only rc==0 is success. A 404 does NOT mean the project is gone — delete
    # resolves the dataset first and 404s on a dataset-less shell.
    if proc.returncode == 0:
        print(f"OK: deleted IXP project '{name}'")
    else:
        print(f"WARN: could not delete '{name}' (exit {proc.returncode}): {out[:200]}")


def load_json(filename):
    path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(path):
        print(f"SKIP: no {filename} at {path}")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"SKIP: could not parse {filename}: {e}")
        return None


def name_from_report():
    """The project the agent created, as it recorded it."""
    report = load_json("report.json")
    if not report:
        return None
    name = (
        report.get("project_name")
        or report.get("name")
        or report.get("ProjectName")
    )
    if not name:
        print("SKIP: no 'project_name' key in report.json")
    return name


def name_from_seed():
    """The project pre_run created, found in `projects list` by this run's uuid8.

    The ProjectName survives an `update-title`, so the uuid8 finds the project
    even if the agent renamed it. Matching Title would not.
    """
    seed = load_json("seed.json")
    if not seed:
        return None
    run_id = seed.get("uuid8")
    if not run_id:
        print("SKIP: no 'uuid8' key in seed.json")
        return None

    proc = run(["uip", "ixp", "projects", "list", "-l", "10000", "--output", "json"])
    if proc is None or proc.returncode != 0:
        print(f"WARN: could not list projects to find the project seeded for run {run_id}")
        return None
    try:
        projects = (json.loads(proc.stdout).get("Data") or {}).get("Projects") or []
    except Exception as e:
        print(f"WARN: could not parse projects list: {e}")
        return None

    matches = [p["Name"] for p in projects if run_id in (p.get("Name") or "")]
    if len(matches) != 1:
        print(f"WARN: {len(matches)} projects carry run id {run_id}; deleting none")
        return None
    return matches[0]


def main():
    for name in dict.fromkeys(filter(None, [name_from_seed(), name_from_report()])):
        delete_project(name)
    sys.exit(0)


if __name__ == "__main__":
    main()
