#!/usr/bin/env python3
"""Seed Test Manager state for the run-package tasks.

Shared by `run_package_ci_smoke` and `run_package_failing_smoke`. Each task
passes its own EVFX- prefix and package on the command line, so the names stay
in the task YAML where fixtures/check-collisions.py sees them.

    seed — check the tenant can run the package (folder, runtime,
           unattended account), upload the
           package from packages/ when the folder feed lacks it, sweep this
           task's stale projects, and create a throwaway project whose key is
           written to project-key.txt.

A tenant that cannot run the package (no folder, no machine with a runtime in
it, no folder member that may run unattended, or no right to upload) exits with TENANT NOT READY on stderr. The pass-rate
gate in smoke-skills.yml drops such a task instead of scoring it as an agent
failure.

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
HERE = os.path.dirname(os.path.abspath(__file__))
SWEEP_AFTER = datetime.timedelta(hours=6)


def log(msg):
    print(f"FIXTURE: {msg}", flush=True)


def call(*args):
    r = subprocess.run([*UIP, *args, "--output", "json"], capture_output=True, text=True)
    out = r.stdout or ""
    try:
        return json.loads(out[out.index("{"):])
    except ValueError:
        return {"Result": "Failure", "Message": (out + (r.stderr or ""))[:300]}


def tenant():
    d = call("login", "status").get("Data") or {}
    return f"{d.get('BaseUrl', '?')} {d.get('Organization', '?')}/{d.get('Tenant', '?')}"


def not_ready(msg):
    print(f"TENANT NOT READY — this is an environment failure, not an agent failure, "
          f"on {tenant()}: {msg} See tests/tasks/uipath-test/fixtures/README.md "
          f"(Run-package fixtures).", file=sys.stderr, flush=True)
    sys.exit(1)


def folder_key(folder):
    rows = call("or", "folders", "list", "-n", folder, "--all").get("Data") or []
    if not rows or not rows[0].get("Key"):
        not_ready(f"no Orchestrator folder '{folder}' is visible to this login.")
    return rows[0]["Key"]


def require_robot(folder, key):
    # Test Manager starts the package's tests as unattended jobs in the folder.
    # Without a machine that has a runtime, they stay Pending until --timeout.
    rows = call("or", "machines", "list", "--folder-key", key, "--all-fields").get("Data") or []
    usable = [m for m in rows
              if (m.get("UnattendedSlots") or 0) > 0 or (m.get("TestAutomationSlots") or 0) > 0]
    if not usable:
        not_ready(f"no machine in '{folder}' has an Unattended or Test Automation runtime, "
                  "so the run can never finish.")
    log(f"runtime on {', '.join(m.get('Name') or '?' for m in usable)}")
    # A runtime needs an account to run the jobs as: a folder member that may
    # hold an unattended session (a robot account, or a user with an
    # unattended robot).
    page, offset = 200, 0
    while True:
        members = call("or", "users", "list-in-folder", "--folder-key", key, "--include-inherited",
                       "--limit", str(page), "--offset", str(offset)).get("Data") or []
        for name in [m.get("UserName") for m in members if m.get("UserName")]:
            rows = call("or", "users", "list", "--username", name, "--all-fields").get("Data") or []
            if any(u.get("UserName") == name and u.get("MayHaveUnattendedSession") for u in rows):
                log(f"unattended account {name}")
                return
        if len(members) < page:
            break
        offset += page
    not_ready(f"no member of '{folder}' may hold an unattended session; add a robot "
              "account to the folder as Automation User.")


def ensure_package(folder, key, package, nupkg):
    def present():
        return call("or", "packages", "versions", package, "--folder-key", key).get("Data")

    if present():
        log(f"package {package} present in '{folder}'")
        return
    path = os.path.join(HERE, "packages", nupkg)
    out = call("or", "packages", "upload", path, "--folder-key", key)
    if out.get("Result") != "Success" or not present():
        not_ready(f"package {package} is not in '{folder}' and uploading {nupkg} failed: "
                  f"{out.get('Message') or out}")
    log(f"uploaded {nupkg} to '{folder}'")


def seed_project(prefix, key_prefix):
    now = datetime.datetime.now(datetime.timezone.utc)
    # A run that died before post_run strands its project. Sweep only projects
    # stamped more than 6 hours ago, so a concurrent run keeps its own.
    for p in call("tm", "project", "list", "--filter", prefix).get("Data") or []:
        name, key = p.get("Name") or "", p.get("ProjectKey")
        if not key or not name.startswith(prefix):
            continue
        try:
            stamp = datetime.datetime.strptime(name[len(prefix):len(prefix) + 15], "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if now - stamp.replace(tzinfo=datetime.timezone.utc) > SWEEP_AFTER:
            call("tm", "project", "delete", "--project-key", key, "--yes")
    key = key_prefix + secrets.token_hex(2).upper()
    name = f"{prefix}{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    out = call("tm", "project", "create", "--name", name, "--project-key", key)
    if out.get("Result") != "Success":
        log(f"PROVISIONING FAILED — could not create {name} ({key}): {out}")
        sys.exit(1)
    with open("project-key.txt", "w") as f:
        f.write(key + "\n")
    log(f"SEEDED project {name} with key {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seed")
    s.add_argument("--folder", required=True)
    s.add_argument("--package", required=True, help="package id, e.g. TestCase_CrossPlatform_VB_Tests")
    s.add_argument("--nupkg", required=True, help="file under _setup/packages/ to upload when missing")
    s.add_argument("--prefix", required=True, help="EVFX- project name prefix this task owns")
    s.add_argument("--key-prefix", required=True, help="4-letter project key prefix")
    a = parser.parse_args()
    key = folder_key(a.folder)
    require_robot(a.folder, key)
    ensure_package(a.folder, key, a.package, a.nupkg)
    seed_project(a.prefix, a.key_prefix)


if __name__ == "__main__":
    main()
