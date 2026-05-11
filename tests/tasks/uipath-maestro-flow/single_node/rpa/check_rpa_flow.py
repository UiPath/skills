#!/usr/bin/env python3
"""ProjectEulerTitle: an RPA-workflow node is wired to return the title."""

from __future__ import annotations

import glob
import json
import sys


def _fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _load_single_flow() -> dict:
    flows = sorted(glob.glob("**/ProjectEulerTitle.flow", recursive=True))
    if not flows:
        _fail("No ProjectEulerTitle.flow found")
    if len(flows) > 1:
        _fail(f"Multiple ProjectEulerTitle.flow files found: {flows}")
    with open(flows[0], encoding="utf-8") as flow_file:
        return json.load(flow_file)


def main() -> None:
    flow = _load_single_flow()
    nodes = flow.get("nodes") or []
    rpa_nodes = [
        node for node in nodes if "uipath.core.rpa-workflow" in node.get("type", "")
    ]
    if len(rpa_nodes) != 1:
        _fail(f"Expected exactly one RPA node, found {len(rpa_nodes)}")

    rpa_node = rpa_nodes[0]
    if (rpa_node.get("inputs") or {}).get("problemId") != 123:
        _fail("RPA node must pass problemId=123")

    bindings_text = json.dumps(flow.get("bindings") or [])
    if "ProjectEuler RPA" not in bindings_text or "RPA Workflow" not in bindings_text:
        _fail("RPA process bindings must reference ProjectEuler RPA.RPA Workflow")

    end_nodes = [node for node in nodes if node.get("type") == "core.control.end"]
    output_sources = json.dumps([node.get("outputs") or {} for node in end_nodes])
    rpa_node_id = rpa_node.get("id")
    if not rpa_node_id:
        _fail("RPA node is missing id")
    expected_source = f"$vars.{rpa_node_id}.output.title"
    if expected_source not in output_sources:
        _fail(f"End node output must map from {expected_source}")

    print("OK: RPA node present; problemId and title output are wired")


if __name__ == "__main__":
    main()
