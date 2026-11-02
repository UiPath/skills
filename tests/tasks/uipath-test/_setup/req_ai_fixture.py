#!/usr/bin/env python3
"""Seed and grade Test Manager state for the requirement AI tasks.

Shared by the `requirement_ai_*` tasks in tests/tasks/uipath-test/. Each task
passes its own EVFX- names on the command line, so the names stay in the task
YAML where fixtures/check-collisions.py sees them; this file knows no names.

    seed   — create-if-absent one requirement and the test cases linked to it,
             reset its description, and remove what an earlier run of the task
             produced (test cases the AI created and linked, extra links).
    warm   — wait on the generate job `seed --capture-generate-timeout` saved, so
             the agent's resume is instant; TENANT NOT READY when the backend
             is too slow (run as pre_run legs: coder_eval caps each at 300 s).
    check  — exit 0 when the requirement / test cases are in the asserted state.

`uip` is the CLI on PATH; set UIP_CMD (for example "node /path/to/index.js")
to run against another build.
"""
import argparse
import datetime
import json
import os
import re
import secrets
import shlex
import subprocess
import sys
import time

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


def stamped_project(prefix):
    """Create a per-run project `<prefix><stamp>-<hex>`, sweep orphans stamped
    more than 6 hours ago, and write its key to project-key.txt (the grader's
    check reads it back). AI tasks share a requirement and the AI-created test
    cases it spawns, so concurrent gate runs on one HEALTH requirement corrupt
    each other's counts — a per-run project isolates them."""
    now = datetime.datetime.now(datetime.timezone.utc)
    for p in (data("proj.sweep", "tm", "project", "list", "--filter", prefix,
                   check=False) or []):
        nm, key = p.get("Name") or "", p.get("ProjectKey")
        if not key or not nm.startswith(prefix):
            continue
        try:
            stamp = datetime.datetime.strptime(nm[len(prefix):len(prefix) + 15],
                                               "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if now - stamp.replace(tzinfo=datetime.timezone.utc) > datetime.timedelta(hours=6):
            call("proj.del", "tm", "project", "delete", "--project-key", key,
                 "--yes", check=False)
    key = "EVAI" + secrets.token_hex(2).upper()
    name = f"{prefix}{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"
    call("proj.create", "tm", "project", "create", "--name", name, "--project-key", key)
    with open("project-key.txt", "w", encoding="utf-8") as fh:
        fh.write(key + "\n")
    log(f"stamped project {name} ({key})")
    return key


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


# No requirement has this id, so a caller allowed to use the route gets
# HTTP 404 before any job starts; a caller who is not gets 403.
PROBE_REQUIREMENT_ID = "00000000-0000-4000-8000-0000000000ad"


def require_access(project, verb):
    """Exclude the task, not fail it, when the tenant refuses `verb` outright.

    The AI routes carry their own feature flag, licence policy and AI Trust
    Layer policy, so one tenant can allow `evaluate` and answer 403 to
    `find-obsolete-testcases` (on Cloud, findObsoleteTests needs a Test Cloud
    licence on the user or A4TMasterFFEnabled on the org; the other two check
    that only on AS and dedicated clouds). The pass-rate gate in
    smoke-skills.yml drops a task whose pre_run fails with TENANT NOT READY on
    stderr. The nightly does not and records ERROR until the tenant is fixed.
    """
    _, env = call(f"probe.{verb}", "tm", "requirements", verb, "--project-key", project,
                  "--requirement-id", PROBE_REQUIREMENT_ID, check=False)
    if env.get("ErrorCode") == "permission_denied":
        print("TENANT NOT READY — this is an environment failure, not an agent failure: "
              f"`uip tm requirements {verb}` answers 403 for this login on project "
              f"{project} ({env.get('Message', '')[:160]}). For find-obsolete-testcases "
              "on Cloud, give the eval user a Test Cloud licence or enable "
              "A4TMasterFFEnabled on the org; otherwise enable the route's feature flag "
              "and AI Trust Layer policy for the eval user.",
              file=sys.stderr, flush=True)
        sys.exit(1)
    if (env.get("Data") or {}).get("ActivityId"):
        fail(f"the {verb} probe started a job; PROBE_REQUIREMENT_ID must not exist")


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
    if getattr(a, "stamped_prefix", None):
        a.project = stamped_project(a.stamped_prefix)
    for verb in a.require_access:
        require_access(a.project, verb)
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
        log(f"saved the timed-out output of job {activity} to {out}; run `warm` next")

    log(f"{a.requirement} ready: {rid}, {len(wanted)} linked test case(s)")


def cmd_warm(a):
    """Backend health gate for the job `seed --capture-generate-timeout` saved.

    The saved envelope is the timed-out state the task needs (the agent must
    resume the job by --activity-id). But the agent then has to WAIT for that
    job, and when the AI Trust Layer / LLM gateway is slow the job outruns the
    agent's budget and the run fails on an environment problem, not an agent
    one. So pre-warm the SAME job here (reading a job by id spends no AI
    units): if it finishes, the agent's resume is instant; if it is still
    running when the LAST leg ends, the backend is too slow for this run —
    exclude the task as tenant-not-ready (the pass-rate gate drops a pre_run
    that exits non-zero with TENANT NOT READY on stderr) rather than let it
    fail closed. The total budget is the skill's own single-wait bound
    (`--timeout 540`): a job the agent could have waited out is not a slow
    backend. coder_eval caps each pre_run command at 300 s, so the task runs
    this as two legs of `--timeout 270`, the second with `--last`. Jobs
    usually finish in 1-2 min; a 240 s budget turned merely slow jobs into
    nightly ERRORs."""
    project = a.project
    try:
        with open("project-key.txt", encoding="utf-8") as fh:
            project = fh.read().strip() or project
    except FileNotFoundError:
        pass
    if not project:
        fail("warm: no project key (project-key.txt missing and no --project)")
    try:
        with open(a.saved, encoding="utf-8") as fh:
            env = json.load(fh)
    except (OSError, ValueError) as exc:
        fail(f"warm: cannot read the saved envelope {a.saved}: {exc}")
    activity = activity_id(env)
    if not activity:
        fail(f"warm: {a.saved} names no AI activity")
    try:
        rc, henv = call("backend.health", "tm", "requirements", "generate-testcases",
                        "--project-key", project, "--activity-id", activity,
                        "--wait", "--timeout", str(a.timeout), "--poll-interval", "5",
                        timeout=a.timeout + 20, check=False)
    except subprocess.TimeoutExpired:
        rc, henv = 2, {"ErrorCode": "timeout", "Message": "wait subprocess timed out"}
    timed_out = (rc == 2 or (henv.get("ErrorCode") or "").lower() == "timeout"
                 or "timed out" in (henv.get("Message") or "").lower())
    if timed_out:
        if not a.last:
            log(f"job {activity} still running after {a.timeout}s; the next warm leg continues")
            return 0
        print("TENANT NOT READY — the AI generate backend did not finish job "
              f"{activity} within the pre-warm budget on project {project}; the AI "
              "Trust Layer / LLM gateway is too slow for this run. Not an agent "
              "failure.", file=sys.stderr, flush=True)
        sys.exit(1)
    if rc != 0:
        # A 5xx while polling (ErrorCode server_error) is the backend
        # wobbling, not a fixture bug: same exclusion as a slow job.
        if (henv.get("ErrorCode") or "").lower() == "server_error":
            print("TENANT NOT READY — the AI generate backend answered a server "
                  f"error while polling job {activity} on project {project}: "
                  f"{(henv.get('Message') or '')[:160]}. Not an agent failure.",
                  file=sys.stderr, flush=True)
            sys.exit(1)
        fail(f"backend.health on job {activity} failed (rc={rc}): "
             f"{json.dumps(henv)[:300]}")
    log(f"job {activity} finished; the agent's resume will be instant")
    return 0


def cmd_check(a):
    problems = []
    # Seed may have put the fixture in a per-run project; use it if present.
    try:
        with open("project-key.txt", encoding="utf-8") as fh:
            a.project = fh.read().strip() or a.project
    except FileNotFoundError:
        pass
    req = find_requirement(a.project, a.requirement)
    if not req:
        print(f"CHECK: requirement {a.requirement} not found")
        return 1
    rid = req["Id"]
    links = linked_ids(a.project, rid)
    # Links the agent just created are eventually consistent; when a count is
    # expected, retry until it settles so a stale read right after create does
    # not false-fail (fail-safe: a genuinely wrong count still fails after the
    # retries). The AI label can lag the link too, so re-read both together.
    generated = ai_created(a.project) if a.links_ai_created else {}
    if a.links is not None:
        for _ in range(6):
            if len(links) == a.links and (not a.links_ai_created
                                          or all(t in generated for t in links)):
                break
            time.sleep(3)
            links = linked_ids(a.project, rid)
            generated = ai_created(a.project) if a.links_ai_created else {}
    print(f"CHECK: {a.requirement} has {len(links)} linked test case(s)")

    if a.links is not None and len(links) != a.links:
        problems.append(f"expected {a.links} linked test case(s), found {len(links)}")
    if a.links_ai_created:
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
        # The agent's `requirements update` is eventually consistent; right
        # after a slow AI-backed apply the first read can still show the seeded
        # text. Retry before concluding nothing changed (fail-safe: a genuinely
        # un-applied suggestion still reads as base after the retries).
        for _ in range(6):
            if desc.strip() != base:
                break
            time.sleep(3)
            desc = (find_requirement(a.project, a.requirement) or {}).get("Description") or ""
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
    s.add_argument("--require-access", action="append", default=[], metavar="VERB",
                   help="exit TENANT NOT READY when this AI verb answers 403 (repeatable)")
    s.add_argument("--capture-generate-timeout", metavar="OUT",
                   help="start generate-testcases with a 3 s wait and save its output "
                        "(then pre-warm that job with `warm`)")
    s.add_argument("--stamped-prefix", metavar="PREFIX",
                   help="seed into a fresh per-run project <PREFIX><stamp>-<hex> "
                        "(key written to project-key.txt) instead of --project, so "
                        "concurrent gate runs do not share the requirement")

    w = sub.add_parser("warm")
    w.add_argument("--saved", required=True, metavar="FILE",
                   help="the envelope seed --capture-generate-timeout wrote")
    w.add_argument("--project", help="fallback when project-key.txt is absent")
    w.add_argument("--timeout", type=int, default=270, metavar="SECONDS",
                   help="this leg's wait (keep the pre_run command under 300 s)")
    w.add_argument("--last", action="store_true",
                   help="a job still running at the end of this leg is TENANT NOT READY")

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
    if a.cmd == "warm":
        return cmd_warm(a)
    return cmd_check(a)


if __name__ == "__main__":
    sys.exit(main())
