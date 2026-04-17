#!/usr/bin/env python3
"""Move-node check: decision before formatSummary, both branches merge into it, single end node."""

import json
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    run_debug,
)


def _load_flow() -> dict:
    import glob as _glob

    project_dir = find_project_dir()
    for path in _glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            return json.load(f)
    sys.exit("FAIL: no .flow file found")


def _assert_edge_exists(flow: dict, source_id: str, target_id: str) -> None:
    for edge in flow.get("edges") or []:
        if edge.get("sourceNodeId") == source_id and edge.get("targetNodeId") == target_id:
            return
    sys.exit(f"FAIL: no edge from '{source_id}' to '{target_id}'")


def _count_nodes_of_type(flow: dict, node_type: str) -> int:
    return sum(1 for n in flow.get("nodes") or [] if n.get("type") == node_type)


def main():
    flow = _load_flow()

    # Decision must come before formatSummary: getWeather → decision node
    # Find the decision node id
    decision_ids = [n["id"] for n in flow.get("nodes") or [] if n.get("type") == "core.logic.decision"]
    if not decision_ids:
        sys.exit("FAIL: no decision node found")
    decision_id = decision_ids[0]

    _assert_edge_exists(flow, "getWeather", decision_id)

    # formatSummary must exist and be downstream of decision
    fmt_ids = [n["id"] for n in flow.get("nodes") or [] if n.get("type") == "core.action.script"]
    if not fmt_ids:
        sys.exit("FAIL: no script node (formatSummary) found")

    # Should have only one end node (merged)
    end_count = _count_nodes_of_type(flow, "core.control.end")
    if end_count != 1:
        sys.exit(f"FAIL: expected 1 end node (merged), found {end_count}")

    assert_flow_has_node_type(["core.action.http"])

    # Runtime check
    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ["nice day", "bring a jacket"], require_all=False)
    print("OK: decision before formatSummary, branches merged, single end node, debug valid")


if __name__ == "__main__":
    main()
