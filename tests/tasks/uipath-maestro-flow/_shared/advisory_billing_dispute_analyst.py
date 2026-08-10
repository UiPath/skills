#!/usr/bin/env python3
"""STRUCTURAL gate for the `billing_dispute_analyst` port — the grounded agent.

v1 asserts two node types EXIST (`uipath.agent.autonomous` and
`uipath.agent.resource.context.index`) and then drives one `flow debug`. Two nodes
existing is weaker than the scenario: an index node sitting unconnected in the
flow satisfies it and grounds nothing. So this gate asserts the WIRING — the thing
the whole card exists to make possible:

1. **Exactly one inline agent**, no published-agent or script stand-in.
2. **Exactly one context-index resource**, whose node type carries the REAL
   index's uuid — the identity is in the type, so a wrong uuid is a node type the
   tenant has never heard of.
3. **It is wired to the agent's own `context` port** — an edge out of the agent's
   `context` source port into the resource's `input` target port, which is the
   direction both definitions declare (`allowedTargets:
   uipath.agent.resource.context.*` on the agent; `allowedSources: … handleId:
   context` with `maxConnections: 1` on the resource). An index in the flow with no
   such edge is what v1's check cannot tell apart from a grounded one.
4. **It carries `inputs.source`** — a stable uuid the platform's validator
   REQUIRES (MST-9265: *"requires a stable UUID at inputs.source"*), plus the
   index's own `indexId`/`indexName`.
5. **The agent is fed both inputs and its prompts reference them**, and both flow
   outputs are read FROM the agent step.
6. **Nothing about the answer is written in** — no determination or rationale
   literal.

Usage: check_billing_dispute_analyst.py <FlowName>.flow
"""
import json
import re
import sys

INLINE = "uipath.agent.autonomous"
CONTEXT_PREFIX = "uipath.agent.resource.context.index."
INDEX_ID = "cc45b9b4-dbf6-47b3-40ac-08debc0cec5b"
INDEX_NAME = "Billing Dispute SOP Index"
IN_CONTRACT = ["disputeDescription", "invoiceNumber"]
OUT_CONTRACT = {"determination": "string", "rationale": "string"}


def fail(msg):
    sys.exit(f"FAIL: {msg}")


def unwrap(v):
    if isinstance(v, dict):
        for k in ("expression", "source"):
            if k in v:
                return unwrap(v[k])
    return v


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "BillingDisputeAnalyst.flow"
    raw = open(path, encoding="utf-8").read()
    f = json.loads(raw)
    nodes, edges = f["nodes"], (f.get("edges") or [])
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

    # ── 2. exactly one context index, carrying the REAL index's uuid ───────────
    ctx = [n for n in nodes if str(n.get("type", "")).startswith(CONTEXT_PREFIX)]
    if len(ctx) != 1:
        fail(
            f"expected exactly ONE {CONTEXT_PREFIX}* node, found {len(ctx)}; node types: {types_seen}. "
            f"The agent has to be grounded on the tenant's semantic index"
        )
    c = ctx[0]
    if not str(c["type"]).endswith(INDEX_ID):
        fail(
            f"the context node's type is {c['type']!r}; the index's identity is IN the node type and this "
            f"one does not end with the real index uuid {INDEX_ID!r} — a wrong uuid is a node type the "
            f"tenant has never heard of"
        )
    cin = {k: unwrap(v) for k, v in (c.get("inputs") or {}).items()}
    if str(cin.get("indexId") or "") != INDEX_ID:
        fail(f"the context node's inputs.indexId is {cin.get('indexId')!r}, not {INDEX_ID!r}")
    if str(cin.get("indexName") or "").strip() != INDEX_NAME:
        fail(f"the context node's inputs.indexName is {cin.get('indexName')!r}, not {INDEX_NAME!r}")
    src = str(cin.get("source") or "")
    if not re.match(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", src):
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
    declared = [str(v.get("id") or v.get("name") or "") for v in (ins.get("agentInputVariables") or [])
                if isinstance(v, dict)]
    prompts = " ".join(str(ins.get(k) or "") for k in ("systemPrompt", "userPrompt"))
    if "$vars." not in prompts:
        fail(
            f"neither prompt references a flow value ($vars.…): {prompts[:160]!r}. The platform derives an "
            f"inline agent's deployed input list by SCANNING the prompts"
        )
    for name in IN_CONTRACT:
        if name not in declared and f"$vars.{name}" not in prompts and f"$vars.start.output.{name}" not in prompts:
            fail(f"the agent is never given {name!r}: agentInputVariables={declared or '[]'} and no prompt references it")

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
    bound = {}
    for n in ends:
        for k, v in (n.get("outputs") or {}).items():
            bound[k] = str(unwrap(v))
    aref = f"$vars.{a['id']}.output"
    via = {n["id"] for n in nodes if aref in json.dumps(n.get("inputs") or {})}
    for name in OUT_CONTRACT:
        s = bound.get(name)
        if s is None:
            fail(f"no End node binds an output named {name!r}; it binds {sorted(bound)}")
        if aref not in s and not any(f"$vars.{x}" in s for x in via):
            fail(f"output {name} is {s!r}, and nothing it reads references {aref} — the answer has to come FROM the agent")

    # ── 6. no answer written in ────────────────────────────────────────────────
    # A determination is free prose, so there is no single literal to forbid — what
    # IS checkable is that neither output is a constant string at the End node.
    for name in OUT_CONTRACT:
        s = bound.get(name, "")
        if re.match(r'^"[^"]*"$', s.strip()) or (s.strip() and "$vars." not in s):
            fail(f"output {name} is the constant {s!r} — the agent's answer is what belongs there")

    print(
        f"{len(nodes)} nodes; one {INLINE} ({a['id']}) fed {declared or 'via prompt refs'}, "
        f"grounded on {c['id']} ({INDEX_NAME}, indexId {INDEX_ID[:8]}…, source {src[:8]}…) "
        f"via {a['id']}:context -> {c['id']}:input; outputs {sorted(OUT_CONTRACT)} read from {a['id']}"
    )


if __name__ == "__main__":
    main()
