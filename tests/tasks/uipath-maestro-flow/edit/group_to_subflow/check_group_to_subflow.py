#!/usr/bin/env python3
"""Group-to-subflow check: fetchAndFormat subflow exists and flow debug produces output."""

import json
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_check import (  # noqa: E402
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


def _assert_subflow_node_exists(flow: dict) -> None:
    """The main flow must have a node with id 'fetchAndFormat' and type 'core.subflow'."""
    for node in flow.get("nodes") or []:
        if node.get("id") == "fetchAndFormat" and node.get("type") == "core.subflow":
            return
    sys.exit("FAIL: no 'fetchAndFormat' node of type 'core.subflow' in main flow")


def _assert_subflow_definition_exists(flow: dict) -> None:
    """The top-level 'subflows' object must contain a 'fetchAndFormat' key."""
    subflows = flow.get("subflows") or {}
    if "fetchAndFormat" not in subflows:
        sys.exit("FAIL: 'subflows.fetchAndFormat' definition missing from flow file")


def _assert_main_flow_nodes_removed(flow: dict) -> None:
    """getWeather and formatSummary must NOT be in the main flow's nodes."""
    main_ids = {n.get("id") for n in flow.get("nodes") or []}
    for removed in ("getWeather", "formatSummary"):
        if removed in main_ids:
            sys.exit(f"FAIL: '{removed}' should have been moved to subflow but is still in main flow nodes")


def main():
    flow = _load_flow()

    # Structural checks
    _assert_subflow_node_exists(flow)
    _assert_subflow_definition_exists(flow)
    _assert_main_flow_nodes_removed(flow)

    # Runtime check
    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ["nice day", "bring a jacket"], require_all=False)
    print("OK: fetchAndFormat subflow present, old nodes removed, debug output valid")


if __name__ == "__main__":
    main()
