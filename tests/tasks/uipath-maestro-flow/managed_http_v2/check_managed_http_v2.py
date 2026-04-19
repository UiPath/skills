#!/usr/bin/env python3
"""Managed HTTP v2: assert core.action.http.v2 is used and legacy v1 is not."""

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.flow_check import (  # noqa: E402
    assert_output_int_in_range,
    find_project_dir,
    run_debug,
)


def _load_flow_types(project_dir: str) -> list[str]:
    flows = glob.glob(os.path.join(project_dir, "*.flow"))
    if not flows:
        sys.exit(f"FAIL: No .flow file found in {project_dir}")
    with open(flows[0]) as f:
        flow = json.load(f)
    return [n.get("type", "") for n in flow.get("nodes", [])]


def main():
    project_dir = find_project_dir()
    types = _load_flow_types(project_dir)

    has_v2 = any(t == "core.action.http.v2" for t in types)
    has_v1 = any(t == "core.action.http" for t in types)

    if not has_v2:
        sys.exit(
            f"FAIL: Expected at least one core.action.http.v2 node, found types: {types}"
        )
    if has_v1:
        sys.exit(
            f"FAIL: Flow uses deprecated core.action.http (v1). The http plugin mandates v2. Types: {types}"
        )

    payload = run_debug(timeout=240)
    # Seattle temperature in Fahrenheit — loose bounds across seasons
    assert_output_int_in_range(payload, -20, 120)
    print("OK: core.action.http.v2 used; v1 absent; debug returned a plausible temperature")


if __name__ == "__main__":
    main()
