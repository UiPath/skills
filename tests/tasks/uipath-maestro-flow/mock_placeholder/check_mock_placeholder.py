#!/usr/bin/env python3
"""Mock placeholder: assert core.logic.mock present and no hallucinated RPA node."""

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

    has_mock = any(t == "core.logic.mock" for t in types)
    if not has_mock:
        sys.exit(
            f"FAIL: Expected a core.logic.mock placeholder for the unpublished "
            f"RPA process per Critical Rule 14. Node types found: {types}"
        )

    # Agent must NOT hallucinate an RPA resource node when the process doesn't exist
    hallucinated = [t for t in types if t.startswith("uipath.core.rpa")]
    if hallucinated:
        sys.exit(
            f"FAIL: Flow references an RPA resource node that does not exist in "
            f"the tenant. Anti-Pattern 7 says insert a mock, not hallucinate a "
            f"resource key. Offending types: {hallucinated}"
        )

    print("OK: core.logic.mock present; no hallucinated RPA node")


if __name__ == "__main__":
    main()
