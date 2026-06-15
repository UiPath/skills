#!/usr/bin/env python3
"""Inline agent + external escalation (ActionCenter) check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node whose `inputs.source`
     matches the sub-folder UUID of the inline agent under the flow
     project.
  2. Flow has a `uipath.agent.resource.escalation` node whose
     `inputs.source` matches the sub-folder UUID of the inline agent's
     resource (under `<inline-agent-uuid>/resources/`).
  3. Edge wires agent.escalation -> escalation.input.
  4. Inline agent dir has an escalation resource.json under its
     resources/ tree with:
       - $resourceType == "escalation"
       - id is a UUID-shaped string
       - isEnabled is truthy
       - channels contains at least one entry with
         type == "actionCenter" (lowercase) bound to the deployed
         "FraudEscalation" app: properties.appName == "FraudEscalation",
         properties.folderName == "Shared/uipath-agents/FraudEscalation"
         (the deployed Orchestrator folder of the app), and
         properties.resourceKey is a UUID-shaped non-empty string
         (copied from `uip solution resources list`'s `Key`)

  Note: the escalation resource.json format does not expose a
  `location` field — the solution-vs-external distinction is captured
  by where the ActionCenter app actually lives (external in Shared for
  F18) and by the test prompt wording.
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_inline_resource,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
    resolve_resource_source,
)

FLOW_PATH = Path(os.getcwd()) / "FraudFlowSol" / "FraudFlow" / "FraudFlow.flow"
ESCALATION_NODE_TYPE = "uipath.agent.resource.escalation"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

EXPECTED_APP_NAME = "FraudEscalation"
EXPECTED_FOLDER_NAME = "Shared/uipath-agents/FraudEscalation"


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    escalation_node = find_resource_node(flow, node_type=ESCALATION_NODE_TYPE)
    print(f"OK: flow has {agent_node['type']} and {escalation_node['type']} nodes")

    agent_source = (agent_node.get("inputs") or {}).get("source")
    if not isinstance(agent_source, str) or not UUID_RE.match(agent_source):
        sys.exit(
            f"FAIL: {agent_node['type']} inputs.source must be a UUID matching "
            f"the inline agent's sub-folder name, got {agent_source!r}"
        )
    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    if agent_dir.name != agent_source:
        sys.exit(
            f"FAIL: inputs.source UUID {agent_source!r} does not match "
            f"the inline agent sub-folder name {agent_dir.name!r}"
        )
    print(f"OK: autonomous node inputs.source={agent_source!r} matches inline agent sub-folder")

    escalation_source = resolve_resource_source(escalation_node)
    if not UUID_RE.match(escalation_source):
        sys.exit(
            f"FAIL: {escalation_node['type']} inputs.source must be a UUID matching "
            f"the inline agent resource's sub-folder name, got {escalation_source!r}"
        )

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="escalation",
        target_id=escalation_node["id"],
        target_port="input",
    )
    print("OK: agent 'escalation' handle is wired to escalation node's 'input' handle")

    path, data = find_inline_resource(
        agent_dir,
        lambda d: d.get("$resourceType") == "escalation",
        description='escalation resource ($resourceType=="escalation")',
    )
    if path.parent.name != escalation_source:
        sys.exit(
            f"FAIL: escalation node inputs.source UUID {escalation_source!r} does not match "
            f"the resource sub-folder name {path.parent.name!r}"
        )
    print(
        f"OK: escalation node inputs.source={escalation_source!r} matches resource sub-folder "
        f"({path.relative_to(Path(os.getcwd()))})"
    )

    rid = data.get("id")
    if not isinstance(rid, str) or not UUID_RE.match(rid):
        sys.exit(f"FAIL: escalation id missing or malformed at {path}: {rid!r}")
    if not data.get("isEnabled"):
        sys.exit(f"FAIL: escalation isEnabled must be truthy at {path}")
    channels = data.get("channels") or []
    ac = [
        c for c in channels
        if isinstance(c, dict)
        and c.get("type") == "actionCenter"
        and isinstance(c.get("name"), str)
        and c["name"].strip()
    ]
    if not ac:
        sys.exit(
            f'FAIL: {path} has no channel with type=="actionCenter" '
            f"and a non-empty name"
        )
    print(f"OK: escalation resource at {path.name} is valid (id={rid}, {len(ac)} actionCenter channel(s))")

    bound = [
        c for c in ac
        if (c.get("properties") or {}).get("appName") == EXPECTED_APP_NAME
    ]
    if not bound:
        sys.exit(
            f"FAIL: no actionCenter channel is bound to the deployed app "
            f"{EXPECTED_APP_NAME!r} (properties.appName) — got appNames: "
            f"{[(c.get('properties') or {}).get('appName') for c in ac]}"
        )
    props = bound[0].get("properties") or {}
    fname = props.get("folderName")
    if fname != EXPECTED_FOLDER_NAME:
        sys.exit(
            f"FAIL: channel properties.folderName should be {EXPECTED_FOLDER_NAME!r} "
            f"(the deployed Orchestrator folder of {EXPECTED_APP_NAME}), got {fname!r}"
        )
    rkey = props.get("resourceKey")
    if not isinstance(rkey, str) or not UUID_RE.match(rkey):
        sys.exit(
            f"FAIL: channel properties.resourceKey must be a UUID-shaped string "
            f"copied from `uip solution resources list`'s `Key`, got {rkey!r}"
        )
    print(
        f"OK: actionCenter channel is bound to appName={EXPECTED_APP_NAME!r}, "
        f"folderName={EXPECTED_FOLDER_NAME!r}, resourceKey={rkey!r}"
    )


if __name__ == "__main__":
    main()
