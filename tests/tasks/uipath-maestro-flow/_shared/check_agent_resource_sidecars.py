#!/usr/bin/env python3
"""Every agent-resource node in the Flow has the agent-project file that makes it live.

An inline agent's capability is TWO artifacts. The `.flow` carries a
`uipath.agent.resource.*` node wired to one of the agent's handles; the agent
PROJECT carries the same resource as `<agent-source>/resources/<dir>/resource.json`
(or, equivalently, an entry in `agent.json`'s `resources[]` — `uip agent refresh`
reads both into one list). On the CLI path the project is the runtime's only view:
refresh strips the node and re-derives it from the file, so a node with no file is
inert, and validate, debug and a non-empty answer all still pass.

Measured 2026-09-24 on this task: a flow with a context-index node and no
`resource.json` scored 1.00 on every criterion while its agent answered that the
SOP excerpts were not in its context or tools. A grader cannot read a rationale
and tell retrieval from invention; it can read this, offline, because the join is
an id.

GATED families are the ones a correct build is expected to carry a file for:
`context.`, and the deployed-resource tool kinds. Everything else is exempt with
a reason, because gating a family nothing can emit is a criterion no one passes:

  * `tool.connector.*` — `uip agent refresh --inline-in-flow` GENERATES it from
    the flow's own connector node (uipcli `flow-connector-tool-service.ts`), so
    its absence before a refresh is by design.
  * `tool.ixp.*`, `tool.clientside*` — writing the file makes `flow validate`
    FAIL after refresh (measured in flow-builder-sdk#806): refresh strips the node
    and cannot rebuild the configuration it carried.
  * `tool.mcp.*`, `tool.a2a*`, `tool.builtin.*` — need a tenant read or a
    toolType mapping the compiler does not have.
  * `escalation*` — needs the Action Center app's ActionSchema and recipients.
  * `memory.*` — a FEATURE (`features/<id>/feature.json`), not a resource.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_agent_resource_sidecars.py <FlowName>.flow

Exit 0 on pass (including a flow with no gated resource nodes at all); exit 1
with a `FAIL:` line naming each node whose resource is missing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from advisory_flow_utils import fail, load_flow, unwrap

AGENT_TYPES = ("uipath.agent.autonomous", "uipath.agent.conversational")
RESOURCE_PREFIX = "uipath.agent.resource."
# Node-type prefix -> the `$resourceType` its file must declare. Only the families
# a correct build is expected to carry a file for; see the module docstring for
# why each of the others is left out. Longest prefix first is not needed here —
# these do not overlap — but the deployed-tool namespaces are listed in full so a
# new one has to be added deliberately rather than swept in by a bare `tool.`.
GATED = (
    ("context.", "context"),
    ("tool.process.", "tool"),
    ("tool.api.", "tool"),
    ("tool.processorchestration.", "tool"),
    ("tool.flow.", "tool"),
    ("tool.agent.", "tool"),
    ("tool.function.", "tool"),
)


def _family(node_type: str) -> str:
    return node_type[len(RESOURCE_PREFIX):]


def _expected_resource_type(family: str) -> str | None:
    """The `$resourceType` this node's file must declare, or None when exempt."""
    for prefix, resource_type in GATED:
        if family.startswith(prefix):
            return resource_type
    return None


def _declared_ids(agent_dir: Path) -> dict[str, str]:
    """Resource id -> `$resourceType`, from both places `uip agent refresh` reads.

    Join on the `id` field; the directory name is only a fallback. Real projects
    name the directory after the resource (`resources/CountSources/`) and carry a
    uuid in `id`, while `compile` names it for the uuid.
    """
    declared: dict[str, str] = {}
    for resource_file in sorted(agent_dir.glob("resources/*/resource.json")):
        try:
            body = json.loads(resource_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            fail(f"{resource_file} is not readable JSON: {error}")
        resource_id = str(body.get("id") or "") or resource_file.parent.name
        declared[resource_id] = str(body.get("$resourceType") or "")
    agent_json = agent_dir / "agent.json"
    if agent_json.is_file():
        try:
            body = json.loads(agent_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            body = {}
        for entry in body.get("resources") or []:
            if isinstance(entry, dict) and entry.get("id"):
                declared.setdefault(str(entry["id"]), str(entry.get("$resourceType") or ""))
    return declared


def main() -> None:
    # POP the name off argv and hand it to `load_flow` as the name to find, the
    # way every sibling checker pins one. Left in argv it would be read as a
    # literal path instead, and the YAML cannot know the generated nesting.
    flow_path, flow, nodes = load_flow(sys.argv.pop(1) if len(sys.argv) > 1 else "*.flow")
    edges = flow.get("edges") or []
    project_dir = flow_path.parent

    resources = [n for n in nodes if str(n.get("type", "")).startswith(RESOURCE_PREFIX)]
    if not resources:
        print(f"{flow_path}: no agent-resource nodes; nothing to join")
        return

    agents = {n["id"]: n for n in nodes if n.get("type") in AGENT_TYPES}
    # resource node id -> the agent that owns it, via the edge the handle declares
    # (out of the agent, into the resource's `input`).
    owner = {
        e["targetNodeId"]: e["sourceNodeId"]
        for e in edges
        if e.get("targetNodeId") in {n["id"] for n in resources} and e.get("sourceNodeId") in agents
    }

    problems: list[str] = []
    checked: list[str] = []
    for node in resources:
        family = _family(str(node["type"]))
        expected_type = _expected_resource_type(family)
        if expected_type is None:
            continue
        agent_id = owner.get(node["id"])
        if agent_id is None:
            problems.append(
                f"{node['id']} ({family}) is joined to no agent handle, so no agent project can own it"
            )
            continue
        agent_source = str(unwrap((agents[agent_id].get("inputs") or {}).get("source")) or "")
        if not agent_source:
            problems.append(f"agent {agent_id!r} carries no inputs.source, so its project has no directory")
            continue
        resource_id = str(unwrap((node.get("inputs") or {}).get("source")) or "")
        if not resource_id:
            problems.append(f"{node['id']} ({family}) carries no inputs.source, so nothing joins it to a resource")
            continue
        agent_dir = project_dir / agent_source
        declared = _declared_ids(agent_dir)
        if resource_id not in declared:
            problems.append(
                f"{node['id']} ({family}) points at resource {resource_id} and the agent project declares "
                f"{sorted(declared) or 'none'} — expected a resource declaring id {resource_id} under "
                f"{agent_source}/resources/ "
                f"(or an agent.json resources[] entry with that id). The node validates without it and the "
                f"runtime never sees the resource"
            )
            continue
        if declared[resource_id] != expected_type:
            problems.append(
                f"{node['id']} ({family}) resolves to resource {resource_id}, which declares "
                f"$resourceType {declared[resource_id]!r}; a {family} node needs {expected_type!r}"
            )
            continue
        checked.append(f"{node['id']} -> {agent_source}/resources/{resource_id} ({expected_type})")

    if problems:
        fail("; ".join(problems))
    if not checked:
        print(f"{flow_path}: {len(resources)} agent-resource node(s), all of families this check exempts")
        return
    print(f"{flow_path}: {len(checked)} agent resource(s) joined to the agent project: " + "; ".join(checked))


if __name__ == "__main__":
    main()
