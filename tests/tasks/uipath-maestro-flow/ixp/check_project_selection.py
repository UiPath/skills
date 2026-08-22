#!/usr/bin/env python3
"""Verify that the dataset row selected its exact published IxP model."""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "_shared"))
from flow_check import find_flow_file  # noqa: E402


EXPECTED = {
    "aviation": (
        "aviation-investigation-final-report-demo-a42b1d4d-ixp",
        "uipath.ixp.aviation-investigation-final-report-demo-a42b1d4d-ixp.",
    ),
    "birth-certificate": (
        "birth_certificates_oob-6252526a-ixp",
        "uipath.ixp.birth-certificates-oob-6252526a-ixp.",
    ),
}


def _nested_values(value, key: str):
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            if nested_key == key:
                yield nested_value
            yield from _nested_values(nested_value, key)
    elif isinstance(value, list):
        for item in value:
            yield from _nested_values(item, key)


def main() -> int:
    row = next((part for part in os.getcwd().split(os.sep) if part in EXPECTED), None)
    if row is None:
        print(f"FAIL: unknown dataset row in cwd: {os.getcwd()}", file=sys.stderr)
        return 2

    path = find_flow_file()
    with open(path, encoding="utf-8") as f:
        flow = json.load(f)

    model_name, type_prefix = EXPECTED[row]
    for node in flow.get("nodes", []):
        has_model = any(
            value == model_name for value in _nested_values(node, "modelName")
        )
        if str(node.get("type", "")).startswith(type_prefix) and has_model:
            print(f"OK: {row} uses published model {model_name} in {path}")
            return 0

    print(
        f"FAIL: no IxP node in {path} pairs type prefix {type_prefix!r} "
        f"with modelName {model_name!r}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
