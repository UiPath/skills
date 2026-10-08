"""Shared helpers for uipath-agents inline-agent flow-wiring checks.

Used by inline-agent tests that verify the combined shape of:
  - a `uipath.agent.autonomous` inline agent node in a `.flow` file,
  - a `uipath.agent.resource.<kind>.*` resource node in the same flow,
  - an edge wiring the autonomous node's `tool` / `context` / `escalation`
    handle (source) to the resource node's `input` handle (target), per
    `agent-flow-integration.md`,
  - a `resource.json` inside the inline agent's UUID subdirectory (pointed
    to by `inputs.source` on the autonomous node).

Source identity for every inline-agent-related node (autonomous agent +
attached resource nodes) lives at `inputs.source`. There is no `model.source`
fallback — checks fail loudly when the legacy location is used so authors
regenerate the fixture.

Import pattern in a check script:

    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from _shared.inline_wiring import (  # noqa: E402
        load_json,
        find_autonomous_agent_node,
        find_resource_node,
        resolve_inline_agent_dir,
        resolve_resource_source,
        find_inline_resource,
        assert_edge,
    )
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

AUTONOMOUS_NODE_TYPE = "uipath.agent.autonomous"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
# The builder SDK compiles an unresolved connection to this stub id (it
# reaches dispatch as a 401), so a UUID check alone would accept it.
STUB_CONNECTION_ID_RE = re.compile(r"^0{8}-0{4}-0{4}-0{4}-0{8}[0-9a-fA-F]{4}$")


def is_real_uuid(value: object) -> bool:
    """True for a UUID string that is not the all-zero stub family."""
    return (
        isinstance(value, str)
        and UUID_RE.match(value) is not None
        and STUB_CONNECTION_ID_RE.match(value) is None
    )


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
    """Return the inline agent's UUID subdirectory.

    Reads the projectId from `inputs.source` on the node instance. The
    legacy `model.source` location is no longer accepted — fixtures using it
    fail loudly so the author regenerates them with the current convention.
    """
    inputs = agent_node.get("inputs") or {}
    source = inputs.get("source")
    if not source or not isinstance(source, str):
        sys.exit(
            f"FAIL: {AUTONOMOUS_NODE_TYPE} node has no inputs.source"
        )
    agent_dir = flow_path.parent / source
    if not agent_dir.is_dir():
        sys.exit(
            f"FAIL: inputs.source {source!r} does not point to an existing "
            f"directory ({agent_dir})"
        )
    assert_inline_agent_definition(agent_dir)
    return agent_dir


def assert_inline_agent_definition(agent_dir: Path) -> dict:
    """Fail unless `agent_dir/agent.json` is a usable inline agent definition.

    The node is a shell: the prompts and model live only in `agent.json`, so
    an empty or prompt-less file gives a flow that validates but runs an
    agent with no instructions. Checks: valid JSON, `type == "lowCode"`,
    `id` equal to the directory name, a non-empty `settings.model`, and a
    non-empty `system` and `user` message.

    Interim: `uip agent validate --inline-in-flow` is the real contract, but
    it rejects every SDK-compiled agent today (UiPath/flow-builder-sdk#962).
    Replace this with that command as a gate once #962 is fixed.
    """
    path = agent_dir / "agent.json"
    data = load_json(path)
    if data.get("type") != "lowCode":
        sys.exit(f"FAIL: {path} type should be 'lowCode', got {data.get('type')!r}")
    if data.get("id") != agent_dir.name:
        sys.exit(
            f"FAIL: {path} id {data.get('id')!r} does not match its directory "
            f"name {agent_dir.name!r}"
        )
    model = (data.get("settings") or {}).get("model")
    if not isinstance(model, str) or not model.strip():
        sys.exit(f"FAIL: {path} has no settings.model")
    for role in ("system", "user"):
        contents = [
            m.get("content") for m in data.get("messages") or []
            if isinstance(m, dict) and m.get("role") == role
        ]
        if not any(isinstance(c, str) and c.strip() for c in contents):
            sys.exit(f"FAIL: {path} has no non-empty {role!r} message")
    print(f"OK: {path.name} defines the inline agent (model {model!r}, system + user prompts)")
    return data


def resolve_resource_source(node: dict) -> str:
    """Return the resource UUID from a resource node's `inputs.source`.

    Resource nodes (`uipath.agent.resource.tool.*`,
    `uipath.agent.resource.escalation`, `uipath.agent.resource.context.*`)
    carry their `<RES_UUID>` at `inputs.source`, identical to the autonomous
    agent. The legacy `model.source` location is no longer accepted.
    """
    inputs = node.get("inputs") or {}
    source = inputs.get("source")
    if not source or not isinstance(source, str):
        node_type = node.get("type", "<unknown>")
        sys.exit(
            f"FAIL: {node_type} node has no inputs.source"
        )
    return source


def find_inline_resource(
    agent_dir: Path,
    predicate,
    *,
    description: str,
) -> tuple[Path, dict]:
    """Locate a resource.json inside an inline agent's resources/ tree by content.

    Inline agents use UUID-named resource subdirectories
    (`resources/<RES_UUID>/resource.json` per inline-in-flow.md), so checks
    cannot hardcode a directory name. This helper iterates every
    `resources/**/resource.json` under `agent_dir` and returns the first one
    whose loaded JSON satisfies `predicate(data) -> bool`.

    On miss it exits with FAIL referencing the `description` (e.g.
    "context index 'ProductKnowledge'").
    """
    resources_dir = agent_dir / "resources"
    if not resources_dir.is_dir():
        sys.exit(f"FAIL: {resources_dir} does not exist — no resources/ directory")
    for path in sorted(resources_dir.rglob("resource.json")):
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if predicate(data):
            return path, data
    sys.exit(
        f"FAIL: no resource.json matching {description} under {resources_dir} — "
        "inline agents use UUID-named resource subdirectories, so the test "
        "matches on content (not directory name)"
    )


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


# Accepted resource.json shapes for an inline agent's deployed-resource tool.
# For an inline-in-flow agent the tool's tenant folder is carried by the
# flow's top-level `bindings[]` (`b<Name>FolderPath`), not by resource.json.
# Each external pair below ran its tenant tool Successful in a live
# `uip maestro flow debug`; a control with no `resources/` faulted.
#   - process (RPA):        https://github.com/UiPath/flow-builder-sdk/issues/922#issuecomment-6000881513
#   - agent:                https://github.com/UiPath/flow-builder-sdk/issues/922#issuecomment-6001964622
#   - api, maestro:         https://github.com/UiPath/flow-builder-sdk/issues/922#issuecomment-6026668870
# The deployed path (pack + deploy + run) is not witnessed for either shape:
# UiPath/flow-builder-sdk#964.
# Solution-local tools: "" and "solution_folder" derive byte-identical solution
# files, and both pass `uip agent validate --inline-in-flow` after
# `uip agent refresh --inline-in-flow`.
INLINE_SOLUTION_FOLDER_PATHS = ("", "solution_folder")


def external_tool_shapes(expected_folder: str) -> set[tuple[str, str]]:
    """The (location, properties.folderPath) pairs witnessed live (see above)."""
    return {("solution", ""), ("external", expected_folder)}


def assert_external_tool_shape(resource: dict, expected_folder: str) -> tuple[str, str]:
    """Fail unless the tool's (location, folderPath) is a witnessed pair."""
    pair = (resource.get("location"), (resource.get("properties") or {}).get("folderPath"))
    allowed = external_tool_shapes(expected_folder)
    if pair not in allowed:
        sys.exit(
            f"FAIL: external tool (location, properties.folderPath) = {pair!r}; "
            f"expected one of {sorted(allowed)}"
        )
    return pair


def assert_tool_folder_binding(flow: dict, resource_name: str, expected_folder: str) -> dict:
    """Return the flow's top-level `folderPath` binding for `resource_name`.

    Fails unless `flow.bindings[]` has a `folderPath` entry for the resource
    (id `b<Name>FolderPath`, or a `resourceKey` ending in `.<Name>`) whose
    `default` is `expected_folder`. This is where an inline-in-flow tool's
    tenant folder lives (see the evidence link above).
    """
    candidates = []
    for b in flow.get("bindings") or []:
        if not isinstance(b, dict):
            continue
        if b.get("propertyAttribute") != "folderPath" and b.get("name") != "folderPath":
            continue
        key = str(b.get("resourceKey") or "")
        if b.get("id") == f"b{resource_name}FolderPath" or key.endswith(f".{resource_name}"):
            candidates.append(b)
    for b in candidates:
        if b.get("default") == expected_folder:
            return b
    found = [(b.get("id"), b.get("default")) for b in candidates]
    sys.exit(
        f"FAIL: flow bindings[] has no folderPath binding for {resource_name!r} with "
        f"default {expected_folder!r} (found: {found or 'none'})"
    )

