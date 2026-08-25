#!/usr/bin/env python3
"""Solution RPA process tool resource check.

Validates:
  1. resources/CalculatePay/resource.json declares a solution-internal
     RPA-process tool:
       - $resourceType == "tool"
       - type == "process"
       - location == "solution"
       - properties.processName == "CalculatePay"
       - properties.folderPath == "solution_folder"
  2. id is a UUID-shaped non-empty string.
  3. isEnabled is truthy.
  4. inputSchema and outputSchema are objects.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "PayrollSol" / "PayrollAgent"
RESOURCE = ROOT / "resources" / "CalculatePay" / "resource.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_tool_header(resource: dict) -> None:
    expected = {
        "$resourceType": "tool",
        "type": "process",
        "location": "solution",
    }
    for key, want in expected.items():
        got = resource.get(key)
        if got != want:
            sys.exit(f"FAIL: resource.json {key!r} should be {want!r}, got {got!r}")
    print('OK: resource.json is $resourceType="tool", type="process", location="solution"')


def assert_properties(resource: dict) -> None:
    props = resource.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: resource.json.properties is not an object: {props!r}")
    if props.get("processName") != "CalculatePay":
        sys.exit(
            f'FAIL: properties.processName should be "CalculatePay", got {props.get("processName")!r}'
        )
    if props.get("folderPath") != "solution_folder":
        sys.exit(
            f'FAIL: properties.folderPath should be "solution_folder" for a '
            f'solution-internal tool, got {props.get("folderPath")!r}'
        )
    print('OK: properties.processName="CalculatePay", folderPath="solution_folder"')


def assert_identity_and_schemas(resource: dict) -> None:
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: resource id missing or malformed: {rid!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: resource.isEnabled must be truthy, got {resource.get('isEnabled')!r}")
    if not isinstance(resource.get("inputSchema"), dict):
        sys.exit("FAIL: resource.inputSchema must be an object")
    if not isinstance(resource.get("outputSchema"), dict):
        sys.exit("FAIL: resource.outputSchema must be an object")
    print(f"OK: resource has id={rid}, isEnabled=true, and input/output schemas")


def main() -> None:
    resource = load(RESOURCE)
    assert_tool_header(resource)
    assert_properties(resource)
    assert_identity_and_schemas(resource)


if __name__ == "__main__":
    main()
