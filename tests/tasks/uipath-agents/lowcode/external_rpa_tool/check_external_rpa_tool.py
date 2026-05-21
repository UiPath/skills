#!/usr/bin/env python3
"""External RPA process tool resource check.

Validates that the agent's external RPA tool wiring matches the
deployed "FibonacciRPA" process in the "Shared/uipath-agents" folder:

  1. resources/FibonacciRPA/resource.json declares an EXTERNAL
     RPA-process tool (Critical Rules 11 and 12):
       - $resourceType == "tool"
       - type == "process"
       - location == "external"
       - properties.processName == "FibonacciRPA"
       - properties.folderPath == "Shared/uipath-agents"
       - referenceKey is a UUID-shaped non-empty string (the agent
         must populate it from `uip solution resource list`'s `Key`).
  2. id is a UUID-shaped non-empty string.
  3. isEnabled is truthy.
  4. inputSchema and outputSchema are objects (shape only —
     content not prescribed).
  5. bindings_v2.json contains a resource binding with
     resource="process", key="FibonacciRPA",
     value.name.defaultValue="FibonacciRPA",
     value.folderPath.defaultValue="Shared/uipath-agents".
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "FibonacciSol" / "FibonacciAgent"
RESOURCE = ROOT / "resources" / "FibonacciRPA" / "resource.json"
BINDINGS = ROOT / "bindings_v2.json"

EXPECTED_PROCESS_NAME = "FibonacciRPA"
EXPECTED_FOLDER_PATH = "Shared/uipath-agents/FibonacciRPA"


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
        "location": "external",
    }
    for key, want in expected.items():
        got = resource.get(key)
        if got != want:
            sys.exit(f"FAIL: resource.json {key!r} should be {want!r}, got {got!r}")
    print(
        'OK: resource.json is $resourceType="tool", type="process", location="external"'
    )


def assert_properties(resource: dict) -> None:
    props = resource.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: resource.json.properties is not an object: {props!r}")
    pname = props.get("processName")
    if pname != EXPECTED_PROCESS_NAME:
        sys.exit(
            f"FAIL: properties.processName should be {EXPECTED_PROCESS_NAME!r} "
            f"(matching the deployed process), got {pname!r}"
        )
    fpath = props.get("folderPath")
    if fpath != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: properties.folderPath should be {EXPECTED_FOLDER_PATH!r} "
            f"(the deployed Orchestrator folder of FibonacciRPA), got {fpath!r}"
        )
    print(
        f"OK: properties.processName={EXPECTED_PROCESS_NAME!r}, "
        f"folderPath={EXPECTED_FOLDER_PATH!r}"
    )


def assert_identity_and_schemas(resource: dict) -> None:
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: resource id missing or malformed: {rid!r}")
    rkey = resource.get("referenceKey")
    if not isinstance(rkey, str) or "-" not in rkey:
        sys.exit(
            f"FAIL: resource.referenceKey must be a UUID-shaped string copied "
            f"from `uip solution resource list`'s `Key`, got {rkey!r}"
        )
    if not resource.get("isEnabled"):
        sys.exit(
            f"FAIL: resource.isEnabled must be truthy, got {resource.get('isEnabled')!r}"
        )
    if not isinstance(resource.get("inputSchema"), dict):
        sys.exit("FAIL: resource.inputSchema must be an object")
    if not isinstance(resource.get("outputSchema"), dict):
        sys.exit("FAIL: resource.outputSchema must be an object")
    print(
        f"OK: resource has id={rid}, referenceKey={rkey}, isEnabled=true, and input/output schemas"
    )


def assert_bindings_process(bindings: dict) -> None:
    resources = bindings.get("resources")
    if not isinstance(resources, list):
        sys.exit(f"FAIL: bindings_v2.json resources must be a list, got {resources!r}")

    process_bindings = [
        r
        for r in resources
        if isinstance(r, dict)
        and r.get("resource") == "process"
        and r.get("key") == EXPECTED_PROCESS_NAME
    ]
    if not process_bindings:
        sys.exit(
            f'FAIL: bindings_v2.json has no resource entry with resource="process" '
            f"and key={EXPECTED_PROCESS_NAME!r}. `uip agent validate` should emit "
            "one for the external RPA tool."
        )
    if len(process_bindings) > 1:
        sys.exit(
            f"FAIL: bindings_v2.json contains {len(process_bindings)} process "
            f"bindings keyed {EXPECTED_PROCESS_NAME!r}; exactly one is expected."
        )
    binding = process_bindings[0]

    value = binding.get("value")
    if not isinstance(value, dict):
        sys.exit(
            f"FAIL: bindings_v2.json process binding value must be an object, got {value!r}"
        )

    name_field = value.get("name") or {}
    name_default = (
        name_field.get("defaultValue") if isinstance(name_field, dict) else None
    )
    if name_default != EXPECTED_PROCESS_NAME:
        sys.exit(
            f"FAIL: bindings_v2.json process binding value.name.defaultValue should be "
            f"{EXPECTED_PROCESS_NAME!r}, got {name_default!r}"
        )

    folder_field = value.get("folderPath") or {}
    folder_default = (
        folder_field.get("defaultValue") if isinstance(folder_field, dict) else None
    )
    if folder_default != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: bindings_v2.json process binding value.folderPath.defaultValue should be "
            f"{EXPECTED_FOLDER_PATH!r} (matching the deployed process folder), got {folder_default!r}"
        )

    print(
        f"OK: bindings_v2.json process binding key={EXPECTED_PROCESS_NAME!r}, "
        f"name={EXPECTED_PROCESS_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}"
    )


def main() -> None:
    resource = load(RESOURCE)
    bindings = load(BINDINGS)

    assert_tool_header(resource)
    assert_properties(resource)
    assert_identity_and_schemas(resource)
    assert_bindings_process(bindings)


if __name__ == "__main__":
    main()
