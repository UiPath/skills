#!/usr/bin/env python3
"""Shared seed for Test Manager connector event-trigger e2e tasks.

Writes seed.json into the sandbox: a unique marker for the record the agent
creates, the TM project key, the trigger under test (operation + object type),
and unique deployment/process names so post_run cleanup can find what the run
deployed even when the agent never wrote result.json. Staged via
sandbox.template_sources and run as ./_setup/seed.py.

Usage: seed.py --operation Created|Updated|Finished --object-type <TM object>
"""
import argparse
import datetime
import json
import os
import sys
import uuid

OPERATIONS = ("Created", "Updated", "Finished")
OBJECT_TYPES = ("Requirement", "TestCase", "TestSet", "TestExecution", "TestCaseLog")
# Records that only change by running a test set: the connector has no create
# or update activity for them, so these tasks drive a runnable fixture.
EXECUTION_DRIVEN = ("TestExecution", "TestCaseLog")


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
        test_set = os.environ.get("TM_EVAL_EXECUTION_TESTSET")
        if not test_set:
            print("FAIL: TM_EVAL_EXECUTION_TESTSET is not set — execution-driven tasks need a runnable automated test set")
            sys.exit(1)
        seed["execution_test_set"] = test_set

    with open("seed.json", "w", encoding="utf-8") as fh:
        json.dump(seed, fh, indent=2)
    print(f"seeded {seed['operation']}/{seed['object_type']}: marker {seed['marker']}, deployment {seed['deployment_name']}")


if __name__ == "__main__":
    main()
