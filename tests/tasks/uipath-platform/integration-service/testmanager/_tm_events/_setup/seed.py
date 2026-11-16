#!/usr/bin/env python3
"""Shared seed for Test Manager connector event-trigger e2e tasks.

Writes seed.json into the sandbox: a unique marker for the record the agent
creates, the TM project key, the trigger under test (operation + object type),
and unique deployment/process names so post_run cleanup can find what the run
deployed even when the agent never wrote result.json. Staged via
sandbox.template_sources and run as ./_setup/seed.py.

Execution-driven tasks (TestExecution, TestCaseLog) get a test set of their own:
the fixture in TM_EVAL_EXECUTION_TESTSET is cloned under a marker-named copy, so
the execution this run fires is the only one that can carry the copy's id. Every
deployed workflow sees the whole project's executions; without a per-run copy, a
concurrent run executing the same fixture would satisfy this run's grader.

Usage: seed.py --operation Created|Updated|Finished --object-type <TM object>
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import uuid
from typing import NoReturn

OPERATIONS = ("Created", "Updated", "Finished")
OBJECT_TYPES = ("Requirement", "TestCase", "TestSet", "TestExecution", "TestCaseLog")
# Records that only change by running a test set: the connector has no create
# or update activity for them, so these tasks drive a runnable fixture.
EXECUTION_DRIVEN = ("TestExecution", "TestCaseLog")
# subprocess cannot run the Windows uip.cmd shim by bare name; resolve it first.
UIP = shutil.which("uip") or "uip"


def fail(msg) -> NoReturn:
    print(f"FAIL: {msg}")
    sys.exit(1)


def run_uip(*args, timeout=120):
    try:
        proc = subprocess.run([UIP, *args, "--output", "json"], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"`uip {' '.join(args[:3])}` did not complete: {exc}")
    try:
        envelope = json.loads(proc.stdout or "{}")
    except ValueError:
        envelope = {}
    if proc.returncode != 0:
        fail(f"`uip {' '.join(args[:3])}` exited {proc.returncode}: {(proc.stdout or proc.stderr)[:400]}")
    return envelope.get("Data", envelope) if isinstance(envelope, dict) else envelope


def get_ci(obj, key):
    if not isinstance(obj, dict):
        return None
    return next((v for k, v in obj.items() if k.lower() == key.lower()), None)


def clone_test_set(fixture, marker):
    """Clone the fixture under a marker name and point the copy at the fixture's runtime."""
    name = f"{marker}-run"
    data = run_uip("tm", "testsets", "clone", "--test-set-key", fixture, "--new-name", name, timeout=150)
    key, set_id = get_ci(data, "TestSetKey"), get_ci(data, "Id")
    if not key or not set_id or str(get_ci(data, "Result") or "").lower() != "cloned":
        fail(f"cloning test set {fixture} did not return a usable copy: {json.dumps(data)[:400]}")
    # The clone copies test cases but not folder or robot; set them when the tenant names them.
    folder = os.environ.get("TM_EVAL_EXECUTION_FOLDER")
    if folder:
        run_uip("tm", "testsets", "set-folder", "--test-set-key", key, "--folder-path", folder)
    robot = os.environ.get("TM_EVAL_EXECUTION_ROBOT")
    if robot:
        run_uip("tm", "testsets", "set-robot", "--test-set-key", key, "--robot-name", robot)
    return {"execution_test_set": key, "execution_test_set_id": set_id,
            "execution_test_set_name": name, "fixture_test_set": fixture}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--operation", required=True, choices=OPERATIONS)
    parser.add_argument("--object-type", required=True, choices=OBJECT_TYPES)
    args = parser.parse_args()

    suffix = uuid.uuid4().hex[:8]
    seed = {
        "marker": f"DataEval-{suffix}",
        "project_key": os.environ.get("TM_EVAL_PROJECT_KEY", "HEALTH"),
        "operation": args.operation,
        "object_type": args.object_type,
        "deployment_name": f"TmTrigger-{args.operation}-{args.object_type}-{suffix}",
        "process_name": f"TmTrigger{args.operation}{args.object_type}{suffix}",
        "started_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if args.operation == "Updated" and args.object_type not in EXECUTION_DRIVEN:
        seed["updated_description"] = f"{seed['marker']}-updated"
    if args.object_type in EXECUTION_DRIVEN:
        fixture = os.environ.get("TM_EVAL_EXECUTION_TESTSET")
        if not fixture:
            fail("TM_EVAL_EXECUTION_TESTSET is not set — execution-driven tasks need a runnable automated test set")
        # Write seed.json first so cleanup can still find a copy left by a failed setup step.
        with open("seed.json", "w", encoding="utf-8") as fh:
            json.dump(seed, fh, indent=2)
        seed.update(clone_test_set(fixture, seed["marker"]))

    with open("seed.json", "w", encoding="utf-8") as fh:
        json.dump(seed, fh, indent=2)
    print(f"seeded {seed['operation']}/{seed['object_type']}: marker {seed['marker']}, deployment {seed['deployment_name']}"
          + (f", test set {seed['execution_test_set']}" if "execution_test_set" in seed else ""))


if __name__ == "__main__":
    main()
