#!/usr/bin/env python3
"""Inline agent + external escalation (ActionCenter) check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.escalation` node.
  2. Edge wires agent.escalation -> escalation.input.
  3. Inline agent dir has at least one escalation resource.json under
     its resources/ tree with:
       - $resourceType == "escalation"
       - id is a UUID-shaped string
       - isEnabled is truthy
       - channels contains at least one entry with
         name == type == "ActionCenter"

  Note: the escalation resource.json format does not expose a
  `location` field — the solution-vs-external distinction is captured
  by where the ActionCenter app actually lives (external in Shared for
  F18) and by the test prompt wording.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = Path(os.getcwd()) / "FraudFlowSol" / "FraudFlow" / "FraudFlow.flow"
ESCALATION_NODE_TYPE = "uipath.agent.resource.escalation"


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    escalation_node = find_resource_node(flow, node_type=ESCALATION_NODE_TYPE)
    print(f"OK: flow has {agent_node['type']} and {escalation_node['type']} nodes")

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="escalation",
        target_id=escalation_node["id"],
        target_port="input",
    )
    print("OK: agent 'escalation' handle is wired to escalation node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resources_dir = agent_dir / "resources"
    if not resources_dir.is_dir():
        sys.exit(f"FAIL: {resources_dir} does not exist — no resources/ directory")

    for path in sorted(resources_dir.rglob("resource.json")):
        data = load_json(path)
        if data.get("$resourceType") != "escalation":
            continue
        rid = data.get("id")
        if not isinstance(rid, str) or "-" not in rid:
            sys.exit(f"FAIL: escalation id missing or malformed at {path}: {rid!r}")
        if not data.get("isEnabled"):
            sys.exit(f"FAIL: escalation isEnabled must be truthy at {path}")
        channels = data.get("channels") or []
        ac = [
            c for c in channels
            if isinstance(c, dict)
            and c.get("name") == "ActionCenter"
            and c.get("type") == "ActionCenter"
        ]
        if not ac:
            sys.exit(
                f"FAIL: {path} has no channel with name=='ActionCenter' "
                f"and type=='ActionCenter'"
            )
        print(f"OK: escalation resource at {path.name} is valid (id={rid}, {len(ac)} ActionCenter channel(s))")
        return

    sys.exit(
        f'FAIL: no escalation resource found under {resources_dir} — '
        'expected at least one resource.json with $resourceType="escalation"'
    )


if __name__ == "__main__":
    main()
