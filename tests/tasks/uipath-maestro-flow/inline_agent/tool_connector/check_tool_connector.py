#!/usr/bin/env python3
"""Flow-file-first check: inline agent + Integration Service connector tool.

Grades the `.flow` as the source of truth (sidecar neither required nor
forbidden). `flow validate` checks NOTHING on connector nodes beyond
`inputs.source`, so this checker is the primary gate:

  1. Self-contained `uipath.agent.autonomous` node (string prompts, real
     system prompt, overridden model, lowercase-UUID `inputs.source`, no
     never-author artifacts) with canvas-form prompt tokens and a
     contract-conformant `agentInputVariables`.
  2. Agent definition present at the exact (type, typeVersion) with the
     inline-agent serviceType.
  3. A `uipath.agent.resource.tool.connector.<key>.<activity>` node wired
     to the agent's `tool` handle (dynamic type — discovered via registry
     search, not hand-constructed), with its definition present.
  4. Tool node carries the CLI-populated flow form: UUID `source`,
     non-empty `name`/`description`, and the `uip maestro flow node
     configure` output in `inputs.detail` (UUID connection identity,
     endpoint/method, configuration with `essentialConfiguration` — the
     block hand-authoring misses), and none of the derived resource.json
     fields (schemas/properties derive from `detail`).
  5. Both connection `bindings[]` rows (ConnectionId row pointing at
     `detail.connectionId`, FolderKey row with a UUID default) — validate
     does not enforce them for connector tools.
  6. Configure-generated solution-side artifacts: `bindings_v2.json` at
     the flow project root declaring a connection resource, and a
     connection resource JSON under
     `<solution>/resources/solution_folder/connection/`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.flow_inline_wiring import (  # noqa: E402
    load_json,
    find_autonomous_agent_node,
    assert_embedded_agent,
    assert_prompt_tokens,
    assert_agent_input_vars,
    assert_agent_sequence_wiring,
    assert_connector_bindings,
    assert_connector_inputs,
    assert_definition_present,
    find_flow_file,
    find_wired_resource,
    assert_resource_source_uuid,
)

INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
CONNECTOR_SERVICE_TYPE = "Intsvc.ActivityExecution"
FLOW_PATH = Path(os.getcwd()) / "ResearchFlowSol" / "ResearchFlow" / "ResearchFlow.flow"
TOOL_TYPE_PREFIX = "uipath.agent.resource.tool.connector."


def assert_bindings_v2(project_dir: Path) -> None:
    """Assert configure generated a project-root bindings_v2.json declaring a connection."""
    candidates = [
        p for p in sorted(project_dir.rglob("bindings_v2.json"))
        if ".agent-builder" not in p.parts
    ]
    if not candidates:
        sys.exit(
            f"FAIL: no bindings_v2.json under {project_dir} (outside "
            ".agent-builder/) — `uip maestro flow node configure` generates it; "
            "never author it by hand"
        )
    for path in candidates:
        data = load_json(path)
        resources = data.get("resources") if isinstance(data, dict) else None
        conn_rows = [
            r for r in (resources if isinstance(resources, list) else [])
            if isinstance(r, dict) and r.get("resource") == "connection"
        ]
        if conn_rows:
            print(f"OK: {path.name} declares a connection resource ({conn_rows[0].get('key')})")
            return
    sys.exit(
        f"FAIL: none of {[str(p) for p in candidates]} declares a resource of "
        "kind 'connection' — the connector tool's connection binding is missing"
    )


def assert_connection_resource(solution_dir: Path) -> None:
    """Assert the solution-level connection resource exists (configure-generated)."""
    connection_dir = solution_dir / "resources" / "solution_folder" / "connection"
    files = sorted(p for p in connection_dir.rglob("*.json") if p.is_file()) if connection_dir.is_dir() else []
    if not files:
        sys.exit(
            f"FAIL: no connection resource JSON under {connection_dir} — "
            "`uip maestro flow node configure` provisions it as part of the "
            "solution; never create it by hand"
        )
    for path in files:
        data = load_json(path)
        resource = data.get("resource") if isinstance(data, dict) else None
        if isinstance(resource, dict) and resource.get("kind") == "connection":
            print(
                f"OK: solution connection resource present "
                f"({path.relative_to(solution_dir)})"
            )
            return
    sys.exit(
        f"FAIL: none of {[str(p) for p in files]} has resource.kind "
        "'connection'"
    )


def main() -> None:
    flow_path = find_flow_file(FLOW_PATH)
    flow = load_json(flow_path)
    agent_node = find_autonomous_agent_node(flow)

    assert_embedded_agent(agent_node)
    assert_prompt_tokens(agent_node)
    assert_agent_input_vars(agent_node)
    assert_agent_sequence_wiring(flow, agent_node)
    print(f"OK: {agent_node['id']} is a self-contained embedded agent")

    definition = assert_definition_present(flow, agent_node)
    service_type = (definition.get("model") or {}).get("serviceType")
    if service_type != INLINE_AGENT_SERVICE_TYPE:
        sys.exit(
            f"FAIL: agent definitions[] entry has model.serviceType "
            f"{service_type!r}, expected {INLINE_AGENT_SERVICE_TYPE!r} — a "
            "missing serviceType means the definition was not copied verbatim "
            "from registry get"
        )
    print(f"OK: agent definition present with serviceType {INLINE_AGENT_SERVICE_TYPE!r}")

    tool_node = find_wired_resource(
        flow, agent_node, type_prefix=TOOL_TYPE_PREFIX, source_port="tool"
    )
    print(f"OK: {tool_node['type']} is wired to the agent's 'tool' handle")

    assert_resource_source_uuid(tool_node)
    detail = assert_connector_inputs(tool_node)
    print(
        f"OK: tool inputs carry the CLI-populated detail "
        f"(connection {detail['connectionId']}, endpoint {detail['endpoint']})"
    )

    tool_definition = assert_definition_present(flow, tool_node)
    tool_service_type = (tool_definition.get("model") or {}).get("serviceType")
    if tool_service_type != CONNECTOR_SERVICE_TYPE:
        sys.exit(
            f"FAIL: connector tool definitions[] entry has model.serviceType "
            f"{tool_service_type!r}, expected {CONNECTOR_SERVICE_TYPE!r} — the "
            "definition was not copied verbatim from registry get"
        )
    print(f"OK: tool definition present with serviceType {CONNECTOR_SERVICE_TYPE!r}")

    assert_connector_bindings(flow, detail["connectionId"])
    print("OK: both connection bindings[] rows present and pointing at the picked connection")

    project_dir = flow_path.parent
    assert_bindings_v2(project_dir)
    assert_connection_resource(project_dir.parent)


if __name__ == "__main__":
    main()
