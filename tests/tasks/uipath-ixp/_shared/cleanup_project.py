#!/usr/bin/env python3
"""
Post-run cleanup for IXP e2e/integration tasks: delete THIS run's project.

Primary source is report.json (CWD), written by the agent right after creation:
  {"project_name": "<ProjectName from `uip ixp projects create` output>"}

Fallback when report.json is absent or unusable (run aborted before writing it):
recover the titles this run passed to `uip ixp projects create` from
mocks/calls.log. A title is not deletable on its own — every other command takes
the server-assigned Name (slug + uuid + `-ixp`) — so each title is resolved in
this order:
  1. a Name already in calls.log that provably derives from that title
     (`<title>-<hex>-ixp`), needing no tenant call;
  2. `uip ixp projects list`, on an EXACT and UNIQUE Title match;
  3. neither -> print `WARN: possible leaked project <title>` for CI grep.

Never deletes on an ambiguous or approximate match: a leaked project costs one
grep in CI logs, deleting a concurrent run's project costs that run. The wrapper
logs each call BEFORE exec'ing the CLI, so a create line proves only that the
call was launched — an unresolved title therefore always WARNs and never reports
the tenant clean.

Only ever removes what this run created — it does NOT sweep older leftovers.
Best-effort and ALWAYS exits 0 (failures are logged as WARN, never fail the
test). Locally without a tenant this is a no-op.
"""

import json
import os
import re
import shlex
import subprocess
import sys

CALLS_LOG = os.path.join("mocks", "calls.log")
LIST_LIMIT = 1000
CREATE_LINE = re.compile(r"^uip\s+ixp\s+projects\s+create\s+(.*)$")
VALUE_FLAGS = {"-d", "--description", "-o", "--output"}


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


def name_from_report():
    report = load_report()
    if report is None:
        return None
    if not isinstance(report, dict):
        print("SKIP: report.json is not a JSON object")
        return None
    name = (
        report.get("project_name")
        or report.get("name")
        or report.get("ProjectName")
    )
    if not name:
        print("SKIP: no 'project_name' key in report.json")
    return name


def read_calls_log():
    path = os.path.join(os.getcwd(), CALLS_LOG)
    if not os.path.exists(path):
        print(f"SKIP: no {CALLS_LOG} - nothing to recover from")
        return None
    try:
        with open(path, errors="replace") as f:
            return f.readlines()
    except Exception as e:
        print(f"SKIP: could not read {CALLS_LOG}: {e}")
        return None


def created_titles(lines):
    """Titles passed to `projects create`, in log order, deduplicated.

    The wrapper logs `uip $*`, so the original quoting is gone: a title with
    spaces recovers as its first word only, matches nothing below, and degrades
    to the WARN line instead of to a wrong delete.
    """
    titles = []
    for line in lines:
        match = CREATE_LINE.match(line.strip())
        if not match:
            continue
        try:
            args = shlex.split(match.group(1))
        except ValueError:
            args = match.group(1).split()
        skip_next = False
        for arg in args:
            if skip_next:
                skip_next = False
            elif arg.startswith("-"):
                skip_next = arg in VALUE_FLAGS
            else:
                if arg not in titles:
                    titles.append(arg)
                break
    return titles


def names_in_log(title, lines):
    """Names in the log that provably derive from `title`.

    Anchoring on the whole title plus a hex uuid excludes a foreign project
    whose title merely extends ours (`<title>x-<uuid>-ixp` does not match).
    """
    pattern = re.compile(rf"^{re.escape(title.lower())}-[0-9a-f][0-9a-f-]*-ixp$")
    found = []
    for line in lines:
        for token in line.split():
            token = token.strip("\"'")
            if pattern.match(token.lower()) and token not in found:
                found.append(token)
    return found


def resolve_name_on_tenant(title):
    """Resolve Title -> Name via `projects list`. Returns (name, reason); reason
    is set only when unresolved."""
    proc = run(["uip", "ixp", "projects", "list", "-l", str(LIST_LIMIT), "--output", "json"])
    if proc is None or proc.returncode != 0:
        return None, "tenant lookup failed"
    try:
        payload = json.loads(proc.stdout or "").get("Data") or {}
    except Exception:
        return None, "tenant lookup returned no usable JSON"
    rows = payload.get("Projects") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return None, "tenant lookup returned no usable JSON"
    names = sorted({
        row["Name"] for row in rows
        if isinstance(row, dict) and row.get("Title") == title and row.get("Name")
    })
    if len(names) == 1:
        return names[0], None
    if len(names) > 1:
        return None, f"{len(names)} projects share that title"
    total = payload.get("Total") if isinstance(payload, dict) else None
    if isinstance(total, int) and total > len(rows):
        return None, f"title absent from the first {len(rows)} of {total} projects"
    return None, "no exact-title match on tenant"


def cleanup_from_calls_log():
    lines = read_calls_log()
    if lines is None:
        return
    titles = created_titles(lines)
    if not titles:
        print(f"SKIP: no `projects create` in {CALLS_LOG} - this run created no project")
        return
    for title in titles:
        candidates = names_in_log(title, lines)
        if len(candidates) == 1:
            delete_project(candidates[0])
        elif len(candidates) > 1:
            print(f"WARN: possible leaked project {title} (ambiguous names: {', '.join(candidates)})")
        else:
            name, reason = resolve_name_on_tenant(title)
            if name:
                delete_project(name)
            else:
                print(f"WARN: possible leaked project {title} ({reason})")


def main():
    try:
        name = name_from_report()
        if name:
            delete_project(name)
        else:
            cleanup_from_calls_log()
    except Exception as e:
        print(f"WARN: cleanup aborted: {e}")
    sys.exit(0)


if __name__ == "__main__":
    main()
