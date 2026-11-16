#!/usr/bin/env python3
"""pre_run: delete IXP projects leaked by earlier runs of the live IXP tasks,
then the AuthZ role assignments that project deletes leave behind.

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

A project whose CreatedAt is missing or unparseable is kept.

Deleting a project through the designtime API, which `uip ixp projects delete`
calls, drops the project but leaves its project-scope AuthZ role assignment
`/tenant/<tid>/Reinfer/project/<hex>` (RE-12819). Every run leaks at least one.
They pile up until AuthZ's OPA evaluation for the user runs out of memory, PAP
answers 500, and every IXP call fails. The CLI can neither list project scopes
nor return the hex project id, so the purge calls the PAP and reinfer APIs
directly with the CLI's own `.auth` token, as DU-App's AuthzProjectRoleCleanup
does.

An assignment is purged only when ALL hold:

  its scope is a Reinfer project of the     another tenant in the org is never
  login tenant                              touched
  its project is missing from reinfer's     `_private/projects` lists the whole
  project list                              tenant, not only what the caller sees
  its createdOn is older than STALE_AFTER   a concurrent run's new project can be
                                            missing from the list for minutes
                                            (RE-12698)

The purge is skipped outright when reinfer's list fails, comes back empty, or
lacks a project the CLI listed: a list that misses one live project would strip
that project's access.

`--dry-run` reports what would be deleted and deletes nothing. Best-effort and
ALWAYS exits 0: hygiene, not a gate. A sweep problem must never cost a run.
"""

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

PROJECT_PREFIX = "codereval-"

# The longest live IXP task budget is 6000s (publish_lifecycle,
# versions_and_metrics). Three hours keeps a margin over it even with clock
# skew between the tenant's CreatedAt and the runner.
STALE_AFTER = timedelta(hours=3)

# Both budgets stop issuing calls once spent, so the script ends inside its
# 300s pre_run timeout on a large backlog: the 60s list, this budget, one last
# 60s delete, the purge budget, and one last HTTP call (60+100+60+50+15 = 285).
# The next run collects the rest.
DELETE_BUDGET_SECONDS = 100
PURGE_BUDGET_SECONDS = 50
HTTP_TIMEOUT_SECONDS = 15

LIST_LIMIT = "10000"

AUTH_FILES = (os.path.expanduser("~/.uipath/.auth"), "/.uipath/.auth")
AUTH_KEYS = (
    "UIPATH_ACCESS_TOKEN",
    "UIPATH_URL",
    "UIPATH_ORGANIZATION_NAME",
    "UIPATH_ORGANIZATION_ID",
    "UIPATH_TENANT_NAME",
    "UIPATH_TENANT_ID",
)
AUTHZ_PAGE_SIZE = 10  # AuthZ caps `top` at 10; a page is 10 principals, not 10 assignments
AUTHZ_DELETE_BATCH = 50


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


def parse_timestamp(raw):
    """An aware datetime, or None. Naive timestamps are read as UTC."""
    if not raw:
        return None
    # The tenant emits 5-digit fractions (`05:20:06.54035+00:00`), which
    # fromisoformat rejects before Python 3.11, as it does a trailing `Z`.
    raw = str(raw).replace("Z", "+00:00")
    raw = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], raw, count=1)
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def stale_projects(projects, now):
    """Names to sweep, oldest first."""
    stale = []
    for project in projects:
        name = project.get("Name") or ""
        created = parse_timestamp(project.get("CreatedAt"))
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


def read_auth():
    """The CLI session as {AUTH_KEYS: value}, or None.

    Read after a `uip` call, which refreshes the token in the file.
    """
    for path in AUTH_FILES:
        try:
            with open(path, encoding="utf-8") as f:
                pairs = dict(line.strip().split("=", 1) for line in f if "=" in line)
        except OSError:
            continue
        auth = {key: pairs.get(key) for key in AUTH_KEYS}
        auth["UIPATH_URL"] = (auth["UIPATH_URL"] or "").rstrip("/")
        if all(auth.values()) and auth["UIPATH_URL"].startswith("https://"):
            return auth
    return None


def api(auth, method, url, headers, body=None):
    """JSON from one HTTP call. Raises on a non-2xx answer; never echoes the token."""
    request = urllib.request.Request(
        url,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        method=method,
        headers={
            "Authorization": f"Bearer {auth['UIPATH_ACCESS_TOKEN']}",
            "Content-Type": "application/json",
            # Cloudflare rejects urllib's default Python-urllib UA (error 1010).
            "User-Agent": "uipath-skills-tests-ixp-sweep/1.0",
            **headers,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            raw = response.read()
    except urllib.error.HTTPError as e:
        snippet = e.read().decode("utf-8", "replace")[:200]
        raise RuntimeError(f"{method} {urllib.parse.urlsplit(url).path} answered {e.code}: {snippet}") from None
    return json.loads(raw) if raw.strip() else {}


def assignments_url(auth):
    return f"{auth['UIPATH_URL']}/{auth['UIPATH_ORGANIZATION_ID']}/pap_/api/userroleassignments"


def project_role_assignments(auth, budget_left):
    """This tenant's Reinfer project-scope assignments as (id, project hex, createdOn)."""
    org_id = auth["UIPATH_ORGANIZATION_ID"]
    # GUID casing is not guaranteed to match between `.auth` and AuthZ.
    prefix = f"/tenant/{auth['UIPATH_TENANT_ID']}/Reinfer/project/".lower()
    found, skip = [], 0
    while True:
        if not budget_left():
            raise TimeoutError("budget spent while listing role assignments")
        # The root scope with inheritance on enumerates every assignment in the
        # org, each carrying its real scope.
        query = urllib.parse.urlencode({
            "x-uipath-internal-accountid": org_id,
            "serviceName": "Reinfer",
            "scope": "/",
            "top": AUTHZ_PAGE_SIZE,
            "skip": skip,
            "noInheritance": "false",
        })
        page = api(auth, "GET", f"{assignments_url(auth)}?{query}", {"x-uipath-internal-accountid": org_id})
        results = page.get("results") or []
        for assignment in (a for r in results for a in (r.get("roleAssignmentDtos") or [])):
            scope = (assignment.get("scope") or "").lower()
            # A PATCH batch is atomic: one immutable id would fail all of it.
            if not assignment.get("id") or assignment.get("mutable") is False or not scope.startswith(prefix):
                continue
            project_hex = scope[len(prefix):]
            if project_hex:
                found.append((assignment["id"], project_hex, assignment.get("createdOn")))
        skip += len(results)
        if not results or skip >= (page.get("totalCount") or 0):
            return found


def live_projects(auth):
    """(hex ids, names) of every project on the tenant, whoever can see it."""
    org = urllib.parse.quote(auth["UIPATH_ORGANIZATION_NAME"])
    tenant = urllib.parse.quote(auth["UIPATH_TENANT_NAME"])
    body = api(
        auth,
        "GET",
        f"{auth['UIPATH_URL']}/{org}/{tenant}/reinfer_/api/_private/projects",
        {
            "x-uipath-internal-accountid": auth["UIPATH_ORGANIZATION_ID"],
            "x-uipath-internal-tenantid": auth["UIPATH_TENANT_ID"],
        },
    )
    projects = body.get("projects") or []
    return (
        {str(p["id"]).lower() for p in projects if p.get("id")},
        {p["name"] for p in projects if p.get("name")},
    )


def stale_assignments(assignments, live_ids, now):
    """Ids of assignments whose project is gone, older than STALE_AFTER."""
    stale = []
    for assignment_id, project_hex, created_on in assignments:
        created = parse_timestamp(created_on)
        if project_hex not in live_ids and created is not None and now - created > STALE_AFTER:
            stale.append(assignment_id)
    return stale


def purge_dangling_role_assignments(cli_names, dry_run=False):
    """cli_names: projects the CLI listed that are still expected to exist."""
    auth = read_auth()
    if auth is None:
        print("SKIP: no usable .auth file; AuthZ role assignments not purged")
        return
    started = time.monotonic()

    def budget_left():
        return time.monotonic() - started < PURGE_BUDGET_SECONDS

    try:
        # Assignments before projects: a project created in between is then
        # either absent from the assignments or present in the project list.
        assignments = project_role_assignments(auth, budget_left)
        if not assignments:
            print("purge: no Reinfer project-scope role assignments on this tenant")
            return
        if not budget_left():
            raise TimeoutError("budget spent before listing projects")
        live_ids, live_names = live_projects(auth)
    except Exception as e:
        print(f"WARN: AuthZ purge skipped: {e}")
        return

    if not live_ids:
        print("WARN: reinfer listed no projects; AuthZ purge skipped")
        return
    unlisted = sorted(cli_names - live_names)
    if unlisted:
        print(f"WARN: reinfer's project list lacks {len(unlisted)} project(s) the CLI lists "
              f"(e.g. '{unlisted[0]}'); AuthZ purge skipped")
        return

    stale = stale_assignments(assignments, live_ids, datetime.now(timezone.utc))
    print(f"purge: {len(assignments)} project-scope role assignment(s), {len(live_ids)} live project(s), "
          f"{len(stale)} dangling older than {STALE_AFTER}")
    if dry_run:
        print(f"purge: dry run; would delete {stale}")
        return

    deleted = 0
    for index in range(0, len(stale), AUTHZ_DELETE_BATCH):
        if not budget_left():
            print(f"purge: budget spent; {len(stale) - index} left for the next run")
            break
        batch = stale[index:index + AUTHZ_DELETE_BATCH]
        try:
            api(
                auth,
                "PATCH",
                assignments_url(auth),
                {"x-uipath-internal-accountid": auth["UIPATH_ORGANIZATION_ID"]},
                {"roleAssignmentsToAdd": [], "roleAssignmentsToDelete": batch},
            )
            deleted += len(batch)
        except Exception as e:
            print(f"WARN: could not delete {len(batch)} role assignment(s): {e}")
    print(f"OK: purged {deleted} dangling AuthZ role assignment(s)")


def main(dry_run=False):
    projects = list_projects()
    if projects is None:
        return
    stale = stale_projects(projects, datetime.now(timezone.utc))
    print(f"sweep: {len(projects)} project(s) on the tenant, {len(stale)} stale '{PROJECT_PREFIX}*' "
          f"older than {STALE_AFTER}")

    if dry_run:
        print(f"sweep: dry run; would delete {stale}")
    else:
        started = time.monotonic()
        for index, name in enumerate(stale):
            if time.monotonic() - started > DELETE_BUDGET_SECONDS:
                print(f"sweep: delete budget spent; {len(stale) - index} left for the next run")
                break
            delete_project(name)

    cli_names = {p["Name"] for p in projects if p.get("Name")} - set(stale)
    purge_dangling_role_assignments(cli_names, dry_run)


if __name__ == "__main__":
    try:
        main(dry_run="--dry-run" in sys.argv[1:])
    except Exception as e:
        print(f"WARN: sweep aborted: {e}")
    sys.exit(0)
