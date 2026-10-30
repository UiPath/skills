#!/usr/bin/env python3
"""Terminate: verify parallel Terminate + Delay branches and that terminate stops the flow."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from _shared.flow_check import (  # noqa: E402
    _get_ci,
    assert_flow_has_node_type,
    find_project_dir,
    run_debug,
)
from _shared.flow_graph import FlowGraph  # noqa: E402


def _check_parallel_branches(project_dir):
    """Verify 2+ branches leave the trigger node, directly or through a merge fork."""
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        sys.exit("FAIL: No .flow file found")

    with open(flows[0]) as f:
        flow = json.load(f)

    graph = FlowGraph(flow)
    trigger_ids = {n["id"] for n in flow.get("nodes", []) if "trigger" in n.get("type", "")}
    outgoing = [e for t in trigger_ids for e in graph.fan_out(t)]
    if len(outgoing) < 2:
        sys.exit(f"FAIL: Expected 2+ parallel branches from trigger, found {len(outgoing)}")

    print("OK: Parallel branches from trigger verified")


def main():
    assert_flow_has_node_type(["core.logic.terminate", "core.logic.delay"])

    project_dir = find_project_dir()
    _check_parallel_branches(project_dir)

    payload = run_debug()

    # Verify the terminate node actually killed the delay branch. Read the
    # runtime payload case-insensitively so a CLI that PascalCases --output json
    # keys (PR #2266) does not make `elementExecutions` unreadable → empty.
    executions = _get_ci(payload, "elementExecutions", "ElementExecutions") or []
    terminated = [e for e in executions if _get_ci(e, "status", "Status") == "Terminated"]
    if not terminated:
        statuses = [(_get_ci(e, "elementId", "ElementId"), _get_ci(e, "status", "Status")) for e in executions]
        sys.exit(f"FAIL: No element was Terminated — terminate node didn't kill the delay branch. Statuses: {statuses}")

    print(f"OK: Terminate + Delay nodes present; {len(terminated)} element(s) terminated")


if __name__ == "__main__":
    main()
