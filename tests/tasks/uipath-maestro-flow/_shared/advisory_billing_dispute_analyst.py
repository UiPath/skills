#!/usr/bin/env python3
"""STRUCTURAL gate for the `billing_dispute_analyst` port — the grounded agent.

v1 asserts two node types EXIST (`uipath.agent.autonomous` and
`uipath.agent.resource.context.index`) and then drives one `flow debug`. Two nodes
existing is weaker than the scenario: an index node sitting unconnected in the
flow satisfies it and grounds nothing. So this gate asserts the WIRING — the thing
the whole card exists to make possible:

1. **Exactly one inline agent**, no published-agent or script stand-in.
2. **Exactly one context-index resource**, whose node type carries a real,
   non-placeholder uuid and names the requested Billing Dispute SOP index.
3. **It is wired to the agent's own `context` port** — an edge out of the agent's
   `context` source port into the resource's `input` target port, which is the
   direction both definitions declare (`allowedTargets:
   uipath.agent.resource.context.*` on the agent; `allowedSources: … handleId:
   context` with `maxConnections: 1` on the resource). An index in the flow with no
   such edge is what v1's check cannot tell apart from a grounded one.
4. **It carries `inputs.source`** — a stable uuid the platform's validator
   requires. If optional `indexId`/`indexName` fields are emitted, they must agree
   with the node type and requested index.
5. **The agent is fed both inputs and its prompts reference them**, and both flow
   outputs are read FROM the agent step.
6. **Nothing about the answer is written in** — no determination or rationale
   literal.

Usage: advisory_billing_dispute_analyst.py [<FlowName>.flow]
"""
from advisory_flow_utils import (
    agent_prompt_text,
    end_bindings,
    fail,
    is_real_uuid,
    load_flow,
    node_dependencies,
    references_field,
    source_depends_on,
    successful_end_ids,
    unwrap,
)

INLINE = "uipath.agent.autonomous"
CONTEXT_PREFIX = "uipath.agent.resource.context.index."
INDEX_NAME = "Billing Dispute SOP Index"
IN_CONTRACT = ["disputeDescription", "invoiceNumber"]
OUT_CONTRACT = {"determination": "string", "rationale": "string"}


def main():
    path, f, nodes = load_flow("BillingDisputeAnalyst.flow")
    edges = f.get("edges") or []
    types_seen = sorted({str(n.get("type")) for n in nodes})

    # ── 1. exactly one INLINE agent ────────────────────────────────────────────
    agents = [n for n in nodes if n.get("type") == INLINE]
    if len(agents) != 1:
        fail(f"expected exactly ONE {INLINE} node, found {len(agents)}; node types: {types_seen}")
    published = [n for n in nodes if str(n.get("type", "")).startswith("uipath.core.agent.")]
    if published:
        fail(f"the flow wires a PUBLISHED agent ({[n['type'] for n in published]}); this scenario asks for an inline one")
    a = agents[0]
    ins = {k: unwrap(v) for k, v in (a.get("inputs") or {}).items()}

    # ── 2. exactly one context index, carrying a real index uuid ───────────────
    ctx = [n for n in nodes if str(n.get("type", "")).startswith(CONTEXT_PREFIX)]
    if len(ctx) != 1:
        fail(
            f"expected exactly ONE {CONTEXT_PREFIX}* node, found {len(ctx)}; node types: {types_seen}. "
            f"The agent has to be grounded on the tenant's semantic index"
        )
    c = ctx[0]
    type_parts = str(c["type"]).rsplit(".", 1)
    index_id = type_parts[-1] if len(type_parts) == 2 else ""
    if not is_real_uuid(index_id):
        fail(
            f"the context node's type is {c['type']!r}; the index identity belongs in the final type "
            f"segment as a real, non-placeholder uuid"
        )
    if "billing-dispute-sop-index" not in str(c["type"]).lower():
        fail(f"the context node's type {c['type']!r} does not name the requested {INDEX_NAME!r}")
    cin = {k: unwrap(v) for k, v in (c.get("inputs") or {}).items()}
    if cin.get("indexId") is not None and str(cin["indexId"]) != index_id:
        fail(f"the context node's inputs.indexId is {cin['indexId']!r}, not the type's uuid {index_id!r}")
    if cin.get("indexName") is not None and str(cin["indexName"]).strip() != INDEX_NAME:
        fail(f"the context node's inputs.indexName is {cin.get('indexName')!r}, not {INDEX_NAME!r}")
    src = str(cin.get("source") or "")
    if not is_real_uuid(src):
        fail(
            f"the context node's inputs.source is {src!r} — the platform's validator REQUIRES a stable "
            f"uuid there (MST-9265: \"requires a stable UUID at inputs.source\"), and a flow without one "
            f"fails `uip maestro flow validate`"
        )

    # ── 3. it is WIRED to the agent's context handle ───────────────────────────
    wired = [e for e in edges
             if e.get("sourceNodeId") == a["id"] and e.get("sourcePort") == "context"
             and e.get("targetNodeId") == c["id"] and e.get("targetPort") == "input"]
    if not wired:
        got = [f"{e.get('sourceNodeId')}:{e.get('sourcePort')}->{e.get('targetNodeId')}:{e.get('targetPort')}"
               for e in edges]
        fail(
            f"no edge joins the agent's `context` port to the index's `input` port — the index is in the "
            f"flow but grounds nothing, which is exactly what v1's node-type check cannot see. Edges: {got}"
        )

    # ── 4. the agent is fed both inputs, and the prompts reference them ────────
    input_variables = [v for v in (ins.get("agentInputVariables") or []) if isinstance(v, dict)]
    declared = [str(v.get("id") or v.get("name") or "") for v in input_variables]
    bindings = {
        str(v.get("id") or v.get("name") or ""): str(unwrap(v.get("binding")) or "")
        for v in input_variables
    }
    prompts = agent_prompt_text(path, a)
    for name in IN_CONTRACT:
        prompt_ref = any(token in prompts for token in (f"$vars.{name}", f"$vars.start.output.{name}", f"input.{name}"))
        binding_ref = any(references_field(binding, name) for binding in bindings.values())
        if not prompt_ref and not binding_ref:
            fail(
                f"the agent is never given {name!r}: agentInputVariables={bindings or '{}'} and neither "
                f"the Flow nor sidecar prompts reference it"
            )

    # ── 5. the declared contract, and both outputs read FROM the agent ─────────
    globs = {g["id"]: g for g in ((f.get("variables") or {}).get("globals") or [])}
    ins_g = {k: v for k, v in globs.items() if v.get("direction") == "in"}
    outs_g = {k: v for k, v in globs.items() if v.get("direction") == "out"}
    for name in IN_CONTRACT:
        if name not in ins_g:
            fail(f"the flow declares in-globals {sorted(ins_g)}; the contract asks for {name}")
    out_vars = [str(v.get("id") or v.get("name") or "") for v in (ins.get("agentOutputVariables") or [])
                if isinstance(v, dict)]
    for name, want in OUT_CONTRACT.items():
        if name not in outs_g:
            fail(f"the flow declares out-globals {sorted(outs_g)}; the contract asks for {name}")
        if outs_g[name].get("type") != want:
            fail(f"output {name} is declared {outs_g[name].get('type')!r}; the contract asks for {want}")
        if name not in out_vars:
            fail(f"the agent declares outputs {out_vars or '[]'}; it has to declare {name} — only a declared field is a checkable read")

    ends = [n for n in nodes if n.get("type") == "core.control.end"]
    if not ends:
        fail("the flow has no End node, so it declares no outputs")
    dependencies = node_dependencies(nodes)
    success_ends = successful_end_ids(nodes, edges, a["id"])
    if not success_ends:
        fail(f"no End node is reachable from agent {a['id']!r} without taking its error port")
    for name in OUT_CONTRACT:
        bindings_for_output = end_bindings(nodes, success_ends, name)
        if not bindings_for_output:
            fail(f"no successful End node binds an output named {name!r}")
        if not any(source_depends_on(value, a["id"], dependencies) for value in bindings_for_output):
            fail(
                f"successful output {name} has bindings {[str(unwrap(v)) for v in bindings_for_output]!r}, "
                f"and none depends on $vars.{a['id']}.output — the answer has to come FROM the agent"
            )

    # ── 6. no answer written in ────────────────────────────────────────────────
    # A determination is free prose, so there is no single literal to forbid — what
    # IS checkable is that neither output is a constant string at the End node.
    for name in OUT_CONTRACT:
        values = end_bindings(nodes, success_ends, name)
        if values and not any(source_depends_on(value, a["id"], dependencies) for value in values):
            fail(f"successful output {name} is constant — the agent's answer is what belongs there")

    print(
        f"{len(nodes)} nodes; one {INLINE} ({a['id']}) fed {declared or 'via prompt refs'}, "
        f"grounded on {c['id']} ({INDEX_NAME}, indexId {index_id[:8]}…, source {src[:8]}…) "
        f"via {a['id']}:context -> {c['id']}:input; outputs {sorted(OUT_CONTRACT)} read from {a['id']}"
    )


if __name__ == "__main__":
    main()
