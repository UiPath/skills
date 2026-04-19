#!/usr/bin/env python3
"""Plan artifacts: verify the built flow matches the plan's branching topology."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import find_project_dir  # noqa: E402


def _load_flow(project_dir: str) -> dict:
    flows = glob.glob(os.path.join(project_dir, "*.flow"))
    if not flows:
        sys.exit(f"FAIL: No .flow file found in {project_dir}")
    with open(flows[0]) as f:
        return json.load(f)


def main():
    project_dir = find_project_dir()
    flow = _load_flow(project_dir)

    types = [n.get("type", "") for n in flow.get("nodes", [])]

    decision_count = sum(1 for t in types if t == "core.logic.decision")
    end_count = sum(1 for t in types if t == "core.control.end")
    http_count = sum(1 for t in types if t.startswith("core.action.http"))

    if decision_count < 1:
        sys.exit(f"FAIL: Expected ≥1 core.logic.decision node, found {decision_count}")
    if end_count < 2:
        sys.exit(
            f"FAIL: Decision-branched flow needs two End nodes (one per path), found {end_count}"
        )
    if http_count < 1:
        sys.exit(f"FAIL: Expected ≥1 HTTP node to fetch order details, found {http_count}")

    # Every `out` variable must be mapped on every reachable End node (Critical Rule 12)
    out_vars = [
        v
        for v in flow.get("variables", {}).get("globals", [])
        if v.get("direction") == "out"
    ]
    if out_vars:
        for n in flow.get("nodes", []):
            if n.get("type") != "core.control.end":
                continue
            outputs = n.get("outputs") or {}
            for v in out_vars:
                name = v.get("id") or v.get("name")
                if name and name not in outputs:
                    sys.exit(
                        f"FAIL: End node '{n.get('id')}' missing output mapping for "
                        f"'out' variable '{name}' (Critical Rule 12)"
                    )

    print(
        f"OK: flow has {decision_count} decision, {end_count} ends, {http_count} HTTP; "
        f"out-var mappings present on every End"
    )


if __name__ == "__main__":
    main()
