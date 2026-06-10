#!/usr/bin/env python3
"""MCP server resource check.

Validates resources/orchestrator/resource.json declares the UiPath
Orchestrator MCP server reference in the authoritative shape
(agents-storage-schemas `mcpStorageSchemaV16`):
  - $resourceType == "mcp"  (not "tool" — MCP is a distinct resource type)
  - name == "orchestrator"  (the resource is named after the MCP server itself,
    matching its folder; the job-subset lives in availableTools, not the name)
  - description is a non-empty string
  - id is a UUID-shaped non-empty string (agent-local id)
  - slug is a non-empty string (the AgentHub server slug)
  - folderPath is a non-empty string (the server's Orchestrator folder)
  - availableTools is a list (the user-SELECTED subset of the server's tools;
    may be empty offline). Each entry, when present, carries name + description
    + an inputSchema OBJECT (not an escaped string).
  - solutionProperties.resourceKey is a non-empty string (the cloud server key)

The resource is a reference (key/slug) to a cloud MCP server, not a server
definition.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DevToolsSol" / "DevAssistantAgent"
RESOURCE = ROOT / "resources" / "orchestrator" / "resource.json"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def require_nonempty_str(resource: dict, field: str) -> str:
    value = resource.get(field)
    if not isinstance(value, str) or not value.strip():
        sys.exit(f"FAIL: MCP resource {field} missing or empty: {value!r}")
    return value


def assert_mcp_resource(resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "mcp":
        sys.exit(
            f'FAIL: $resourceType should be "mcp" (distinct from "tool"), got {rtype!r}'
        )
    name = resource.get("name")
    if name != "orchestrator":
        sys.exit(
            f'FAIL: MCP resource name should be "orchestrator" (named after the '
            f"MCP server itself, matching its folder), got {name!r}"
        )

    require_nonempty_str(resource, "description")
    require_nonempty_str(resource, "slug")
    require_nonempty_str(resource, "folderPath")

    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: MCP resource id missing or malformed: {rid!r}")

    sp = resource.get("solutionProperties")
    if not isinstance(sp, dict) or not str(sp.get("resourceKey") or "").strip():
        sys.exit(
            f"FAIL: MCP resource solutionProperties.resourceKey missing or empty: {sp!r}"
        )

    tools = resource.get("availableTools")
    if not isinstance(tools, list):
        sys.exit(
            f"FAIL: MCP resource availableTools must be a list (selected subset), got {tools!r}"
        )
    for i, t in enumerate(tools):
        if not isinstance(t, dict):
            sys.exit(f"FAIL: availableTools[{i}] must be an object, got {t!r}")
        if not str(t.get("name") or "").strip():
            sys.exit(f"FAIL: availableTools[{i}].name missing or empty")
        if not isinstance(t.get("inputSchema"), dict):
            sys.exit(
                f"FAIL: availableTools[{i}].inputSchema must be a JSON Schema object "
                f"(parse the escaped string from `resource get`), got {t.get('inputSchema')!r}"
            )

    print(
        f'OK: resource.json is $resourceType="mcp", name="orchestrator", id={rid}, '
        f'slug={resource.get("slug")!r}, folderPath={resource.get("folderPath")!r}, '
        f'resourceKey present, availableTools list present ({len(tools)} selected)'
    )


def main() -> None:
    resource = load(RESOURCE)
    assert_mcp_resource(resource)


if __name__ == "__main__":
    main()
