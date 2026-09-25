#!/usr/bin/env python3
"""pre_run: delete IXP projects leaked by earlier runs of the live IXP tasks.

cleanup_project.py deletes only the project its own run recorded, so a run that
dies before writing report.json leaves its project behind. Every project holds
IXP sources and the tenant caps them (100 on the codereval tenant). Once the
leaks fill the cap, `projects create` fails with 403 "quotas exceeded" for
every run until someone deletes projects by hand.

A project is swept only when BOTH hold:

  its ProjectName starts with PROJECT_PREFIX   every live IXP task names its
                                               project `codereval-<task>-…`
  its CreatedAt is older than STALE_AFTER      past any live run's budget, so a
                                               concurrent run's project is safe

A project whose CreatedAt is missing or unparseable is kept. Best-effort and
ALWAYS exits 0: hygiene, not a gate. A sweep problem must never cost a run.
"""

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

PROJECT_PREFIX = "codereval-"

# The longest live IXP task budget is 6000s (publish_lifecycle,
# versions_and_metrics). Three hours keeps a margin over it even with clock
# skew between the tenant's CreatedAt and the runner.
STALE_AFTER = timedelta(hours=3)

# Stop issuing deletes past this, so the script ends inside its 300s pre_run
# timeout on a large backlog: the 60s list, this budget, and one last 60s
# delete. The next run collects the rest.
DELETE_BUDGET_SECONDS = 150

LIST_LIMIT = "10000"


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        print(f"WARN: command failed to invoke ({' '.join(cmd)}): {e}")
        return None


def list_projects():
    proc = run(["uip", "ixp", "projects", "list", "-l", LIST_LIMIT, "--output", "json"])
    if proc is None or proc.returncode != 0:
        detail = "" if proc is None else (proc.stdout or proc.stderr or "").strip()[:200]
        print(f"WARN: could not list projects; nothing swept. {detail}")
        return None
    try:
        data = json.loads(proc.stdout).get("Data") or {}
    except Exception as e:
        print(f"WARN: could not parse projects list; nothing swept: {e}")
        return None
    projects = data.get("Projects") or []
    total = data.get("Total")
    if isinstance(total, int) and total > len(projects):
        print(f"WARN: project list truncated ({len(projects)} of {total}); sweeping what was returned")
    return projects


def created_at(project):
    """CreatedAt as an aware datetime, or None. Naive timestamps are read as UTC."""
    raw = project.get("CreatedAt")
    if not raw:
        return None
    # The tenant emits 5-digit fractions (`05:20:06.54035+00:00`), which
    # fromisoformat rejects before Python 3.11, as it does a trailing `Z`.
    raw = str(raw).replace("Z", "+00:00")
    raw = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], raw, count=1)
    try:
        created = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return created if created.tzinfo else created.replace(tzinfo=timezone.utc)


def stale_projects(projects, now):
    """Names to sweep, oldest first."""
    stale = []
    for project in projects:
        name = project.get("Name") or ""
        created = created_at(project)
        if name.startswith(PROJECT_PREFIX) and created is not None and now - created > STALE_AFTER:
            stale.append((created, name))
    return [name for _, name in sorted(stale)]


def delete_project(name):
    proc = run(["uip", "ixp", "projects", "delete", name, "-y", "--output", "json"])
    if proc is None:
        return
    if proc.returncode == 0:
        print(f"OK: swept stale IXP project '{name}'")
        return
    # A concurrent run's sweep may have deleted it first. Also expected for a
    # project with no dataset, which `projects delete` cannot resolve.
    out = (proc.stdout or proc.stderr or "").strip()
    print(f"WARN: could not delete '{name}' (exit {proc.returncode}): {out[:200]}")


def main():
    projects = list_projects()
    if projects is None:
        return
    stale = stale_projects(projects, datetime.now(timezone.utc))
    print(f"sweep: {len(projects)} project(s) on the tenant, {len(stale)} stale '{PROJECT_PREFIX}*' "
          f"older than {STALE_AFTER}")

    started = time.monotonic()
    for index, name in enumerate(stale):
        if time.monotonic() - started > DELETE_BUDGET_SECONDS:
            print(f"sweep: delete budget spent; {len(stale) - index} left for the next run")
            break
        delete_project(name)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"WARN: sweep aborted: {e}")
    sys.exit(0)
