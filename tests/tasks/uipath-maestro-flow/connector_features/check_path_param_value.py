#!/usr/bin/env python3
"""Verify a deterministic path-parameter value is wired into the flow.

Usage:
    check_path_param_value.py <flow_glob> <expected_value>

Looks for <expected_value> in either:
  - Any node's `inputs.detail.pathParameters` dict values (native connector path)
  - Any node's `inputs.detail.url` or `inputs.detail.endpoint` (managed HTTP path)
"""

from __future__ import annotations

import glob
import json
import sys
from typing import Any


def _fail(message: str) -> None:
    sys.exit(f"FAIL: {message}")


def _load_flow(pattern: str) -> dict[str, Any]:
    matches = sorted(glob.glob(pattern, recursive=True))
    if not matches:
        _fail(f"No flow found for {pattern!r}")
    if len(matches) > 1:
        _fail(f"Multiple flows found for {pattern!r}: {matches}")
    with open(matches[0], encoding="utf-8") as flow_file:
        return json.load(flow_file)


def main() -> None:
    if len(sys.argv) != 3:
        _fail("usage: check_path_param_value.py <flow_glob> <expected_value>")

    flow = _load_flow(sys.argv[1])
    needle = sys.argv[2]

    for node in flow.get("nodes", []):
        detail = (node.get("inputs", {}) or {}).get("detail", {}) or {}
        path_params = detail.get("pathParameters", {}) or {}
        if isinstance(path_params, dict):
            for value in path_params.values():
                if str(value) == needle:
                    print(
                        f"OK: {needle!r} found in pathParameters of node {node.get('id')!r}"
                    )
                    return
        for key in ("url", "endpoint"):
            target = str(detail.get(key, "") or "")
            if needle in target:
                print(f"OK: {needle!r} found in {key} of node {node.get('id')!r}")
                return

    _fail(f"{needle!r} not found in any node's pathParameters, url, or endpoint")


if __name__ == "__main__":
    main()
