#!/usr/bin/env python3
"""Parallel merge: assert a merge node synchronizes two parallel HTTP branches."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_flow_has_node_type,
    assert_outputs_contain,
    find_project_dir,
    run_debug,
)


def _load_flow(project_dir: str) -> dict:
    flows = glob.glob(os.path.join(project_dir, "*.flow"))
    if not flows:
        sys.exit(f"FAIL: No .flow file found in {project_dir}")
    with open(flows[0]) as f:
        return json.load(f)


def main():
    assert_flow_has_node_type(["core.logic.merge"])

    project_dir = find_project_dir()
    flow = _load_flow(project_dir)

    merge_ids = [
        n["id"] for n in flow.get("nodes", []) if n.get("type") == "core.logic.merge"
    ]
    if not merge_ids:
        sys.exit("FAIL: No core.logic.merge node in the flow")

    # Merge plugin: accepts multiple incoming edges on the same `input` port
    incoming = [
        e for e in flow.get("edges", []) if e.get("targetNodeId") in merge_ids
    ]
    if len(incoming) < 2:
        sys.exit(
            f"FAIL: Expected 2+ edges into the merge node to prove parallel "
            f"synchronization, found {len(incoming)}: {incoming}"
        )

    # Both incoming paths must originate from HTTP nodes (v1 or v2)
    http_ids = {
        n["id"]
        for n in flow.get("nodes", [])
        if n.get("type", "").startswith("core.action.http")
    }
    upstream_sources = {_trace_upstream(flow, e["sourceNodeId"]) for e in incoming}
    if not all(any(src in http_ids for src in chain) for chain in upstream_sources):
        sys.exit(
            f"FAIL: Expected both merge inputs to trace back to HTTP nodes. "
            f"http_ids={http_ids}, upstream_chains={upstream_sources}"
        )

    payload = run_debug(timeout=240)
    assert_outputs_contain(payload, ["Seattle", "Phoenix"])
    print("OK: merge node with 2+ HTTP upstreams; debug returned both cities")


def _trace_upstream(flow: dict, node_id: str, depth: int = 5) -> frozenset:
    """Walk upstream from node_id up to `depth` hops, return set of visited ids."""
    seen = set()
    frontier = [node_id]
    for _ in range(depth):
        next_frontier = []
        for nid in frontier:
            if nid in seen:
                continue
            seen.add(nid)
            for e in flow.get("edges", []):
                if e.get("targetNodeId") == nid:
                    next_frontier.append(e["sourceNodeId"])
        frontier = next_frontier
    return frozenset(seen)


if __name__ == "__main__":
    main()
