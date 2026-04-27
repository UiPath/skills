#!/usr/bin/env python3
"""Built-in tool resource check.

Validates that the agent enabled at least one built-in tool by
authoring a resource.json under DocAnalystAgent/resources/ that
matches the static built-in-tools registry:

  - $resourceType == "tool"
  - type == "internal"
  - referenceKey is null
  - properties.toolType is one of the four documented keys:
      "analyze-attachments" | "load-attachments" |
      "deep-rag" | "batch-transform"
  - id is a UUID-shaped string
  - isEnabled is truthy

Since the prompt asked for "Analyze Files" specifically, we also
verify at least one resource uses toolType == "analyze-attachments".

The resource directory name is not prescribed (agent may use any
human-readable name), so we scan every resource.json under
DocAnalystAgent/resources/.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "DocsSol" / "DocAnalystAgent"
RESOURCES_DIR = ROOT / "resources"

BUILTIN_TOOL_TYPES = {
    "analyze-attachments",
    "load-attachments",
    "deep-rag",
    "batch-transform",
}


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_resource_jsons() -> list:
    if not RESOURCES_DIR.is_dir():
        sys.exit(f"FAIL: {RESOURCES_DIR} does not exist — no resources/ directory")
    files = sorted(RESOURCES_DIR.rglob("resource.json"))
    if not files:
        sys.exit(f"FAIL: no resource.json files found under {RESOURCES_DIR}")
    return files


def is_builtin_tool(resource: dict) -> bool:
    return (
        resource.get("$resourceType") == "tool"
        and resource.get("type") == "internal"
    )


def assert_builtin_shape(path: Path, resource: dict) -> str:
    if resource.get("$resourceType") != "tool":
        sys.exit(f'FAIL: {path} $resourceType should be "tool", got {resource.get("$resourceType")!r}')
    if resource.get("type") != "internal":
        sys.exit(f'FAIL: {path} type should be "internal" for a built-in tool, got {resource.get("type")!r}')
    if resource.get("referenceKey") is not None:
        sys.exit(
            f"FAIL: {path} referenceKey should be null for a built-in tool "
            f"(per the registry), got {resource.get('referenceKey')!r}"
        )
    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: {path} resource id missing or malformed: {rid!r}")
    if not resource.get("isEnabled"):
        sys.exit(f"FAIL: {path} resource.isEnabled must be truthy")
    props = resource.get("properties") or {}
    tool_type = props.get("toolType")
    if tool_type not in BUILTIN_TOOL_TYPES:
        sys.exit(
            f"FAIL: {path} properties.toolType must be one of "
            f"{sorted(BUILTIN_TOOL_TYPES)}, got {tool_type!r}"
        )
    print(f"OK: {path.parent.name} is a built-in tool with toolType={tool_type!r}")
    return tool_type


def main() -> None:
    files = find_resource_jsons()
    builtin_tool_types_seen = []
    for f in files:
        resource = load(f)
        if is_builtin_tool(resource):
            tt = assert_builtin_shape(f, resource)
            builtin_tool_types_seen.append(tt)

    if not builtin_tool_types_seen:
        sys.exit(
            "FAIL: no built-in tool resources found — expected at least one "
            'resource with $resourceType="tool" and type="internal"'
        )

    if "analyze-attachments" not in builtin_tool_types_seen:
        sys.exit(
            f'FAIL: prompt asked for the "Analyze Files" built-in tool '
            f'(toolType "analyze-attachments"), but none was enabled. '
            f'Got toolTypes: {builtin_tool_types_seen}'
        )
    print('OK: "Analyze Files" (toolType="analyze-attachments") is enabled')


if __name__ == "__main__":
    main()
