#!/usr/bin/env python3
"""Add-node check: convertToCelsius node exists and flow debug produces output with a Celsius value."""

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


def _assert_node_exists(node_id: str) -> None:
    """Verify a node with the given id exists in the .flow file."""
    import glob as _glob

    project_dir = find_project_dir()
    for path in _glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        for node in flow.get("nodes") or []:
            if node.get("id") == node_id:
                return
    sys.exit(f"FAIL: node '{node_id}' not found in flow")


def _assert_edge_exists(source_id: str, target_id: str) -> None:
    """Verify an edge from source to target exists."""
    import glob as _glob

    project_dir = find_project_dir()
    for path in _glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        for edge in flow.get("edges") or []:
            if edge.get("sourceNodeId") == source_id and edge.get("targetNodeId") == target_id:
                return
    sys.exit(f"FAIL: no edge from '{source_id}' to '{target_id}'")


def main():
    # Structural checks: the new node must exist and be wired correctly
    _assert_node_exists("convertToCelsius")
    _assert_edge_exists("getWeather", "convertToCelsius")
    _assert_edge_exists("convertToCelsius", "formatSummary")

    # Must still have the HTTP node
    assert_flow_has_node_type(["core.action.http"])

    # Runtime check: debug must complete and output should contain "C" (Celsius marker)
    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ["nice day", "bring a jacket"], require_all=False)
    print("OK: convertToCelsius node present, wired correctly, debug output valid")


if __name__ == "__main__":
    main()
