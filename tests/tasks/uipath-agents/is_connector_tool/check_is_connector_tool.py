#!/usr/bin/env python3
"""Integration Service (IS) connector tool resource check.

Design-time checks only — this script does NOT invoke the connector.

Validates:

  1. At least one resource.json under ResearchAgent/resources/ declares
     an IS tool:
       - $resourceType == "tool"
       - type == "integration"
     (Other `properties` fields are intentionally under-asserted — the
      canonical IS tool `properties` shape isn't fully locked in the
      skill docs yet. When it stabilizes, tighten this check.)

  2. At least one bindings_v2.json file exists somewhere under the
     agent project. Agent authors it manually as the source for
     `uip solution resource refresh`. Shape is under-asserted for
     now — we just verify presence and valid JSON.

  3. After `uip solution resource refresh`, at least one connection
     resource file exists under
     ResearchSol/resources/solution_folder/connection/. The exact
     filename depends on the connector and connection name chosen by
     the agent; we check the directory is non-empty.
"""

import json
import os
import sys
from pathlib import Path

SOLUTION = Path(os.getcwd()) / "ResearchSol"
AGENT = SOLUTION / "ResearchAgent"
AGENT_RESOURCES = AGENT / "resources"
CONNECTION_DIR = SOLUTION / "resources" / "solution_folder" / "connection"


def load(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_integration_tool() -> tuple:
    if not AGENT_RESOURCES.is_dir():
        sys.exit(
            f"FAIL: {AGENT_RESOURCES} does not exist — agent has no "
            "resources/ directory, so no IS tool was authored"
        )
    for path in sorted(AGENT_RESOURCES.rglob("resource.json")):
        data = load(path)
        if data.get("$resourceType") == "tool" and data.get("type") == "integration":
            return path, data
    sys.exit(
        f"FAIL: no IS tool resource found under {AGENT_RESOURCES} — "
        'expected at least one resource.json with $resourceType="tool" '
        'and type="integration"'
    )


def assert_bindings_v2_authored() -> Path:
    candidates = sorted(AGENT.rglob("bindings_v2.json"))
    # Exclude .agent-builder generations; bindings_v2.json authored by
    # the agent is the source for refresh — the generated equivalent
    # would be under .agent-builder/ after validate.
    authored = [p for p in candidates if ".agent-builder" not in p.parts]
    if not authored:
        sys.exit(
            f"FAIL: no bindings_v2.json authored under {AGENT} (outside "
            ".agent-builder/). Agent must create it manually as the source "
            "for `uip solution resource refresh`."
        )
    path = authored[0]
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")
    if not isinstance(data, dict) and not isinstance(data, list):
        sys.exit(f"FAIL: {path} root is neither object nor array: {type(data).__name__}")
    print(f"OK: bindings_v2.json authored at {path.relative_to(SOLUTION.parent)}")
    return path


def assert_connection_provisioned() -> None:
    if not CONNECTION_DIR.is_dir():
        sys.exit(
            f"FAIL: {CONNECTION_DIR} does not exist — `uip solution resource "
            "refresh` did not provision a connection resource under "
            "resources/solution_folder/connection/"
        )
    # Directory exists; require at least one connection JSON file somewhere under it.
    connection_files = [p for p in CONNECTION_DIR.rglob("*.json") if p.is_file()]
    if not connection_files:
        sys.exit(
            f"FAIL: {CONNECTION_DIR} is empty — refresh did not drop any "
            "connection resource JSON files"
        )
    print(
        f"OK: found {len(connection_files)} connection resource file(s) under "
        f"resources/solution_folder/connection/"
    )


def main() -> None:
    if not SOLUTION.is_dir():
        sys.exit(f"FAIL: Solution directory {SOLUTION} does not exist")

    tool_path, tool = find_integration_tool()
    print(
        f'OK: {tool_path.relative_to(SOLUTION.parent)} is $resourceType="tool", '
        f'type="integration"'
    )

    rid = tool.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: IS tool id missing or malformed: {rid!r}")
    if not tool.get("isEnabled"):
        sys.exit(f"FAIL: IS tool isEnabled must be truthy, got {tool.get('isEnabled')!r}")
    print(f"OK: IS tool has id={rid}, isEnabled=true")

    assert_bindings_v2_authored()
    assert_connection_provisioned()


if __name__ == "__main__":
    main()
