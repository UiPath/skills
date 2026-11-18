#!/usr/bin/env python3
"""Tenant gate for the `defect_*` tasks in tests/tasks/uipath-test/.

    probe  — raise one defect in a throwaway project and delete the project.
             Exits TENANT NOT READY (stderr, exit 1) only when Test Manager
             answers 403 to `defects create`; every other outcome exits 0.

Why a real create: Automation Suite answers 403 `permission_denied` to
`uip tm defects create` for the eval login while every other Test Manager
verb works, so the agent reaches that command and the task records a FAILURE
that no skill change can fix. Raising one defect before the agent starts is the
only check known to reproduce it. The PR smoke gate (smoke-skills.yml) drops a
task whose pre_run fails with TENANT NOT READY on stderr; the nightly records
ERROR instead of FAILURE.

The probe never turns a healthy tenant red: a step that fails for any other
reason is logged and the task runs as before.

This file knows no names: the task passes its own EVFX- prefix, so the name
stays in the task YAML where fixtures/check-collisions.py sees it. The project
is named `<prefix><YYYYMMDD-HHMMSS>-probe<hex>`, the stamp layout the tasks'
own orphan sweeps already parse, so a probe a crashed run strands is removed
by the owning task's next sweep.

`uip` is the CLI on PATH; set UIP_CMD (for example "node /path/to/index.js")
to run against another build.
"""
import argparse
import datetime
import json
import os
import secrets
import shlex
import subprocess
import sys

UIP = shlex.split(os.environ.get("UIP_CMD", "uip"))


def log(msg):
    print(f"FIXTURE: {msg}", flush=True)


def call(label, *args, timeout=150):
    """Run one uip command; return the parsed JSON envelope ({} when unreadable)."""
    try:
        r = subprocess.run([*UIP, *args, "--output", "json"],
                           capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError) as exc:
        print(f"FIXTURE[{label}] did not finish: {exc}", flush=True)
        return {}
    out = (r.stdout or "").strip()
    print(f"FIXTURE[{label}] rc={r.returncode} out={out[:200]}", flush=True)
    try:
        return json.loads(out[out.index("{"):])
    except ValueError:
        return {}


class Skip(Exception):
    """A probe step failed for a reason other than the 403 under test."""


def created(project, kind, name):
    call(f"{kind}.create", "tm", kind, "create", "--project-key", project, "--name", name)
    for row in call(f"{kind}.find", "tm", kind, "list", "--project-key", project,
                    "--filter", name).get("Data") or []:
        if row.get("Name") == name:
            return row
    raise Skip(f"could not create {name}")


def raise_defect(project, prefix):
    """Seed one Failed manual result and raise a defect on it; return the envelope."""
    ts = created(project, "testsets", f"{prefix}PROBE-SET")
    tc = created(project, "testcases", f"{prefix}PROBE-TC1")
    call("set.add", "tm", "testcases", "add", "--test-set-key", ts["TestSetKey"],
         "--test-case-keys", tc["TestCaseKey"])
    eid = (call("run", "tm", "testsets", "run", "--test-set-key", ts["TestSetKey"],
                "--execution-type", "manual").get("Data") or {}).get("ExecutionId")
    if not eid:
        raise Skip("could not start a manual execution")
    call("finish", "tm", "testcaselog", "finish", "--project-key", project,
         "--execution-id", eid, "--test-case-id", tc["Id"], "--result", "Failed",
         "--has-error", "true", "--executed-by", "eval-fixture@uipath.com")
    return call("defect.create", "tm", "defects", "create", "--project-key", project,
                "--execution-id", eid, "--test-case-id", tc["Id"])


def cmd_probe(a):
    now = datetime.datetime.now(datetime.timezone.utc)
    key = a.key_prefix + secrets.token_hex(2).upper()
    name = f"{a.stamped_prefix}{now.strftime('%Y%m%d-%H%M%S')}-probe{secrets.token_hex(3)}"
    if call("project.create", "tm", "project", "create", "--name", name,
            "--project-key", key).get("Result") != "Success":
        log(f"probe skipped: could not create project {name} ({key})")
        return 0
    try:
        env = raise_defect(key, a.stamped_prefix)
    except Skip as exc:
        log(f"probe skipped: {exc}")
        return 0
    finally:
        call("project.delete", "tm", "project", "delete", "--project-key", key, "--yes")
    if env.get("ErrorCode") == "permission_denied":
        print("TENANT NOT READY — this is an environment failure, not an agent failure: "
              f"`uip tm defects create` answers 403 for this login "
              f"({(env.get('Message') or '')[:160]}). Grant the eval login the Test "
              "Manager defect permission on this tenant (on Automation Suite the user "
              "login is refused although the project role allows defects).",
              file=sys.stderr, flush=True)
        return 1
    log(f"defects create is allowed on this tenant (probe project {key} removed)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("probe", help="exit TENANT NOT READY when `defects create` answers 403")
    p.add_argument("--stamped-prefix", required=True,
                   help="the task's own EVFX- project prefix, e.g. EVFX-DEFECT-")
    p.add_argument("--key-prefix", default="EVDP",
                   help="first 4 characters of the throwaway project key")
    p.set_defaults(fn=cmd_probe)
    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
