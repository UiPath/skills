#!/usr/bin/env python3
"""Subflow: verify subflow structure and that debug reverses 'hello' to 'olleh'."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    read_flow_input_vars,
    run_debug,
)


def _fail(msg):
    sys.exit(f"FAIL: {msg}")


def _check_subflow_structure(project_dir):
    """Validate the subflow internals: nodes, edges, variables, mappings."""
    flows = glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True)
    if not flows:
        _fail("No .flow file found")

    with open(flows[0]) as f:
        flow = json.load(f)

    # Find the core.subflow node
    subflow_node = next(
        (n for n in flow.get("nodes", []) if n.get("type") == "core.subflow"), None
    )
    if not subflow_node:
        _fail(f"No Subflow node found. Types: {[n.get('type') for n in flow.get('nodes', [])]}")

    sid = subflow_node["id"]
    if not subflow_node.get("inputs"):
        _fail(f"Subflow parent node '{sid}' has no inputs defined")

    # Verify the subflows section
    sf = flow.get("subflows", {}).get(sid)
    if not sf:
        _fail(f"No subflows.{sid} section found. Keys: {list(flow.get('subflows', {}).keys())}")

    sf_nodes = sf.get("nodes", [])
    sf_edges = sf.get("edges", [])
    if len(sf_nodes) < 3:
        _fail(f"Subflow needs at least 3 nodes (start, logic, end), found {len(sf_nodes)}")
    if len(sf_edges) < 2:
        _fail(f"Subflow needs at least 2 edges, found {len(sf_edges)}")

    sf_types = [n.get("type", "") for n in sf_nodes]
    if "core.trigger.manual" not in sf_types:
        _fail(f"Subflow missing Start node. Types: {sf_types}")
    if "core.control.end" not in sf_types:
        _fail(f"Subflow missing End node. Types: {sf_types}")

    # Check subflow variables
    sf_globals = sf.get("variables", {}).get("globals", [])
    in_vars = [v for v in sf_globals if v.get("direction") == "in"]
    if not in_vars:
        _fail("Subflow has no input variables (direction: in)")
    for v in in_vars:
        if not v.get("triggerNodeId"):
            _fail(f"Subflow input variable '{v['id']}' missing triggerNodeId")

    out_vars = [v for v in sf_globals if v.get("direction") == "out"]
    if not out_vars:
        _fail("Subflow has no output variables (direction: out)")

    for n in sf_nodes:
        if n.get("type") == "core.control.end" and not n.get("outputs"):
            _fail(f"Subflow End node '{n['id']}' has no output mappings")

    print(f"OK: Subflow '{sid}' structure valid ({len(sf_nodes)} nodes, {len(in_vars)} in, {len(out_vars)} out)")


def main():
    assert_flow_has_node_type(["core.subflow"])

    project_dir = find_project_dir()
    _check_subflow_structure(project_dir)

    in_vars = read_flow_input_vars(project_dir)
    inputs = {in_vars[0]: "hello"} if in_vars else None
    payload = run_debug(inputs=inputs)

    assert_outputs_contain(payload, "olleh")
    print("OK: Subflow node present; 'hello' reversed to 'olleh'")


if __name__ == "__main__":
    main()
