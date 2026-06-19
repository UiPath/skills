#!/usr/bin/env python3
"""MCP server resource check.

Validates:
  1. resources/GitHubMcp/resource.json declares an MCP server:
       - $resourceType == "mcp"  (not "tool" — MCP is a distinct resource type)
       - name == "GitHubMcp"
       - description is a non-empty string
       - isEnabled is truthy
       - id is a UUID-shaped non-empty string
       - tools is a list (may be empty — MCP tool definitions are
         populated at runtime per the agent-json-format spec)
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DevToolsSol" / "DevAssistantAgent"
RESOURCE = ROOT / "resources" / "GitHubMcp" / "resource.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def assert_mcp_resource(resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "mcp":
        sys.exit(
            f'FAIL: $resourceType should be "mcp" (distinct from "tool"), got {rtype!r}'
        )
    name = resource.get("name")
    if name != "GitHubMcp":
        sys.exit(f'FAIL: MCP resource name should be "GitHubMcp", got {name!r}')
    description = resource.get("description")
    if not isinstance(description, str) or not description.strip():
        sys.exit(f"FAIL: MCP resource description missing or empty: {description!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: MCP resource isEnabled must be truthy, got {resource.get('isEnabled')!r}")
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: MCP resource id missing or malformed: {rid!r}")
    tools = resource.get("tools")
    if not isinstance(tools, list):
        sys.exit(f"FAIL: MCP resource tools must be a list, got {tools!r}")
    print(
        f'OK: resource.json is $resourceType="mcp", name="GitHubMcp", '
        f'id={rid}, isEnabled=true, tools list present ({len(tools)} entries)'
    )


def main() -> None:
    resource = load(RESOURCE)
    assert_mcp_resource(resource)


if __name__ == "__main__":
    main()
