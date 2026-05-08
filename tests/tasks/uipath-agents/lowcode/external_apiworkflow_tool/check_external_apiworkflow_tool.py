#!/usr/bin/env python3
"""External API workflow tool resource check.

Validates:
  1. resources/GetLatestQuote/resource.json declares an EXTERNAL
     API workflow tool:
       - $resourceType == "tool"
       - type == "api"
       - location == "external"
       - properties.folderPath is a real folder path (NOT "solution_folder")
  2. id is a UUID-shaped non-empty string.
  3. isEnabled is truthy.
  4. inputSchema and outputSchema are objects.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "QuoteSol" / "QuoteAgent"
RESOURCE = ROOT / "resources" / "GetLatestQuote" / "resource.json"


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
        "type": "api",
        "location": "external",
    }
    for key, want in expected.items():
        got = resource.get(key)
        if got != want:
            sys.exit(f"FAIL: resource.json {key!r} should be {want!r}, got {got!r}")
    print('OK: resource.json is $resourceType="tool", type="api", location="external"')


def assert_properties(resource: dict) -> None:
    props = resource.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: resource.json.properties is not an object: {props!r}")
    fpath = props.get("folderPath")
    if not isinstance(fpath, str) or not fpath.strip():
        sys.exit(f"FAIL: properties.folderPath must be a non-empty string, got {fpath!r}")
    if fpath == "solution_folder":
        sys.exit(
            'FAIL: properties.folderPath is "solution_folder", which is only '
            'valid for location=="solution". External tools require a real '
            'Orchestrator folder path like "Shared".'
        )
    print(f'OK: properties.folderPath={fpath!r} (not "solution_folder")')


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
