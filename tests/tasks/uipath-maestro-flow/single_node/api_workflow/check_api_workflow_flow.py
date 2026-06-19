#!/usr/bin/env python3
"""NameToAge API-workflow flow: structural assertions.

The previous checker ran ``uip maestro flow debug``. That command is a
live-tenant operation by CLI design — it uploads the flow to Studio Web,
creates a debug instance in PIMS, and polls until completion. The
maestro-flow skill itself bans this exact pattern:

    SKILL.md: "Never run `flow debug` as a validation step — debug
    executes the flow with real side effects. Use `flow validate` for
    checking correctness."

Under no-tenant or transient conditions, PIMS returned ``PIMS-100003`` /
500 against the published binding
``Shared/uipath-maestro-flow/NameToAge APIWF.API Workflow``, sinking the
score for skill-flow-api-workflow even when the agent built a perfectly
valid flow.

Move to a fully static structural check that asserts the flow has the
right shape for an API-workflow invocation:

1. An ``uipath.core.api-workflow.*`` node is present (delegated to
   ``assert_flow_has_node_type`` so we share the manifest-aware glob).
2. The flow declares at least one published API-workflow binding —
   ``bindings[]`` entry with ``resource == "process"``,
   ``resourceSubType == "Api"``, and a non-empty ``resourceKey``.
3. The api-workflow node sets the prompt-required input
   ``inputs.name == "tomasz"`` (case-insensitive).
"""

from __future__ import annotations

import glob
import json
import os
import sys
from pathlib import Path
from typing import Any, NoReturn

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.flow_check import assert_flow_has_node_type  # noqa: E402


FLOW_GLOB = "NameToAge/NameToAge/NameToAge.flow"
API_WORKFLOW_NODE_PREFIX = "uipath.core.api-workflow"


def fail(msg: str) -> NoReturn:
    sys.exit(f"FAIL: {msg}")


def load_flow() -> dict[str, Any]:
    matches = glob.glob(FLOW_GLOB)
    if not matches:
        fail(f"No flow file matching {FLOW_GLOB}")
    path = Path(matches[0])
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f"{path} is not valid JSON: {exc}")


def assert_api_workflow_binding(flow: dict[str, Any]) -> None:
    bindings = flow.get("bindings")
    if not isinstance(bindings, list) or not bindings:
        fail("Flow has no top-level bindings[] — API workflow resource is not wired up.")
    api_bindings = [
        b for b in bindings
        if isinstance(b, dict)
        and b.get("resource") == "process"
        and b.get("resourceSubType") == "Api"
        and b.get("resourceKey")
    ]
    if not api_bindings:
        fail(
            "No published API-workflow binding found "
            "(expected bindings[] entry with resource='process', "
            "resourceSubType='Api', and a non-empty resourceKey)."
        )


def assert_name_input(flow: dict[str, Any]) -> None:
    nodes = flow.get("nodes")
    if not isinstance(nodes, list):
        fail("Flow has no nodes[] array.")
    api_nodes = [
        n for n in nodes
        if isinstance(n, dict)
        and isinstance(n.get("type"), str)
        and n["type"].lower().startswith(API_WORKFLOW_NODE_PREFIX)
    ]
    if not api_nodes:
        fail(f"No api-workflow node (type starts with '{API_WORKFLOW_NODE_PREFIX}') found.")
    for node in api_nodes:
        inputs = node.get("inputs") or {}
        name = inputs.get("name")
        if isinstance(name, str) and name.strip().lower() == "tomasz":
            return
    fail("API workflow node does not set inputs.name = 'tomasz' as the prompt requires.")


def main() -> None:
    assert_flow_has_node_type([API_WORKFLOW_NODE_PREFIX])
    flow = load_flow()
    assert_api_workflow_binding(flow)
    assert_name_input(flow)
    print("OK: API workflow node present, published binding wired, inputs.name='tomasz'")


if __name__ == "__main__":
    main()
