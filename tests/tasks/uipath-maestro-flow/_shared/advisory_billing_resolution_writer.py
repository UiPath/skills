#!/usr/bin/env python3
"""STRUCTURAL gate for the `billing_resolution_writer` port.

v1 asserts one node type exists (`uipath.agent.autonomous`) and then drives one
`flow debug`, scoping its behaviour assertions to the `emailBody` output — which
its own docstring explains is the point: matching the whole debug payload is a
false pass, because the trigger echoes `invoiceNumber` back into the outputs, so
the invoice string is "present" even when the agent refuses to draft OR the End
node never maps the agent's result.

This gate carries that lesson into the structure, and adds what no behaviour rung
can see:

1. **Exactly one inline agent**, and no stand-in. A `script` that string-formats
   an email satisfies every behaviour rung — that is the one substitution this
   scenario has to cost marks for — so a flow with no `uipath.agent.autonomous`
   node, or with a PUBLISHED agent (`uipath.core.agent.<key>`) instead, is
   refused here.
2. **The agent is fed the flow's three inputs, and its prompts REFERENCE them.**
   The platform derives an inline agent's deployed input list by scanning the
   node's prompts for `$vars.*`, so an `agentInputVariables` entry no prompt
   mentions can be dropped on deploy. This is also exactly the defect card IA
   fixed one layer down (the live path sent the unevaluated expression), and it is
   why a prompt with no `$vars.` at all cannot be right for this scenario: the
   email has to cite an invoice number the flow was handed.
3. **`returns` declares both fields** the contract reads back, since only a
   declared field is a checkable read.
4. **Both outputs are read FROM the agent step** — not restated, not composed by a
   script that ignores the agent.
5. **The draft is not written in.** No literal invoice number, credit amount, or
   canned email body anywhere in the flow.

Usage: check_billing_resolution_writer.py <FlowName>.flow
"""
import json
import re
import sys

INLINE = "uipath.agent.autonomous"
IN_CONTRACT = ["customerName", "invoiceNumber", "creditAmount"]
OUT_CONTRACT = {"emailSubject": "string", "emailBody": "string"}
# The values the live rung asserts. None may be a literal in the flow.
FORBIDDEN = ["MCS-2026-04872", "Northwind Traders"]
FORBIDDEN_NUMBERS = ["1610", "1,610"]


def fail(msg):
    sys.exit(f"FAIL: {msg}")


def unwrap(v):
    if isinstance(v, dict):
        for k in ("expression", "source"):
            if k in v:
                return unwrap(v[k])
    return v


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "BillingResolutionWriter.flow"
    raw = open(path, encoding="utf-8").read()
    f = json.loads(raw)
    nodes = f["nodes"]
    types_seen = sorted({str(n.get("type")) for n in nodes})

    # ── 1. exactly one INLINE agent, and no stand-in ──────────────────────────
    agents = [n for n in nodes if n.get("type") == INLINE]
    if len(agents) != 1:
        fail(f"expected exactly ONE {INLINE} node, found {len(agents)}; node types: {types_seen}")
    published = [n for n in nodes if str(n.get("type", "")).startswith("uipath.core.agent.")]
    if published:
        fail(
            f"the flow wires a PUBLISHED agent ({[n['type'] for n in published]}); this scenario asks for "
            f"an agent EMBEDDED in the flow project (inline), which is {INLINE}"
        )
    a = agents[0]
    ins = {k: unwrap(v) for k, v in (a.get("inputs") or {}).items()}

    # ── 2. the three inputs reach it, and the prompts reference them ──────────
    declared = [str(v.get("id") or v.get("name") or "") for v in (ins.get("agentInputVariables") or [])
                if isinstance(v, dict)]
    prompts = " ".join(str(ins.get(k) or "") for k in ("systemPrompt", "userPrompt"))
    if not prompts.strip():
        fail("the agent node carries no systemPrompt/userPrompt")
    if "$vars." not in prompts:
        fail(
            f"neither prompt references a flow value ($vars.…): {prompts[:160]!r}. The platform derives an "
            f"inline agent's deployed input list by SCANNING the prompts, and the drafted email has to cite "
            f"an invoice number the flow was handed — a prompt with no reference cannot do either"
        )
    for name in IN_CONTRACT:
        # Either passed as an agent input variable, or referenced straight in a
        # prompt — both reach the model; the platform merges the two lists.
        if name not in declared and f"$vars.{name}" not in prompts and f"$vars.start.output.{name}" not in prompts:
            fail(
                f"the agent is never given {name!r}: agentInputVariables={declared or '[]'} and no prompt "
                f"references it. All three inputs are the material the email is drafted from"
            )

    # ── 3. `returns` declares both fields ─────────────────────────────────────
    out_vars = [str(v.get("id") or v.get("name") or "") for v in (ins.get("agentOutputVariables") or [])
                if isinstance(v, dict)]
    for want in ("subject", "body"):
        if not any(want in o.lower() for o in out_vars):
            fail(
                f"the agent declares outputs {out_vars or '[]'}; it has to declare the email's subject and "
                f"body — only a DECLARED field is a checkable read"
            )

    # ── 4. both flow outputs are READ FROM the agent step ─────────────────────
    globs = {g["id"]: g for g in ((f.get("variables") or {}).get("globals") or [])}
    ins_g = {k: v for k, v in globs.items() if v.get("direction") == "in"}
    outs_g = {k: v for k, v in globs.items() if v.get("direction") == "out"}
    for name in IN_CONTRACT:
        if name not in ins_g:
            fail(f"the flow declares in-globals {sorted(ins_g)}; the contract asks for {name}")
    for name, want in OUT_CONTRACT.items():
        if name not in outs_g:
            fail(f"the flow declares out-globals {sorted(outs_g)}; the contract asks for {name}")
        if outs_g[name].get("type") != want:
            fail(f"output {name} is declared {outs_g[name].get('type')!r}; the contract asks for {want}")

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
        src = bound.get(name)
        if src is None:
            fail(f"no End node binds an output named {name!r}; it binds {sorted(bound)}")
        if aref not in src and not any(f"$vars.{s}" in src for s in via):
            fail(
                f"output {name} is {src!r}, and nothing it reads references {aref} — the draft has to come "
                f"FROM the agent step. Steps that read it: {sorted(via) or 'none'}"
            )

    # ── 5. the draft is not written in ────────────────────────────────────────
    for bad in FORBIDDEN:
        if bad in raw:
            fail(
                f"the flow carries the literal {bad!r}. The live rung asserts the drafted email cites it, so "
                f"a flow that writes it in passes while the agent drafts nothing — v1's own checker scopes to "
                f"the emailBody output for exactly this reason"
            )
    for bad in FORBIDDEN_NUMBERS:
        if re.search(r"(?<![0-9])" + re.escape(bad) + r"(?![0-9])", raw):
            fail(f"the flow carries the credit amount {bad!r} as a literal; it arrives as a flow INPUT")

    print(
        f"{len(nodes)} nodes; one {INLINE} ({a['id']}) fed {declared or 'via prompt refs'}, "
        f"returns {out_vars}; outputs {sorted(OUT_CONTRACT)} read from {a['id']}; no draft literals"
    )


if __name__ == "__main__":
    main()
