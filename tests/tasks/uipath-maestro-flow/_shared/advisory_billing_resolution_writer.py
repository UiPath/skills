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
2. **The agent is fed the flow's three inputs.** The supported representations
   are explicit `agentInputVariables[].binding` values or variable references in
   the Flow/sidecar prompts. The email has to cite the invoice data the flow was
   handed; generic prompt text alone is insufficient.
3. **`returns` declares both fields** the contract reads back, since only a
   declared field is a checkable read.
4. **Both outputs are read FROM the agent step** — not restated, not composed by a
   script that ignores the agent.
5. **The draft is not written in.** No literal invoice number, credit amount, or
   canned email body anywhere in the flow.
6. **The drafted resolution is POSTED to Slack.** `correlationId` is a declared
   input; `caseKey`/`slackMessageId` are declared routed outputs; exactly one Slack
   `send-message-to-channel` node sends as `user`; the message depends on the agent
   step (so a canned template over the trigger inputs is refused offline); `caseKey`
   routes the correlationId and `slackMessageId` comes from the executed send.

Usage: advisory_billing_resolution_writer.py [<FlowName>.flow]
"""

from advisory_flow_utils import (
    agent_prompt_text,
    carries_literal,
    end_bindings,
    fail,
    load_flow,
    node_dependencies,
    references_field,
    source_depends_on,
    successful_end_ids,
    unwrap,
)

INLINE = "uipath.agent.autonomous"
IN_CONTRACT = ["customerName", "invoiceNumber", "creditAmount"]
OUT_CONTRACT = {"emailSubject": "string", "emailBody": "string"}
# correlationId is a flow INPUT but not drafting material, so it is not in
# IN_CONTRACT (which gates what the agent must be fed); it is required as a
# declared in-global only. caseKey/slackMessageId are routed outputs, not
# agent-drafted, so they are not in OUT_CONTRACT (which gates agent-dependency).
ROUTED_IN = "correlationId"
ROUTED_OUT = {"caseKey": "string", "slackMessageId": "string"}
SLACK_KEY = "uipath-salesforce-slack"
SLACK_OP = "send-message-to-channel"
# The values the live rung asserts. None may be a literal in the flow.
FORBIDDEN = ["MCS-2026-04872", "Northwind Traders"]
FORBIDDEN_NUMBERS = ["1610", "1,610"]


def main():
    path, f, nodes = load_flow("BillingResolutionWriter.flow")
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
    input_variables = [v for v in (ins.get("agentInputVariables") or []) if isinstance(v, dict)]
    declared = [str(v.get("id") or v.get("name") or "") for v in input_variables]
    bindings = {
        str(v.get("id") or v.get("name") or ""): str(unwrap(v.get("binding")) or "")
        for v in input_variables
    }
    prompts = agent_prompt_text(path, a)
    if not prompts.strip():
        fail("the agent node carries no systemPrompt/userPrompt")
    for name in IN_CONTRACT:
        prompt_ref = any(token in prompts for token in (f"$vars.{name}", f"$vars.start.output.{name}", f"input.{name}"))
        binding_ref = any(references_field(binding, name) for binding in bindings.values())
        if not prompt_ref and not binding_ref:
            fail(
                f"the agent is never given {name!r}: agentInputVariables={bindings or '{}'} and neither "
                f"the Flow nor sidecar prompts reference it. All three inputs are drafting material"
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
    dependencies = node_dependencies(nodes)
    success_ends = successful_end_ids(nodes, f.get("edges") or [], a["id"])
    if not success_ends:
        fail(f"no End node is reachable from agent {a['id']!r} without taking its error port")
    for name in OUT_CONTRACT:
        output_bindings = end_bindings(nodes, success_ends, name)
        if not output_bindings:
            fail(f"no successful End node binds an output named {name!r}")
        if not any(source_depends_on(value, a["id"], dependencies) for value in output_bindings):
            fail(
                f"successful output {name} has bindings {[str(unwrap(v)) for v in output_bindings]!r}, and "
                f"none depends on $vars.{a['id']}.output — the draft has to come FROM the agent step"
            )

    # ── 5. the draft is not written in ────────────────────────────────────────
    for bad in FORBIDDEN:
        if carries_literal(f, bad):
            fail(
                f"the flow carries the literal {bad!r}. The live rung asserts the drafted email cites it, so "
                f"a flow that writes it in passes while the agent drafts nothing — v1's own checker scopes to "
                f"the emailBody output for exactly this reason"
            )
    for bad in FORBIDDEN_NUMBERS:
        if carries_literal(f, bad):
            fail(f"the flow carries the credit amount {bad!r} as a literal; it arrives as a flow INPUT")

    # ── 6. the drafted resolution is POSTED to Slack ──────────────────────────
    # correlationId is a declared flow input; caseKey + slackMessageId are declared
    # routed outputs.
    if ROUTED_IN not in ins_g:
        fail(f"the flow declares in-globals {sorted(ins_g)}; the contract asks for {ROUTED_IN}")
    for name, want in ROUTED_OUT.items():
        if name not in outs_g:
            fail(f"the flow declares out-globals {sorted(outs_g)}; the contract asks for {name}")
        if outs_g[name].get("type") != want:
            fail(f"output {name} is declared {outs_g[name].get('type')!r}; the contract asks for {want}")

    # Exactly one Slack SEND node (native connector node or connector-mode HTTP
    # proxy to the send op) — a read/search activity is not a delivery.
    def is_slack_send(n: dict) -> bool:
        t = str(n.get("type", ""))
        if SLACK_KEY in t and SLACK_OP in t:
            return True
        detail = (n.get("inputs") or {}).get("detail") or {}
        body = detail.get("bodyParameters") or {} if isinstance(detail, dict) else {}
        target = str((body.get("targetConnector") or body.get("connectorKey") or "")).lower()
        auth = str(body.get("authentication") or "").lower()
        return (
            t.lower().startswith("core.action.http")
            and target == SLACK_KEY
            and auth == "connector"
            and SLACK_OP.replace("-", "") in json.dumps(detail).lower().replace("-", "").replace("_", "")
        )

    slack_nodes = [n for n in nodes if is_slack_send(n)]
    if len(slack_nodes) != 1:
        fail(f"expected exactly ONE Slack {SLACK_OP} node, found {len(slack_nodes)}; node types: {types_seen}")
    slack = slack_nodes[0]

    # Send as `user`, not the default bot.
    send_as = str(((slack.get("inputs") or {}).get("detail") or {}).get("queryParameters", {}).get("send_as", "")).strip().lower()
    if send_as != "user":
        fail(f"the Slack send node sets send_as={send_as!r}; the prompt requires sending as 'user'")

    # The posted message must depend on the agent's draft — a canned template over
    # trigger inputs (correlationId, invoice, credit) would satisfy an ids-only gate
    # without ever posting the resolution. This is the structural, offline-catchable
    # form of the live checker's body[:80] assertion.
    if not source_depends_on(slack.get("inputs") or {}, a["id"], dependencies):
        fail(
            f"the Slack node's inputs do not depend on $vars.{a['id']}.output — the message "
            "must carry the agent's drafted resolution, not only the trigger inputs"
        )

    # caseKey routes the correlationId; slackMessageId comes from the Slack send.
    case_bindings = end_bindings(nodes, success_ends, "caseKey")
    if not case_bindings:
        fail("no successful End node binds an output named 'caseKey'")
    if not any(references_field(v, ROUTED_IN) for v in case_bindings):
        fail(f"caseKey has bindings {[str(unwrap(v)) for v in case_bindings]!r}; it must route the {ROUTED_IN}")
    ts_bindings = end_bindings(nodes, success_ends, "slackMessageId")
    if not ts_bindings:
        fail("no successful End node binds an output named 'slackMessageId'")
    if not any(source_depends_on(v, slack["id"], dependencies) for v in ts_bindings):
        fail(
            f"slackMessageId has bindings {[str(unwrap(v)) for v in ts_bindings]!r}, none depending on "
            f"$vars.{slack['id']}.output — the posted message's ts must come FROM the executed send"
        )

    print(
        f"{len(nodes)} nodes; one {INLINE} ({a['id']}) fed {declared or 'via prompt refs'}, "
        f"returns {out_vars}; outputs {sorted(OUT_CONTRACT)} read from {a['id']}; no draft literals"
    )


if __name__ == "__main__":
    main()
