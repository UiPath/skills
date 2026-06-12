#!/usr/bin/env python3
"""Shape check for the Test Manager API-Workflow connector task.

SKELETON: the `shape` mode is fully implemented (connector-agnostic). The
`tenant` mode is a TODO that needs the live-confirmed create/get operation names
and the connection UUID — fill it in after running `uip api-workflow registry
resolve "test manager test case"` and provisioning the `tm-connector-eval`
connection.

Usage: check_testmanager_create_testcase.py [shape|tenant]
Exit 0 = pass, non-zero = fail.
"""
import glob
import json
import os
import sys

CONNECTOR_KEY = "uipath-uipath-testmanager"
TC_NAME = "Connector Eval - API Workflow TC"


def _load_workflow():
    candidates = sorted(glob.glob("Workflow.json") + glob.glob("**/Workflow.json", recursive=True))
    if not candidates:
        print("FAIL: Workflow.json not found")
        sys.exit(1)
    with open(candidates[0], encoding="utf-8") as fh:
        return candidates[0], fh.read(), json.loads(open(candidates[0], encoding="utf-8").read())


def check_shape():
    path, raw, _doc = _load_workflow()
    problems = []
    # 1. References the Test Manager connector.
    if CONNECTOR_KEY not in raw:
        problems.append(f"connectorKey {CONNECTOR_KEY!r} not present in {path}")
    # 2. Uses an Integration Service connector activity (not a raw HTTP fallback).
    if "UiPath.IntSvc" not in raw:
        problems.append("no UiPath.IntSvc connector call found (expected an IntSvc-kind activity)")
    # 3. No unresolved stub placeholders left behind.
    if "<REPLACE_WITH_" in raw:
        problems.append("unresolved stub placeholder (<REPLACE_WITH_...>) left in workflow")
    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        sys.exit(1)
    print(f"OK: Workflow.json calls the {CONNECTOR_KEY} connector via IntSvc with a resolved connection")


def check_tenant():
    # TODO(operation): after `uip api-workflow registry resolve "test manager test case"`,
    # confirm the create + get operation objectNames, then verify the test case
    # named TC_NAME exists via:
    #   uip is resources run <CONNECTOR_KEY> <getObject> --operation <Get/List> \
    #       --connection-id <uuid> --output json
    # and assert TC_NAME is present. Skipped until the operation slug is confirmed.
    print("SKIP: tenant-state check not yet implemented (needs live-confirmed operation slug)")
    sys.exit(0)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "shape"
    (check_tenant if mode == "tenant" else check_shape)()
