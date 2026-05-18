#!/usr/bin/env python3
"""Inline agent + context (semantic index) check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node and a
     `uipath.agent.resource.context.index` node.
  2. Edge wires agent.context -> context.input.
  3. Inline agent dir has at least one resource.json under
     `resources/**/` (UUID-named per inline-in-flow.md) with:
       - $resourceType == "context"
       - contextType == "index"
       - indexName == "ProductKnowledge"
       - settings.retrievalMode in {semantic, structured, deepRAG, batchTransform}
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_inline_resource,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = Path(os.getcwd()) / "KnowledgeFlowSol" / "KnowledgeFlow" / "KnowledgeFlow.flow"
CONTEXT_INDEX_NODE_TYPE = "uipath.agent.resource.context.index"
VALID_RETRIEVAL_MODES = {"semantic", "structured", "deepRAG", "batchTransform"}


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    context_node = find_resource_node(flow, node_type=CONTEXT_INDEX_NODE_TYPE)
    print(f"OK: flow has {agent_node['type']} and {context_node['type']} nodes")

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="context",
        target_id=context_node["id"],
        target_port="input",
    )
    print("OK: agent 'context' handle is wired to context.index node's 'input' handle")

    agent_dir = resolve_inline_agent_dir(FLOW_PATH, agent_node)
    resource_path, resource = find_inline_resource(
        agent_dir,
        lambda d: (
            d.get("$resourceType") == "context"
            and d.get("contextType") == "index"
            and d.get("indexName") == "ProductKnowledge"
        ),
        description='context index "ProductKnowledge"',
    )
    print(
        f'OK: {resource_path.relative_to(Path(os.getcwd()))} is '
        f'$resourceType="context", contextType="index", indexName="ProductKnowledge"'
    )

    settings = resource.get("settings") or {}
    mode = settings.get("retrievalMode")
    if mode not in VALID_RETRIEVAL_MODES:
        sys.exit(
            f"FAIL: settings.retrievalMode must be one of {sorted(VALID_RETRIEVAL_MODES)}, "
            f"got {mode!r}"
        )
    print(f"OK: settings.retrievalMode is {mode!r}")


if __name__ == "__main__":
    main()
