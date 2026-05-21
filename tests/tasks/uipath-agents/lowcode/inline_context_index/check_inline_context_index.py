#!/usr/bin/env python3
"""Inline agent + context (semantic index) check.

Validates:
  1. Flow has a `uipath.agent.autonomous` node whose `inputs.source`
     matches the sub-folder UUID of the inline agent under the flow
     project.
  2. Flow has a `uipath.agent.resource.context.index.<name>.<uuid>`
     node whose `model.source` matches the sub-folder UUID of the
     inline agent's resource (under `<inline-agent-uuid>/resources/`).
  3. Edge wires agent.context -> context.input.
  4. Inline agent dir has at least one resource.json under
     `resources/**/` (UUID-named per inline-in-flow.md) for the
     "UiPathAgentsProductKnowledge" external semantic index with:
       - $resourceType == "context"
       - contextType == "index"
       - name == "UiPathAgentsProductKnowledge"
       - indexName == "UiPathAgentsProductKnowledge"
       - folderPath == "Shared/uipath-agents"
       - settings.retrievalMode in {semantic, structured, deepRAG, batchTransform}
  5. Inline agent's agent.json declares a required `question:string`
     input and an `answer:string` output (matching the standalone
     context_index schema).
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from _shared.inline_wiring import (  # noqa: E402
    assert_edge,
    find_autonomous_agent_node,
    find_inline_resource,
    find_resource_node,
    load_json,
    resolve_inline_agent_dir,
)

FLOW_PATH = (
    Path(os.getcwd()) / "KnowledgeFlowSol" / "KnowledgeFlow" / "KnowledgeFlow.flow"
)
CONTEXT_INDEX_NODE_TYPE_PREFIX = "uipath.agent.resource.context.index."
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

EXPECTED_INDEX_NAME = "UiPathAgentsProductKnowledge"
EXPECTED_FOLDER_PATH = "Shared/uipath-agents"
VALID_RETRIEVAL_MODES = {"semantic", "structured", "deepRAG", "batchTransform"}


def assert_input_shape(schema: dict) -> None:
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(props, dict) or "question" not in props:
        sys.exit(
            f"FAIL: agent.json inputSchema.properties missing 'question'; "
            f"got {list(props) if isinstance(props, dict) else props!r}"
        )
    q = props["question"]
    if not isinstance(q, dict) or q.get("type") != "string":
        sys.exit(
            f"FAIL: agent.json inputSchema.properties.question.type should be 'string', got {q!r}"
        )
    required = schema.get("required")
    if not isinstance(required, list) or "question" not in required:
        sys.exit(
            f"FAIL: agent.json inputSchema.required must contain 'question', got {required!r}"
        )
    print("OK: agent.json inputSchema declares required question:string")


def assert_output_shape(schema: dict) -> None:
    props = schema.get("properties") if isinstance(schema, dict) else None
    if not isinstance(props, dict) or "answer" not in props:
        sys.exit(
            f"FAIL: agent.json outputSchema.properties missing 'answer'; "
            f"got {list(props) if isinstance(props, dict) else props!r}"
        )
    a = props["answer"]
    if not isinstance(a, dict) or a.get("type") != "string":
        sys.exit(
            f"FAIL: agent.json outputSchema.properties.answer.type should be 'string', got {a!r}"
        )
    print("OK: agent.json outputSchema declares answer:string")


def main() -> None:
    flow = load_json(FLOW_PATH)
    agent_node = find_autonomous_agent_node(flow)
    context_node = find_resource_node(
        flow, node_type_prefix=CONTEXT_INDEX_NODE_TYPE_PREFIX
    )
    print(f"OK: flow has {agent_node['type']} and {context_node['type']} nodes")

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
    print(
        f"OK: autonomous node inputs.source={agent_source!r} matches inline agent sub-folder"
    )

    context_source = (context_node.get("model") or {}).get("source")
    if not isinstance(context_source, str) or not UUID_RE.match(context_source):
        sys.exit(
            f"FAIL: {context_node['type']} model.source must be a UUID matching "
            f"the inline agent resource's sub-folder name, got {context_source!r}"
        )

    assert_edge(
        flow,
        source_id=agent_node["id"],
        source_port="context",
        target_id=context_node["id"],
        target_port="input",
    )
    print("OK: agent 'context' handle is wired to context.index node's 'input' handle")

    resource_path, resource = find_inline_resource(
        agent_dir,
        lambda d: (
            d.get("$resourceType") == "context"
            and d.get("contextType") == "index"
            and d.get("indexName") == EXPECTED_INDEX_NAME
        ),
        description=f'context index "{EXPECTED_INDEX_NAME}"',
    )
    if resource_path.parent.name != context_source:
        sys.exit(
            f"FAIL: context node model.source UUID {context_source!r} does not match "
            f"the resource sub-folder name {resource_path.parent.name!r}"
        )
    print(
        f"OK: context node model.source={context_source!r} matches resource sub-folder "
        f"({resource_path.relative_to(Path(os.getcwd()))})"
    )

    name = resource.get("name")
    if name != EXPECTED_INDEX_NAME:
        sys.exit(
            f"FAIL: resource.json name should be {EXPECTED_INDEX_NAME!r} "
            f"(matching the deployed index), got {name!r}"
        )
    folder_path = resource.get("folderPath")
    if folder_path != EXPECTED_FOLDER_PATH:
        sys.exit(
            f"FAIL: resource.json folderPath should be {EXPECTED_FOLDER_PATH!r} "
            f"(the deployed Orchestrator folder of the index), got {folder_path!r}"
        )
    print(
        f'OK: resource.json is $resourceType="context", contextType="index", '
        f"name=indexName={EXPECTED_INDEX_NAME!r}, folderPath={EXPECTED_FOLDER_PATH!r}"
    )

    settings = resource.get("settings") or {}
    mode = settings.get("retrievalMode")
    if mode not in VALID_RETRIEVAL_MODES:
        sys.exit(
            f"FAIL: settings.retrievalMode must be one of {sorted(VALID_RETRIEVAL_MODES)}, "
            f"got {mode!r}"
        )
    print(f"OK: settings.retrievalMode is {mode!r}")

    agent_json = load_json(agent_dir / "agent.json")
    assert_input_shape(agent_json.get("inputSchema") or {})
    assert_output_shape(agent_json.get("outputSchema") or {})


if __name__ == "__main__":
    main()
