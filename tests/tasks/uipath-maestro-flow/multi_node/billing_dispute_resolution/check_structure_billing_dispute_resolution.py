#!/usr/bin/env python3
"""Structural check for the full DevCon BillingDisputeResolution flow.

No execution — pure shape + WIRING asserts on the agent-built `.flow`. Existence
of the right node *types* is necessary but not sufficient: a flow with every
required node left unconnected, or wired in the wrong order, would reproduce the
node inventory without reproducing the orchestration. So this check verifies the
actual directed topology against the reference flow's shape:

  Required nodes (anti-hardcode — each targets a tenant resource a Script node
  cannot fake):
    - IxP extraction              (uipath.ixp.*)                 invoice parsing
    - Data Service query          (…dataservice.query-entity-records)  ERP/CRM lookup
    - inline autonomous agent     (uipath.agent.autonomous)      analyst + writer
    - context index               (uipath.agent.resource.context.index.*)  SOP grounding
    - API-workflow function       (uipath.core.api-workflow.*)   financial posting
    - switch + decision           (core.logic.switch / .decision) routing
    - end                         (core.control.end)             RETURNS the outcome

  Topology the reference flow pins (each is wiring, not mere presence):
    1. trigger → IxP → 2× Data Service → analyst agent   (the ingest pipeline is
       connected end-to-end; no orphaned resource nodes).
    2. the SOP context index is ATTACHED to an agent      (a `[context]` edge),
       not present-but-dangling.
    3. analyst agent → switch with ≥3 case branches       (routes on recommendedAction).
    4. switch → decision; decision → BOTH the API-workflow path AND an end node
       (the approve→post / reject→return outcomes).
    5. API-workflow → a SECOND, distinct agent (the writer) → end.
    6. every control-flow leaf is a `core.control.end`    (no path dead-ends).

  Edits this task requires (the reason it differs from the raw DevCon flow):
    - NO human-in-the-loop node  — the HITL approval gate was removed.
    - NO send-email node         — the flow must NOT email; it RETURNS instead.
    - declares ≥2 `out` variables — the resolution is returned to the caller.
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


# ── pure topology assertions (unit-testable against the reference) ─────────────


def assert_topology(nodes_by_id, edges):
    """Assert the directed wiring matches the reference orchestration.

    Pure: takes the parsed graph, calls ``sys.exit`` on the first violation.
    Identifies roles by node TYPE + reachability, never by node id/label, so a
    correct agent build with its own naming still passes.
    """

    def of(sub):
        s = sub.lower()
        return {i for i, n in nodes_by_id.items() if s in str(n.get("type", "")).lower()}

    adj = {}
    for e in edges:
        adj.setdefault(e.get("sourceNodeId"), []).append(e.get("targetNodeId"))

    def reach(starts):
        seen, stack = set(), list(starts)
        while stack:
            x = stack.pop()
            for y in adj.get(x, ()):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return seen

    def need(cond, msg):
        if not cond:
            sys.exit(f"FAIL: topology — {msg}")

    triggers = of("core.trigger")
    ixp = of("uipath.ixp")
    ds = of("dataservice.query-entity-records")
    agents = of("uipath.agent.autonomous")
    ctx = of("uipath.agent.resource.context.index")
    switch = of("core.logic.switch")
    decision = of("core.logic.decision")
    api = of("uipath.core.api-workflow")
    ends = of("core.control.end")

    need(triggers, "no trigger node (core.trigger.*) — flow has no entry point")
    need(len(ds) >= 2, f"expected ≥2 Data Service query nodes (ERP+CRM), found {len(ds)}")
    need(len(agents) >= 2, f"expected ≥2 inline agents (analyst+writer), found {len(agents)}")

    from_trigger = reach(triggers)

    # 1. Ingest pipeline is connected: IxP and both Data Service lookups are
    #    reachable from the trigger (not orphaned islands).
    need(ixp & from_trigger, "IxP node not reachable from the trigger")
    need(ds <= from_trigger, "a Data Service query node is not reachable from the trigger")

    # analyst = an agent the switch is reachable FROM (it routes on the agent's output)
    need(switch, "no switch node (core.logic.switch)")
    analysts = {a for a in agents if switch & reach({a})}
    need(analysts, "no agent flows into the switch — analyst agent is not wired before routing")

    # ingest → analyst: the analyst is downstream of BOTH Data Service lookups.
    for q in ds:
        need(analysts & reach({q}), "analyst agent is not downstream of a Data Service lookup")

    # 2. SOP context index is attached to an agent (a context edge), not dangling.
    need(ctx, "no context-index node (SOP grounding)")
    attached = any(
        ({e.get("sourceNodeId"), e.get("targetNodeId")} & ctx)
        and ({e.get("sourceNodeId"), e.get("targetNodeId")} & agents)
        for e in edges
    )
    need(attached, "context index is present but not attached to any agent (no grounding edge)")

    # 3. switch fans out to ≥3 branches (escalate / auto-resolve / reject).
    for sw in switch:
        outs = [e for e in edges if e.get("sourceNodeId") == sw]
        need(len(outs) >= 3, f"switch has {len(outs)} branches, expected ≥3 (escalate/auto/reject)")

    # 4. switch → decision; decision → BOTH api-workflow AND an end node.
    need(decision, "no decision node (core.logic.decision) for the approval gate")
    need(decision & reach(switch), "decision (approval) node is not downstream of the switch")
    need(api, "no API-workflow node (financial posting)")
    from_decision = reach(decision)
    need(api & from_decision, "API-workflow not reachable from the approval decision (approve path)")
    need(ends & from_decision, "no end node reachable from the approval decision (reject path)")

    # 5. api-workflow → a SECOND distinct agent (writer) → end.
    from_api = reach(api)
    writers = agents & from_api
    need(writers, "no agent downstream of the API-workflow — writer agent is not wired after posting")
    need(writers - analysts, "writer and analyst resolve to the same agent — expected two distinct agents")
    need(ends & from_api, "no end node reachable after the API-workflow / writer (path does not return)")

    # 6. every control-flow leaf is an end node (resource nodes like the context
    #    index are legitimately leaves and are excluded).
    resource_leaves = ctx
    for nid, n in nodes_by_id.items():
        if adj.get(nid):
            continue  # has outgoing edges
        if nid in resource_leaves or nid in ends:
            continue
        sys.exit(
            f"FAIL: topology — node {nid!r} (type {n.get('type','')!r}) is a dead end "
            f"with no outgoing edge and is not a core.control.end"
        )

    need(len(ends) >= 2, f"expected ≥2 end nodes (a resolution path + ≥1 rejection path), found {len(ends)}")


def _assert_absent(nodes_by_id, substr, why):
    hits = [n.get("type", "") for n in nodes_by_id.values()
            if substr.lower() in str(n.get("type", "")).lower()]
    if hits:
        sys.exit(f"FAIL: {why} — found node type(s) {sorted(set(hits))} matching {substr!r}")


def main():
    # Positive: the full orchestration is present. Each hint targets a resource
    # node that a hardcoded Script cannot substitute for.
    assert_flow_has_node_type(["uipath.ixp"])
    assert_flow_has_node_type(["dataservice.query-entity-records"])
    assert_flow_has_node_type(["uipath.agent.autonomous"])
    assert_flow_has_node_type(["uipath.agent.resource.context.index"])
    assert_flow_has_node_type(["uipath.core.api-workflow"])
    assert_flow_has_node_type(["core.logic.switch"])
    assert_flow_has_node_type(["core.logic.decision"])
    assert_flow_has_node_type(["core.control.end"])
    print("OK: full orchestration present (IxP, Data Service, 2 inline agents, "
          "SOP context index, API-workflow, switch, decision, end)")

    project_dir = find_project_dir()
    nodes_by_id, edges, globals_list = _flow_graph(project_dir)

    # Wiring — the orchestration is connected in the right order, not just present.
    assert_topology(nodes_by_id, edges)
    print("OK: topology wired correctly (trigger→IxP→Data Service→analyst→switch→"
          "decision→API-workflow→writer→end; SOP index attached to an agent)")

    # Edit 1 — HITL removed.
    _assert_absent(nodes_by_id, "human-in-the-loop", "HITL node must be removed")
    # Edit 2 — no terminal email; the flow returns instead of sending.
    _assert_absent(nodes_by_id, "send-email", "flow must NOT send email — return the outcome instead")
    print("OK: no human-in-the-loop node and no send-email node")

    # Edit 2 (cont.) — the outcome is RETURNED as flow output variables.
    out_vars = [v["id"] for v in globals_list if v.get("direction") == "out"]
    if len(out_vars) < 2:
        sys.exit(
            f"FAIL: flow declares {len(out_vars)} `out` variable(s); expected ≥2 — the "
            "resolution must be RETURNED to the caller (e.g. determination / rationale / "
            "resolution body), not emailed."
        )
    print(f"OK: flow returns its outcome via out variables {out_vars}")


if __name__ == "__main__":
    main()
