#!/usr/bin/env python3
"""Every agent-resource node in the Flow has the agent-project file that makes it live.

An inline agent's capability is TWO artifacts. The `.flow` carries a
`uipath.agent.resource.*` node wired to one of the agent's handles; the agent
PROJECT carries the same resource as `<agent-source>/resources/<resource-id>/resource.json`
(or, equivalently, an entry in `agent.json`'s `resources[]` — `uip agent refresh`
reads both into one list). The runtime's view comes from the project: nothing in
the CLI derives an agent resource from the flow, and `uip agent refresh` strips and
re-derives the NODE from the file, never the other way round.

So the node alone is inert, and nothing else in the ladder can see it. Measured
2026-09-24 on this very task: a flow with a context-index node and no
`resource.json` passed `uip maestro flow validate` with `Status: Valid` and no
warnings, ran to completion under `flow debug`, returned a non-empty
determination — and its agent answered *"the required Billing Dispute SOP excerpts
are not present in the available context or tools"*. Every criterion scored 1.00.
Debugging the same artifact by hand, the agent invented its policy basis ("Per
STANDARD Billing Dispute SOP guidelines … TYPICALLY 5-10 business days") where a
grounded build quotes the index ("SOP AR-SOP-014, §5.4 - Incorrect Rate").

A grader cannot read a rationale and tell retrieval from invention. It CAN read
this, offline, with no tenant: the join is an id, so it is exact.

EXEMPT: `tool.connector.*`. `uip agent refresh --inline-in-flow` generates those
resource.json files FROM the flow's connector nodes (uipcli's
`flow-connector-tool-service.ts`, ported from flow-core's `agent-connector-tool`
mapper), so their absence before a refresh is by design and not a defect. Every
other family — context, mcp, a2a, the per-instance tool kinds, escalation — has no
such generator.

Usage (from a task's run_command, cwd = sandbox root):
    python3 $REFERENCE_DIR/_shared/check_agent_resource_sidecars.py [<FlowName>.flow]

Exit 0 on pass (including a flow with no agent-resource nodes at all, which this
check has nothing to say about); exit 1 with a `FAIL:` line naming each node whose
resource is missing, and where it was looked for.
"""
from __future__ import annotations

import json
from pathlib import Path

from advisory_flow_utils import fail, load_flow, unwrap

AGENT_TYPES = ("uipath.agent.autonomous", "uipath.agent.conversational")
RESOURCE_PREFIX = "uipath.agent.resource."
# Family -> the `$resourceType` its resource.json must declare. Keyed by the node
# type segment after the prefix, longest match first so `tool.connector` is tested
# before `tool`.
RESOURCE_TYPES = (
    ("context.", "context"),
    ("tool.mcp.", "mcp"),
    ("tool.", "tool"),
    ("escalation.", "escalation"),
    ("memory.", None),  # a FEATURE (features/<id>/feature.json), not a resource
)
# See the module docstring: the CLI generates these from the flow itself.
GENERATED_FROM_FLOW = ("tool.connector.",)


def _family(node_type: str) -> str:
    return node_type[len(RESOURCE_PREFIX):]


def _expected_resource_type(family: str) -> str | None:
    for prefix, resource_type in RESOURCE_TYPES:
        if family.startswith(prefix):
            return resource_type
    return None


def _declared_ids(agent_dir: Path) -> dict[str, str]:
    """Resource id -> `$resourceType`, from both places `uip agent refresh` reads.

    The join is the resource's `id` FIELD, not its directory name. Real agent
    projects name the directory after the resource — `resources/CountSources/`,
    `resources/WebSearch/`, `resources/SupportKnowledge/` — and carry a uuid in
    `id`; `compile` happens to name it for the uuid. Keying on the directory would
    pass the SDK's own output and fail every designer-authored project, so fall
    back to the directory name only when a resource declares no `id`.
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
    flow_path, flow, nodes = load_flow("*.flow")
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
        if expected_type is None or family.startswith(GENERATED_FROM_FLOW):
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
