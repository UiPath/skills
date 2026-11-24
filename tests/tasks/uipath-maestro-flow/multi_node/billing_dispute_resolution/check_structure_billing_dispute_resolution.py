#!/usr/bin/env python3
"""Structural check for the DevCon BillingDisputeResolution flow.

No execution: shape and wiring asserts on the agent-built `.flow`. The prompt
asks for the orchestration in business terms and leaves the routing to the
agent. "Automatically approve anything requiring manager review" can be built
as a decision node that defaults to Approved, or as the manager-review case
going straight to posting. Both are correct, so this check does not pin the
reference's switch + decision layout. It asserts the wiring the request implies:

  1. IxP and both entity reads are reachable from the trigger. Either
     entity-read shape counts (`flow_check.ENTITY_QUERY_HINTS`): tenant
     availability decides which one the agent can build.
  2. An analyst agent sits after both entity reads and before the
     FinancialPostingFunction API workflow.
  3. The SOP context index is attached to an agent.
  4. A second, distinct agent (the writer) is downstream of the API workflow,
     and an end node follows it.
  5. A rejection path: an end node is reachable from the analyst without
     passing through the API workflow (a rejected dispute is not posted).
  6. Every control-flow leaf is a `core.control.end`.
  7. No human-in-the-loop node and no send-email node.
  8. At least two `out` variables (the resolution is returned, not sent).
"""
import glob
import json
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.flow_check import (  # noqa: E402
    ENTITY_QUERY_HINTS,
    assert_flow_has_any_node_type,
    assert_flow_has_node_type,
    find_project_dir,
)


# ── graph loading ─────────────────────────────────────────────────────────────


def _flow_graph(project_dir):
    """Merge nodes + edges across every `.flow` under the project into one graph.

    Returns ``(nodes_by_id, edges, globals_list)``. The flow is authored as a
    single `.flow`, but globbing keeps this robust to multi-file projects.
    """
    nodes_by_id, edges, globals_list = {}, [], []
    for path in glob.glob(os.path.join(project_dir, "**/*.flow"), recursive=True):
        with open(path) as f:
            flow = json.load(f)
        for n in flow.get("nodes") or []:
            nodes_by_id[n["id"]] = n
        edges.extend(flow.get("edges") or [])
        globals_list.extend((flow.get("variables") or {}).get("globals") or [])
    return nodes_by_id, edges, globals_list


# ── topology ─────────────────────────────────────────────────────────────────


def assert_topology(nodes_by_id, edges):
    """Assert the wiring the request implies. Exits on the first violation.

    Roles are found by node type and reachability, never by id or label.
    """

    def of(sub):
        s = sub.lower()
        return {i for i, n in nodes_by_id.items() if s in str(n.get("type", "")).lower()}

    adj = {}
    for e in edges:
        adj.setdefault(e.get("sourceNodeId"), []).append(e.get("targetNodeId"))

    def reach(starts, blocked=frozenset()):
        seen, stack = set(), [s for s in starts if s not in blocked]
        while stack:
            x = stack.pop()
            for y in adj.get(x, ()):
                if y not in seen and y not in blocked:
                    seen.add(y)
                    stack.append(y)
        return seen

    def need(cond, msg):
        if not cond:
            sys.exit(f"FAIL: topology — {msg}")

    triggers = of("core.trigger")
    ixp = of("uipath.ixp")
    reads = {i for hint in ENTITY_QUERY_HINTS for i in of(hint)}
    # The writer may be an existing tenant agent (`uipath.core.agent.<key>`).
    agents = of("uipath.agent.autonomous") | of("uipath.core.agent.")
    ctx = of("uipath.agent.resource.context.index")
    api = of("uipath.core.api-workflow")
    ends = of("core.control.end")

    need(triggers, "no trigger node (core.trigger.*)")
    need(ixp, "no IxP extraction node (uipath.ixp.*)")
    need(len(reads) >= 2, f"expected ≥2 entity-read nodes (ERP+CRM), found {len(reads)}")
    need(len(agents) >= 2, f"expected ≥2 agents (analyst+writer), found {len(agents)}")
    need(api, "no API-workflow node (FinancialPostingFunction)")

    from_trigger = reach(triggers)
    need(ixp & from_trigger, "IxP node not reachable from the trigger")
    need(reads <= from_trigger, "an entity-read node is not reachable from the trigger")

    # The analyst runs after both lookups and before posting; the writer, which
    # is also downstream of the lookups, runs after posting.
    analysts = {
        a for a in agents
        if all(a in reach({q}) for q in reads) and api & reach({a})
    }
    need(analysts, "no agent sits between the entity reads and the API workflow (analyst not wired)")

    need(ctx, "no context-index node (SOP grounding)")
    attached = any(
        ({e.get("sourceNodeId"), e.get("targetNodeId")} & ctx)
        and ({e.get("sourceNodeId"), e.get("targetNodeId")} & agents)
        for e in edges
    )
    need(attached, "context index is present but not attached to any agent")

    from_api = reach(api)
    writers = (agents & from_api) - analysts
    need(writers, "no second agent downstream of the API workflow (writer not wired after posting)")
    need(ends & reach(writers), "no end node after the writer agent (the resolution path does not return)")

    need(
        ends & reach(analysts, blocked=frozenset(api)),
        "no end node reachable from the analyst without the API workflow (no rejection path)",
    )

    for nid, n in nodes_by_id.items():
        if adj.get(nid) or nid in ctx or nid in ends:
            continue
        sys.exit(
            f"FAIL: topology — node {nid!r} (type {n.get('type', '')!r}) is a dead end "
            "with no outgoing edge and is not a core.control.end"
        )


def _assert_absent(nodes_by_id, substr, why):
    hits = [n.get("type", "") for n in nodes_by_id.values()
            if substr.lower() in str(n.get("type", "")).lower()]
    if hits:
        sys.exit(f"FAIL: {why} — found node type(s) {sorted(set(hits))} matching {substr!r}")


def main():
    # Each hint targets a resource node that a hardcoded Script cannot stand in for.
    assert_flow_has_node_type(["uipath.ixp"])
    assert_flow_has_any_node_type(ENTITY_QUERY_HINTS)
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_has_node_type(["uipath.agent.resource.context.index"])
    assert_flow_has_node_type(["uipath.core.api-workflow"])
    assert_flow_has_node_type(["core.control.end"])
    print("OK: IxP, entity read, inline agent, SOP context index, API workflow and end nodes present")

    nodes_by_id, edges, globals_list = _flow_graph(find_project_dir())

    assert_topology(nodes_by_id, edges)
    print("OK: trigger→IxP→ERP/CRM→analyst (SOP index attached)→posting→writer→end, "
          "plus a rejection path that skips posting")

    _assert_absent(nodes_by_id, "human-in-the-loop", "the manager review is auto-approved, no HITL node")
    _assert_absent(nodes_by_id, "send-email", "the email is drafted, not sent")
    print("OK: no human-in-the-loop node and no send-email node")

    out_vars = [v["id"] for v in globals_list if v.get("direction") == "out"]
    if len(out_vars) < 2:
        sys.exit(f"FAIL: flow declares {len(out_vars)} `out` variable(s); expected ≥2")
    print(f"OK: flow returns its outcome via out variables {out_vars}")


if __name__ == "__main__":
    main()
