#!/usr/bin/env python3
"""Inline agent flow-wiring check.

Reads WeatherSol/WeatherFlow/WeatherFlow.flow (existence asserted by
a file_exists criterion in the task YAML) and verifies:

  1. The flow contains a `uipath.agent.autonomous` node.
  2. The node's `model.source` property points to an existing
     directory (the inline agent's UUID-named subdirectory).
  3. The node's `model.serviceType` is `Orchestrator.StartInlineAgentJob`
     (inline agents only — `StartAgentJob` is the solution-agent variant
     and would fail at runtime).
  4. The agent node is wired into the flow — at least one incoming edge
     on port `input` and at least one outgoing edge on port `success`.
"""

import json
import os
import sys
from pathlib import Path

INLINE_AGENT_NODE_TYPE = "uipath.agent.autonomous"
INLINE_AGENT_SERVICE_TYPE = "Orchestrator.StartInlineAgentJob"
FLOW_PATH = Path(os.getcwd()) / "WeatherSol" / "WeatherFlow" / "WeatherFlow.flow"


def main():
    try:
        flow = json.loads(FLOW_PATH.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {FLOW_PATH} is not valid JSON: {e}")

    nodes = flow.get("nodes") or []
    agent_nodes = [n for n in nodes if n.get("type") == INLINE_AGENT_NODE_TYPE]
    if not agent_nodes:
        sys.exit(
            f"FAIL: {FLOW_PATH.name} has no node of type "
            f"{INLINE_AGENT_NODE_TYPE!r}"
        )

    agent_node = agent_nodes[0]
    model = agent_node.get("model") or {}

    source = model.get("source")
    if not source:
        sys.exit(
            f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no model.source"
        )

    agent_dir = FLOW_PATH.parent / source
    if not agent_dir.is_dir():
        sys.exit(
            f"FAIL: model.source {source!r} does not point to an "
            f"existing directory ({agent_dir})"
        )

    print(
        f"OK: {INLINE_AGENT_NODE_TYPE} node's model.source points to "
        f"inline agent directory {source}"
    )

    service_type = model.get("serviceType")
    if service_type != INLINE_AGENT_SERVICE_TYPE:
        sys.exit(
            f"FAIL: {INLINE_AGENT_NODE_TYPE} node's model.serviceType is "
            f"{service_type!r}, expected {INLINE_AGENT_SERVICE_TYPE!r}. "
            f"'Orchestrator.StartAgentJob' is the solution-agent variant "
            f"and must not be used for inline agents."
        )
    print(f"OK: model.serviceType is {INLINE_AGENT_SERVICE_TYPE!r}")

    agent_id = agent_node.get("id")
    if not agent_id:
        sys.exit(f"FAIL: {INLINE_AGENT_NODE_TYPE} node has no id")

    edges = flow.get("edges") or []
    incoming_input = [
        e for e in edges
        if e.get("targetNodeId") == agent_id and e.get("targetPort") == "input"
    outgoing_success = [
        e for e in edges
        if e.get("sourceNodeId") == agent_id and e.get("sourcePort") == "success"
    ]
    if not incoming_input:
        sys.exit(
            f"FAIL: agent node {agent_id!r} has no incoming edge on "
            f"targetPort 'input' — node is not wired into the flow"
        )
    if not outgoing_success:
        sys.exit(
            f"FAIL: agent node {agent_id!r} has no outgoing edge on "
            f"sourcePort 'success' — flow has no continuation after the agent"
        )
    print(
        f"OK: agent node is wired — {len(incoming_input)} incoming on "
        f"'input', {len(outgoing_success)} outgoing on 'success'"
    )


if __name__ == "__main__":
    main()
