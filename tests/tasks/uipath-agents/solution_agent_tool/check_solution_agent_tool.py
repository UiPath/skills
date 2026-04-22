#!/usr/bin/env python3
"""Solution agent-as-tool resource check.

Validates:
  1. ParentAgent and ToolAgent have distinct, well-formed projectId
     UUIDs (guards against copy-pasted UUIDs across agents).
  2. ParentAgent/resources/ToolAgent/resource.json declares ToolAgent
     as a solution-internal agent tool:
       - $resourceType == "tool"
       - type == "agent"
       - location == "solution"
       - properties.processName == "ToolAgent"
       - properties.folderPath == "solution_folder"
     and its inputSchema / outputSchema are functionally equivalent
     to ToolAgent/agent.json's own inputSchema / outputSchema.
     "Functionally equivalent" means identical type/properties/
     required structure — but `description` text is allowed to differ
     (descriptions are LLM-facing hints, not part of the runtime
     contract).
"""

import json
import os
import sys
from pathlib import Path

SOLUTION_DIR = Path(os.getcwd()) / "OrchestratorSol"
RESOURCE = (
    SOLUTION_DIR / "ParentAgent" / "resources" / "ToolAgent" / "resource.json"
)
TOOL_AGENT = SOLUTION_DIR / "ToolAgent" / "agent.json"
PARENT_AGENT = SOLUTION_DIR / "ParentAgent" / "agent.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_distinct_project_ids():
    parent = load(PARENT_AGENT)
    tool = load(TOOL_AGENT)
    parent_id = parent.get("projectId")
    tool_id = tool.get("projectId")
    for label, pid in (("ParentAgent", parent_id), ("ToolAgent", tool_id)):
        if not isinstance(pid, str) or "-" not in pid:
            sys.exit(f"FAIL: {label} has missing or malformed projectId: {pid!r}")
    if parent_id == tool_id:
        sys.exit(
            f"FAIL: ParentAgent and ToolAgent share the same projectId "
            f"{parent_id} (Anti-pattern 8)"
        )
    print(f"OK: Distinct projectIds — {parent_id} vs {tool_id}")


def assert_resource_fields(resource: dict):
    expected = {
        "$resourceType": "tool",
        "type": "agent",
        "location": "solution",
    }
    for key, want in expected.items():
        got = resource.get(key)
        if got != want:
            sys.exit(f"FAIL: resource.json {key!r} should be {want!r}, got {got!r}")
    print('OK: resource.json has $resourceType="tool", type="agent", location="solution"')

    props = resource.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: resource.json.properties is not an object: {props!r}")
    expected_props = {
        "processName": "ToolAgent",
        "folderPath": "solution_folder",
    }
    for key, want in expected_props.items():
        got = props.get(key)
        if got != want:
            sys.exit(
                f"FAIL: resource.json.properties.{key} should be {want!r}, got {got!r}"
            )
    print(
        'OK: resource.json.properties has processName="ToolAgent" and '
        'folderPath="solution_folder"'
    )


def strip_descriptions(node):
    """Recursively drop any `description` key from nested dicts/lists.

    `description` is LLM-facing documentation, not part of the
    functional schema — the tool call executes identically regardless
    of description text.
    """
    if isinstance(node, dict):
        return {k: strip_descriptions(v) for k, v in node.items() if k != "description"}
    if isinstance(node, list):
        return [strip_descriptions(item) for item in node]
    return node


def assert_schemas_match_tool_agent(resource: dict, tool: dict):
    pairs = [
        ("inputSchema", resource.get("inputSchema"), tool.get("inputSchema")),
        ("outputSchema", resource.get("outputSchema"), tool.get("outputSchema")),
    ]
    for label, resource_schema, tool_schema in pairs:
        r_shape = strip_descriptions(resource_schema)
        t_shape = strip_descriptions(tool_schema)
        if r_shape != t_shape:
            sys.exit(
                f"FAIL: resource.json.{label} is not shape-equivalent to "
                f"ToolAgent/agent.json.{label} (comparing type/properties/required, "
                f"ignoring description text)\n"
                f"  resource.{label}:\n{json.dumps(r_shape, sort_keys=True, indent=2)}\n"
                f"  tool.{label}:\n{json.dumps(t_shape, sort_keys=True, indent=2)}"
            )
        print(f"OK: resource.json.{label} is shape-equivalent to ToolAgent/agent.json.{label}")


def main():
    if not SOLUTION_DIR.is_dir():
        sys.exit(f"FAIL: Solution directory {SOLUTION_DIR} does not exist")

    assert_distinct_project_ids()

    resource = load(RESOURCE)
    tool = load(TOOL_AGENT)

    assert_resource_fields(resource)
    assert_schemas_match_tool_agent(resource, tool)


if __name__ == "__main__":
    main()
