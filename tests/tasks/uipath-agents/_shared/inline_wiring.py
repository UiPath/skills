"""Shared helpers for uipath-agents inline-agent flow-wiring checks.

Used by Batch 3 tests (F12.*, F13, F14, F15.*, F17, F18, F19) that verify
the combined shape of:
  - a `uipath.agent.autonomous` inline agent node in a `.flow` file,
  - a `uipath.agent.resource.<kind>.*` resource node in the same flow,
  - an edge wiring the autonomous node's `tool` / `context` / `escalation`
    handle (source) to the resource node's `input` handle (target), per
    `agent-flow-integration.md`,
  - a `resource.json` inside the inline agent's UUID subdirectory (pointed
    to by `model.source` on the autonomous node).

Import pattern in a check script:

    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from _shared.inline_wiring import (  # noqa: E402
        load_json,
        find_autonomous_agent_node,
        find_resource_node,
        resolve_inline_agent_dir,
        assert_edge,
    )
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

AUTONOMOUS_NODE_TYPE = "uipath.agent.autonomous"


def load_json(path: Path) -> dict:
    """Load a JSON file. Exit with FAIL on missing or invalid JSON."""
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def find_autonomous_agent_node(flow: dict) -> dict:
    """Return the first `uipath.agent.autonomous` node in the flow."""
    nodes = flow.get("nodes") or []
    matches = [n for n in nodes if n.get("type") == AUTONOMOUS_NODE_TYPE]
    if not matches:
        sys.exit(f"FAIL: flow has no node of type {AUTONOMOUS_NODE_TYPE!r}")
    node = matches[0]
    if not node.get("id"):
        sys.exit(f"FAIL: {AUTONOMOUS_NODE_TYPE} node has no id")
    return node


def find_resource_node(
    flow: dict,
    *,
    node_type: str | None = None,
    node_type_prefix: str | None = None,
) -> dict:
    """Find the first resource node by exact type or type-prefix match.

    Use `node_type` for well-defined types (e.g.
    `uipath.agent.resource.tool.rpa`). Use `node_type_prefix` for wildcards
    (e.g. `uipath.agent.resource.tool.agent.` for agent-as-tool nodes,
    which include a `<process-key>` suffix, or `uipath.agent.resource.mcp.`
    for MCP server nodes).
    """
    nodes = flow.get("nodes") or []
    if node_type is not None:
        matches = [n for n in nodes if n.get("type") == node_type]
        descriptor = f"type {node_type!r}"
    elif node_type_prefix is not None:
        matches = [
            n for n in nodes
            if isinstance(n.get("type"), str)
            and n["type"].startswith(node_type_prefix)
        ]
        descriptor = f"type starting with {node_type_prefix!r}"
    else:
        sys.exit("FAIL: find_resource_node requires node_type or node_type_prefix")
    if not matches:
        sys.exit(f"FAIL: flow has no node with {descriptor}")
    node = matches[0]
    if not node.get("id"):
        sys.exit(f"FAIL: node with {descriptor} has no id")
    return node


def resolve_inline_agent_dir(flow_path: Path, agent_node: dict) -> Path:
    """Return the inline agent's UUID subdirectory (from `model.source`)."""
    source = (agent_node.get("model") or {}).get("source")
    if not source:
        sys.exit(f"FAIL: {AUTONOMOUS_NODE_TYPE} node has no model.source")
    agent_dir = flow_path.parent / source
    if not agent_dir.is_dir():
        sys.exit(
            f"FAIL: model.source {source!r} does not point to an existing "
            f"directory ({agent_dir})"
        )
    return agent_dir


def assert_edge(
    flow: dict,
    *,
    source_id: str,
    source_port: str,
    target_id: str,
    target_port: str,
) -> None:
    """Assert that an edge wires source_id:source_port -> target_id:target_port."""
    edges = flow.get("edges") or []
    matches = [
        e for e in edges
        if e.get("sourceNodeId") == source_id
        and e.get("sourcePort") == source_port
        and e.get("targetNodeId") == target_id
        and e.get("targetPort") == target_port
    ]
    if not matches:
        sys.exit(
            f"FAIL: no edge wires source node {source_id!r} port "
            f"{source_port!r} to target node {target_id!r} port "
            f"{target_port!r}."
        )
