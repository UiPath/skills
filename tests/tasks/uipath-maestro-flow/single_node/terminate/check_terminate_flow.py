#!/usr/bin/env python3
"""Terminate: verify parallel Terminate + Delay branches and that terminate stops the flow."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    find_project_dir,
    run_debug,
)


def _check_parallel_branches(project_dir):
    """Verify 2+ edges leave the trigger node (parallel branches)."""
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit("FAIL: No .flow file found")

    with open(flows[0]) as f:
        flow = json.load(f)

    edges = flow.get("edges", [])
    trigger_ids = {n["id"] for n in flow.get("nodes", []) if "trigger" in n.get("type", "")}
    outgoing = [e for e in edges if e.get("sourceNodeId") in trigger_ids]
    if len(outgoing) < 2:
        sys.exit(f"FAIL: Expected 2+ edges from trigger for parallel branches, found {len(outgoing)}")

    print("OK: Parallel branches from trigger verified")


def main():
    assert_flow_has_node_type(["core.logic.terminate", "core.logic.delay"])

    project_dir = find_project_dir()
    _check_parallel_branches(project_dir)

    payload = run_debug()

    # Verify the terminate node actually killed the delay branch
    executions = payload.get("elementExecutions") or []
    terminated = [e for e in executions if e.get("status") == "Terminated"]
    if not terminated:
        statuses = [(e.get("elementId"), e.get("status")) for e in executions]
        sys.exit(f"FAIL: No element was Terminated — terminate node didn't kill the delay branch. Statuses: {statuses}")

    print(f"OK: Terminate + Delay nodes present; {len(terminated)} element(s) terminated")


if __name__ == "__main__":
    main()
