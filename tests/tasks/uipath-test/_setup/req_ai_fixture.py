#!/usr/bin/env python3
"""Seed and grade Test Manager state for the requirement AI tasks.

Shared by the `requirement_ai_*` tasks in tests/tasks/uipath-test/. Each task
passes its own EVFX- names on the command line, so the names stay in the task
YAML where fixtures/check-collisions.py sees them; this file knows no names.

    seed   — create-if-absent one requirement and the test cases linked to it,
             reset its description, and remove what an earlier run of the task
             produced (test cases the AI created and linked, extra links).
    check  — exit 0 when the requirement / test cases are in the asserted state.

`uip` is the CLI on PATH; set UIP_CMD (for example "node /path/to/index.js")
to run against another build.
"""
import argparse
import json
import os
import re
import shlex
import subprocess
import sys

AI_LABEL = "autopilot-generated"
UIP = shlex.split(os.environ.get("UIP_CMD", "uip"))


def log(msg):
    print(f"FIXTURE: {msg}", flush=True)


def fail(msg):
    log(f"PROVISIONING FAILED - {msg}")
    sys.exit(1)


def call(label, *args, timeout=180, check=True):
    """Run one uip command; return (exit code, parsed JSON envelope)."""
    r = subprocess.run([*UIP, *args, "--output", "json"],
                       capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "").strip()
    print(f"FIXTURE[{label}] rc={r.returncode} out={out[:200]}", flush=True)
    try:
        env = json.loads(out[out.index("{"):])
    except ValueError:
        env = {}
    if check and (r.returncode != 0 or env.get("Result") != "Success"):
        fail(f"{label} failed (rc={r.returncode})")
    return r.returncode, env


def data(label, *args, **kw):
    return call(label, *args, **kw)[1].get("Data")


def find_requirement(project, name):
    rows = data("req.find", "tm", "requirements", "list", "--project-key", project,
                "--filter", name, "--limit", "100") or []
    hits = [r for r in rows if r.get("Name") == name]
    if len(hits) > 1:
        fail(f"{len(hits)} requirements named {name}; delete the extras by hand")
    return hits[0] if hits else None


def find_testcase(project, name):
    rows = data("tc.find", "tm", "testcases", "list", "--project-key", project,
                "--filter", name) or []
    hits = [t for t in rows if t.get("Name") == name]
    return hits[0] if hits else None


def linked_ids(project, req_id):
    d = data("req.links", "tm", "requirements", "list-testcase-ids",
             "--project-key", project, "--requirement-id", req_id) or {}
    return [i.lower() for i in d.get("TestCaseIds") or []]


def ai_created(project):
    """Id -> row of every test case carrying the label the AI's --create sets."""
    rows = data("tc.ai", "tm", "testcases", "list", "--project-key", project,
                "--labels", AI_LABEL) or []
    return {t["Id"].lower(): t for t in rows if t.get("Id")}


def activity_id(env):
    """A start returns Data.ActivityId; a timed-out wait names the job only in
    Message ("AI activity '<id>' polling timed out ...")."""
    found = (env.get("Data") or {}).get("ActivityId")
    if not found:
        m = re.search(r"AI activity '([0-9a-fA-F-]{36})'", env.get("Message") or "")
        found = m and m.group(1)
    return found


def ensure_requirement(project, name, description):
    """The requirement, with exactly `description` (None = no description)."""
    req = find_requirement(project, name)
    current = (req or {}).get("Description") or ""
    if req and description is None and current:
        # An empty description cannot be written back; start over instead.
        call("req.delete", "tm", "requirements", "delete", "--project-key", project,
             "--requirement-ids", req["Id"], "--yes")
        req = None
    if not req:
        args = ["tm", "requirements", "create", "--project-key", project, "--name", name]
        if description is not None:
            args += ["--description", description]
        call("req.create", *args)
        req = find_requirement(project, name)
        if not req:
            fail(f"could not create or find requirement {name}")
    elif description is not None and current != description:
        call("req.reset", "tm", "requirements", "update", "--project-key", project,
             "--requirement-id", req["Id"], "--description", description)
    return req


def ensure_testcase(project, name, description):
    tc = find_testcase(project, name)
    if not tc:
        call("tc.create", "tm", "testcases", "create", "--project-key", project,
             "--name", name, "--description", description)
        tc = find_testcase(project, name)
        if not tc:
            fail(f"could not create or find test case {name}")
    return tc


def cmd_seed(a):
    req = ensure_requirement(a.project, a.requirement,
                             None if a.no_description else a.description)
    rid = req["Id"]

    wanted = {}
    for spec in a.case:
        name, _, desc = spec.partition("=")
        wanted[ensure_testcase(a.project, name, desc or name)["Id"].lower()] = name

    linked = linked_ids(a.project, rid)
    generated = ai_created(a.project) if linked else {}
    # Scratch from an earlier run: what the AI created for this requirement
    # is deleted, anything else linked by hand is only unlinked.
    for tid in linked:
        if tid in wanted:
            continue
        row = generated.get(tid)
        if row:
            call("tc.purge", "tm", "testcases", "delete", "--project-key", a.project,
                 "--test-case-key", row["TestCaseKey"], "--yes")
    extra = [t for t in linked_ids(a.project, rid) if t not in wanted]
    if extra:
        call("req.unlink", "tm", "requirements", "testcases", "--project-key", a.project,
             "--requirement-id", rid, "--remove-testcase-ids", *extra)
    missing = [t for t in wanted if t not in linked]
    if missing:
        call("req.link", "tm", "requirements", "testcases", "--project-key", a.project,
             "--requirement-id", rid, "--add-testcase-ids", *missing)
    if sorted(linked_ids(a.project, rid)) != sorted(wanted):
        fail(f"{a.requirement} links do not match the {len(wanted)} seeded test case(s)")

    out = a.capture_generate_timeout
    if out:
        # Exit 2 (timed out) is the state the task needs; only a missing
        # ActivityId means the job never started.
        _, env = call("capture.generate", "tm", "requirements", "generate-testcases",
                      "--project-key", a.project, "--requirement-id", rid,
                      "--wait", "--timeout", "3", "--poll-interval", "1", check=False)
        activity = activity_id(env)
        if not activity:
            fail(f"generate-testcases started no job: {json.dumps(env)[:300]}")
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(env, fh, indent=2)
        log(f"saved the timed-out output of job {activity} to {out}")

    log(f"{a.requirement} ready: {rid}, {len(wanted)} linked test case(s)")


def cmd_check(a):
    problems = []
    req = find_requirement(a.project, a.requirement)
    if not req:
        print(f"CHECK: requirement {a.requirement} not found")
        return 1
    rid = req["Id"]
    links = linked_ids(a.project, rid)
    print(f"CHECK: {a.requirement} has {len(links)} linked test case(s)")

    if a.links is not None and len(links) != a.links:
        problems.append(f"expected {a.links} linked test case(s), found {len(links)}")
    if a.links_ai_created:
        generated = ai_created(a.project)
        unlabelled = [t for t in links if t not in generated]
        if unlabelled:
            problems.append(f"{len(unlabelled)} linked test case(s) lack the {AI_LABEL} label")

    if a.exist_count is not None:
        prefix, _, want = a.exist_count.rpartition("=")
        rows = data("tc.count", "tm", "testcases", "list", "--project-key", a.project,
                    "--filter", prefix) or []
        have = sum(1 for t in rows if (t.get("Name") or "").startswith(prefix))
        print(f"CHECK: {have} test case(s) named {prefix}*")
        if have != int(want):
            problems.append(f"expected {want} test case(s) named {prefix}*, found {have}")

    desc = req.get("Description") or ""
    if a.description_empty and desc.strip():
        problems.append("the requirement's description was changed")
    if a.description_extends is not None:
        base = a.description_extends.strip()
        if desc.strip() == base:
            problems.append("the requirement's description was not changed")
        elif not desc.strip().startswith(base):
            problems.append("the seeded description was replaced instead of extended")

    for p in problems:
        print(f"CHECK FAILED: {p}")
    return 1 if problems else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("seed")
    s.add_argument("--project", required=True)
    s.add_argument("--requirement", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--description")
    g.add_argument("--no-description", action="store_true")
    s.add_argument("--case", action="append", default=[], metavar="NAME=DESCRIPTION",
                   help="a test case to create-if-absent and link (repeatable)")
    s.add_argument("--capture-generate-timeout", metavar="OUT",
                   help="start generate-testcases with a 3 s wait and save its output")

    c = sub.add_parser("check")
    c.add_argument("--project", required=True)
    c.add_argument("--requirement", required=True)
    c.add_argument("--links", type=int)
    c.add_argument("--links-ai-created", action="store_true")
    c.add_argument("--exist-count", metavar="NAME_PREFIX=N")
    c.add_argument("--description-empty", action="store_true")
    c.add_argument("--description-extends", metavar="TEXT",
                   help="the description must start with TEXT and add to it")

    a = ap.parse_args()
    if a.cmd == "seed":
        cmd_seed(a)
        return 0
    return cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
