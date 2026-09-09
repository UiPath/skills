#!/usr/bin/env python3
"""Client-side tool resource check.

Validates that a client-side tool is authored under BoardAssistantAgent/resources/
in the shape `clientSideToolResourceSchema` accepts:
  - $resourceType == "tool"  (client-side is a tool subtype, unlike MCP)
  - type == "clientSide"     — lowercase. The Python models spell it "ClientSide"
    and tolerate either via a case-insensitive enum, but the zod schemas and the
    solution packager do not. Checked explicitly so the failure names the casing
    instead of surfacing as a generic "no client-side tool found".
  - referenceKey is null     — the schema declares z.null(); unlike other tool
    types this one references no cloud resource.
  - location == "solution"
  - properties.folderPath == "solution_folder" — `uip agent validate` reports
    "solution tools must use folderPath" otherwise.
  - settings, guardrail, inputSchema, outputSchema all present — declared
    without .optional(). guardrail carries a policies list (may be empty).
  - name and description are non-empty. The name is the agent's choice, so it
    is NOT pinned to a specific value — we locate the resource by type.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "BoardSol" / "BoardAssistantAgent"
RESOURCES = ROOT / "resources"


def load_resources() -> list:
    if not RESOURCES.is_dir():
        sys.exit(
            f"FAIL: {RESOURCES} does not exist — the agent authored no resources"
        )
    out = []
    for path in sorted(RESOURCES.rglob("resource.json")):
        try:
            out.append((path, json.loads(path.read_text())))
        except (OSError, json.JSONDecodeError):
            continue
    return out


def find_client_side_resource(resources: list) -> dict:
    for path, data in resources:
        if data.get("type") == "clientSide":
            print(f"OK: found client-side tool at {path.relative_to(ROOT.parent)}")
            return data

    # Distinguish the casing trap from "nothing was authored at all".
    for path, data in resources:
        if str(data.get("type") or "").lower() == "clientside":
            sys.exit(
                f'FAIL: {path.relative_to(ROOT.parent)} has type {data.get("type")!r}; '
                'the schema literal is "clientSide" (lowercase c). "ClientSide" is '
                "what the Python models use and is rejected by the solution packager."
            )

    found = sorted({str(d.get("type")) for _, d in resources if d.get("type")})
    sys.exit(
        f'FAIL: no client-side tool (type=="clientSide") found under {RESOURCES}. '
        f"Tool types present: {found or 'none'}"
    )


def require_nonempty_str(resource: dict, field: str) -> str:
    value = resource.get(field)
    if not isinstance(value, str) or not value.strip():
        sys.exit(f"FAIL: client-side tool {field} missing or empty: {value!r}")
    return value


def require_schema_object(resource: dict, field: str) -> None:
    value = resource.get(field)
    if not isinstance(value, dict):
        sys.exit(
            f"FAIL: client-side tool {field} must be a JSON Schema object "
            f"(declared without .optional()), got {value!r}"
        )


def assert_client_side_resource(resource: dict) -> None:
    rtype = resource.get("$resourceType")
    if rtype != "tool":
        sys.exit(
            f'FAIL: $resourceType should be "tool" (client-side is a tool subtype), '
            f"got {rtype!r}"
        )

    name = require_nonempty_str(resource, "name")
    require_nonempty_str(resource, "description")

    rid = resource.get("id")
    if not isinstance(rid, str) or "-" not in rid:
        sys.exit(f"FAIL: client-side tool id missing or malformed: {rid!r}")

    # Explicit null, not absent and not the tool id.
    if "referenceKey" not in resource:
        sys.exit(
            "FAIL: client-side tool referenceKey missing — the schema declares it "
            "as null, so the key must be present with a null value"
        )
    if resource.get("referenceKey") is not None:
        sys.exit(
            f"FAIL: client-side tool referenceKey must be null, got "
            f"{resource.get('referenceKey')!r} (other tool types set a resource key here)"
        )

    location = resource.get("location")
    if location != "solution":
        sys.exit(f'FAIL: client-side tool location must be "solution", got {location!r}')

    props = resource.get("properties")
    if not isinstance(props, dict):
        sys.exit(f"FAIL: client-side tool properties must be an object, got {props!r}")
    folder_path = props.get("folderPath")
    if folder_path != "solution_folder":
        sys.exit(
            f'FAIL: properties.folderPath must be "solution_folder", got {folder_path!r} '
            '— `uip agent validate` reports "solution tools must use folderPath"'
        )

    require_schema_object(resource, "inputSchema")
    require_schema_object(resource, "outputSchema")
    require_schema_object(resource, "settings")

    guardrail = resource.get("guardrail")
    if not isinstance(guardrail, dict) or not isinstance(
        guardrail.get("policies"), list
    ):
        sys.exit(
            f"FAIL: client-side tool guardrail must be an object carrying a policies "
            f"list (empty is fine), got {guardrail!r}"
        )

    print(
        f'OK: resource.json is $resourceType="tool", type="clientSide", name={name!r}, '
        f"id={rid}, referenceKey=null, location={location!r}, "
        f'folderPath="solution_folder", inputSchema/outputSchema/settings objects, '
        f"guardrail.policies list present ({len(guardrail['policies'])} policies)"
    )


def assert_prompt_references_tool(resource: dict, agent_json: "Path") -> None:
    """The tool must be named somewhere in the agent's messages.

    Declaring a tool makes it available; the system prompt is what makes the
    agent call it. A resource that is never referenced is dead weight, and the
    project still validates -- so it is checked here rather than by the CLI.

    Matched case-insensitively on the tool name anywhere in message content, so
    any reasonable phrasing of the Tools-slot line passes.
    """
    if not agent_json.is_file():
        sys.exit(f"FAIL: {agent_json} not found")
    agent = json.loads(agent_json.read_text())
    name = resource["name"]
    bodies = [
        m.get("content", "")
        for m in (agent.get("messages") or [])
        if isinstance(m, dict)
    ]
    if not any(name.lower() in (b or "").lower() for b in bodies):
        sys.exit(
            f"FAIL: no message in agent.json mentions the tool {name!r}. Declaring "
            "a tool makes it available; the system prompt is what makes the agent "
            "call it."
        )
    print(f"OK: agent.json messages reference the tool {name!r}")


def main() -> None:
    resources = load_resources()
    resource = find_client_side_resource(resources)
    assert_client_side_resource(resource)
    assert_prompt_references_tool(resource, ROOT / "agent.json")


if __name__ == "__main__":
    main()
