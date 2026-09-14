#!/usr/bin/env python3
"""pre_run: create one IXP project from the fixture invoices, record only its TITLE.

  seed.json = {"uuid8": "a1b2c3d4", "project": {"title": "Codereval IXP Seed a1b2c3d4"}}

The ProjectName slug is deliberately withheld — a task grading Title ->
ProjectName resolution is meaningless once the slug is in the sandbox. Whoever
needs it later looks it up from `projects list` by the run id.

The uuid8 makes the title unique per run, so concurrent runs never collide and a
leftover from a failed cleanup is never mistaken for this run's project.

  IXP_SEED_TITLE_BASE  title stem (default `Codereval IXP Seed`)

Exits non-zero if the tenant rejects the seed: pre_run's fail_on_error then ends
the run as an environment error instead of scoring the skill against a project
that does not exist.
"""

import json
import os
import subprocess
import sys
import time
import uuid

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
EXPECTED_DOCS = {"csi_tower_invoice.png", "hp_tax_invoice.png", "york_solutions_invoice.png"}


def uip(*args, timeout=180):
    """Run `uip <args> --output json` and return the parsed envelope, or exit 1."""
    cmd = ["uip", *args, "--output", "json"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as exc:
        sys.exit("seed_project: %s failed to invoke: %s" % (" ".join(cmd), exc))
    if proc.returncode != 0:
        sys.exit("seed_project: %s exited %d: %s"
                 % (" ".join(cmd), proc.returncode, (proc.stderr or proc.stdout or "")[:500]))
    try:
        return json.loads(proc.stdout)
    except ValueError:
        sys.exit("seed_project: %s returned non-JSON: %s" % (" ".join(cmd), proc.stdout[:500]))


def uploaded_filenames(project_name):
    data = uip("ixp", "documents", "list", project_name, "-l", "100").get("Data") or {}
    return {d.get("Filename") for d in (data.get("Documents") or [])}


def main():
    run_id = uuid.uuid4().hex[:8]
    base = (os.environ.get("IXP_SEED_TITLE_BASE") or "Codereval IXP Seed").strip()
    title = "%s %s" % (base, run_id)

    created = uip("ixp", "projects", "create", title, FIXTURES, "--skip-taxonomy").get("Data") or {}
    name = created.get("ProjectName") or created.get("Name")
    if not name:
        sys.exit("seed_project: create returned no ProjectName: %s" % json.dumps(created)[:500])

    # Cleanup and the tenant check locate this project by the run id in its
    # ProjectName. Fail here rather than leak the project later.
    if run_id not in name:
        sys.exit("seed_project: ProjectName %r does not carry run id %s; "
                 "cleanup could not find this project" % (name, run_id))

    # `projects delete` resolves the dataset first and 404s without one, so a
    # taxonomy-less project cannot be cleaned up.
    uip("ixp", "projects", "import-taxonomy", name, os.path.join(FIXTURES, "taxonomy.json"))

    # Confirm the uploads landed: a partial one reads as an unexplained failure.
    for attempt in range(5):
        found = uploaded_filenames(name)
        if EXPECTED_DOCS <= found:
            break
        if attempt < 4:
            time.sleep(3)
    else:
        sys.exit("seed_project: %s holds %s, expected %s"
                 % (name, sorted(found), sorted(EXPECTED_DOCS)))

    with open("seed.json", "w", encoding="utf-8") as fh:
        json.dump({"uuid8": run_id, "project": {"title": title}}, fh)

    # Run log only — the sandbox gets the title alone.
    print("seed_project: seeded '%s' as %s with %d documents" % (title, name, len(found)))


main()
