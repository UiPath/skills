#!/usr/bin/env python3
"""Conversational agent + client-side tool check.

Asserts the same resource shape as the standalone client_side_tool task, plus
the part specific to this scenario: the tool's `outputSchema` must model what
the *user* supplies, since on pre-built surfaces the form is generated from it.

Shape (per `clientSideToolResourceSchema`):
  - $resourceType == "tool", type == "clientSide" (lowercase — "ClientSide" is
    the Python spelling and is rejected by the packager)
  - referenceKey null, location "solution",
    properties.folderPath "solution_folder"
  - settings, guardrail, inputSchema, outputSchema all present

Scenario:
  - outputSchema declares at least one property — an empty object would render
    an empty form and collect nothing.
  - outputSchema is not a bare passthrough (`result` / `output` / `data` as the
    only field), which is the API-response-envelope habit this test exists to
    catch.

The property names themselves are the agent's choice and are NOT pinned.
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.getcwd()) / "ReviewSol" / "ReviewAgent"
RESOURCES = ROOT / "resources"

PASSTHROUGH_NAMES = {"result", "output", "data", "response", "value"}


def load_resources() -> list:
    if not RESOURCES.is_dir():
        sys.exit(f"FAIL: {RESOURCES} does not exist — the agent authored no resources")
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

    for path, data in resources:
        if str(data.get("type") or "").lower() == "clientside":
            sys.exit(
                f'FAIL: {path.relative_to(ROOT.parent)} has type {data.get("type")!r}; '
                'the schema literal is "clientSide" (lowercase c).'
            )

    found = sorted({str(d.get("type")) for _, d in resources if d.get("type")})
    sys.exit(
        f'FAIL: no client-side tool (type=="clientSide") found under {RESOURCES}. '
        f"Tool types present: {found or 'none'}"
    )


def assert_shape(resource: dict) -> None:
    if resource.get("$resourceType") != "tool":
        sys.exit(
            f'FAIL: $resourceType should be "tool", got {resource.get("$resourceType")!r}'
        )

    for field in ("name", "description"):
        value = resource.get(field)
        if not isinstance(value, str) or not value.strip():
            sys.exit(f"FAIL: client-side tool {field} missing or empty: {value!r}")

    if "referenceKey" not in resource or resource.get("referenceKey") is not None:
        sys.exit(
            f"FAIL: client-side tool referenceKey must be present and null, got "
            f"{resource.get('referenceKey')!r}"
        )

    if resource.get("location") != "solution":
        sys.exit(
            f'FAIL: location must be "solution", got {resource.get("location")!r}'
        )

    props = resource.get("properties")
    if not isinstance(props, dict) or props.get("folderPath") != "solution_folder":
        sys.exit(
            f'FAIL: properties.folderPath must be "solution_folder", got '
            f"{(props or {}).get('folderPath')!r}"
        )

    for field in ("inputSchema", "outputSchema", "settings"):
        if not isinstance(resource.get(field), dict):
            sys.exit(f"FAIL: {field} must be an object, got {resource.get(field)!r}")

    guardrail = resource.get("guardrail")
    if not isinstance(guardrail, dict) or not isinstance(
        guardrail.get("policies"), list
    ):
        sys.exit(
            f"FAIL: guardrail must carry a policies list (empty is fine), got {guardrail!r}"
        )


def assert_output_schema_is_a_form(resource: dict) -> None:
    out_schema = resource["outputSchema"]
    properties = out_schema.get("properties")

    if not isinstance(properties, dict) or not properties:
        sys.exit(
            "FAIL: outputSchema declares no properties. On pre-built surfaces the "
            "form is generated from outputSchema, so an empty one renders an empty "
            f"form and collects nothing. Got: {json.dumps(out_schema)[:200]}"
        )

    names = set(properties)
    if names <= PASSTHROUGH_NAMES:
        sys.exit(
            f"FAIL: outputSchema looks like an API response envelope (fields: "
            f"{sorted(names)}). For a client-side tool the outputSchema models what "
            "the user supplies — name the fields after the decision being captured."
        )

    print(
        f"OK: outputSchema declares {len(properties)} field(s): {sorted(names)}; "
        f"required={out_schema.get('required') or []}"
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
    resource = find_client_side_resource(load_resources())
    assert_shape(resource)
    assert_output_schema_is_a_form(resource)
    assert_prompt_references_tool(resource, ROOT / "agent.json")
    print(f'OK: conversational agent carries a well-shaped client-side tool '
          f'{resource["name"]!r}')


if __name__ == "__main__":
    main()
