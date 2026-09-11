"""Verify on the TENANT that the named document — and only it — was deleted.

The seeded project holds three invoices; a run that resolved both the title and
the filename leaves two behind.

Read from the tenant, not from a file the agent saved: `mocks/calls.log` records
invocations before the CLI runs, so a `documents delete` that 404'd is logged
exactly like one that succeeded.

The ProjectName is recovered from `projects list` by seed.json's run id — the
slug is deliberately absent from the sandbox.
"""
import json
import os
import subprocess
import sys
import time

EXPECTED_PRESENT = {"csi_tower_invoice.png", "hp_tax_invoice.png"}
EXPECTED_ABSENT = "york_solutions_invoice.png"


def real_cli_env():
    """PATH without the mock dir, so these calls stay out of calls.log.

    `mock_path_dirs` prepends `<sandbox>/mocks` for run_command criteria too, and
    the wrapper there logs every invocation — which the regex criteria grade.
    """
    env = dict(os.environ)
    mocks = os.path.join(os.getcwd(), "mocks")
    env["PATH"] = os.pathsep.join(
        d for d in env.get("PATH", "").split(os.pathsep)
        if os.path.abspath(d or ".") != mocks
    )
    return env


def uip(*args):
    """Parsed envelope, or (None, reason). Never raises: a broken call must read
    as a criterion failure with a reason, not a traceback."""
    try:
        proc = subprocess.run(["uip", *args, "--output", "json"],
                              capture_output=True, text=True, timeout=30, env=real_cli_env())
    except Exception as exc:
        return None, "could not invoke uip: %s" % exc
    if proc.returncode != 0:
        return None, (proc.stderr or proc.stdout or "")[:300]
    try:
        return json.loads(proc.stdout), None
    except ValueError:
        return None, proc.stdout[:300]


def project_name(run_id):
    listed, err = uip("ixp", "projects", "list", "-l", "10000")
    if listed is None:
        return None, "projects list failed: %s" % err
    projects = (listed.get("Data") or {}).get("Projects") or []
    matches = [p["Name"] for p in projects if run_id in (p.get("Name") or "")]
    if len(matches) != 1:
        return None, "%d projects carry run id %s" % (len(matches), run_id)
    return matches[0], None


def main():
    try:
        run_id = json.load(open("seed.json", encoding="utf-8")).get("uuid8", "")
    except (ValueError, OSError) as exc:
        print("FAIL - seed.json unreadable (%s)" % exc)
        return 1
    if not run_id:
        print("FAIL - seed.json carries no uuid8")
        return 1

    name, err = project_name(run_id)
    if not name:
        print("FAIL - could not resolve the seeded project: %s" % err)
        return 1

    for attempt in range(3):
        listed, err = uip("ixp", "documents", "list", name, "-l", "100")
        if listed is None:
            print("FAIL - documents list on %s failed: %s" % (name, err))
            return 1
        found = {d.get("Filename") for d in ((listed.get("Data") or {}).get("Documents") or [])}
        if EXPECTED_ABSENT not in found and EXPECTED_PRESENT <= found:
            print("PASS - %s holds %s" % (name, sorted(found)))
            return 0
        if attempt < 2:
            time.sleep(3)

    if EXPECTED_ABSENT in found:
        print("FAIL - %s is still in %s" % (EXPECTED_ABSENT, name))
    missing = EXPECTED_PRESENT - found
    if missing:
        print("FAIL - deleted more than asked: %s no longer in %s" % (sorted(missing), name))
    return 1


sys.exit(main())
