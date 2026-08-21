#!/usr/bin/env python3
"""Covering structural check for the GA row-7 port (BillingDisputeResolution).

v1's own structural checker runs beside this one, VERBATIM, and it reads the
orchestration: the node types, the directed topology, no HITL, no send-email, and
that the flow declares at least two `out` variables. This file asserts only the
three things v1 CANNOT see — each one a contract measured on the product runtime,
each one a defect this campaign already paid for once.

1. **The connector's CONNECTION bindings carry a real key.** The platform resolves
   an Integration Service connection through the flow's native `bindings[]` or
   `resources[]` declarations, by the names the definition declares. A pair
   that is missing, or that carries a symbolic name instead of the tenant's key,
   deploys and then faults with `[102010] Integration Services invalid value in
   input`. That is board row G-19, and it is invisible to every offline rung
   except this one: no local executor reads `bindings[]`.

2. **The IxP node's `fileRef` is a plain `=js:$vars.…` string.** The expression
   ENVELOPE (`{type:'jsExpression', …}`) is the file format's general spelling and
   this SDK emits it everywhere else, but the product's own `ixp-node` validator
   tests `typeof fileRef !== 'string'` and refuses the object form — which fails
   `uip maestro flow validate`, criterion 1, weight 3.0. Card ga7 found it, and
   the reason it survived a green platform run is that the RUNTIME accepts both.
   Asserted here as well as in flow-check (FC419) because a graded criterion
   should not depend on a rule in a vendored package staying enabled.

3. **The five declared outputs, and the two REJECTION paths not carrying a
   drafted email.** v1 asks for "≥2 out variables", which a flow returning
   `determination` and `rationale` satisfies while quietly dropping the credit and
   the resolution body. The prompt's contract is five named outputs, and that
   `resolutionEmailBody` comes from the writer agent on the resolution path and
   from something else on a rejection path — a writer that never ran cannot have
   drafted anything.

Usage: advisory_billing_dispute_resolution.py [<FlowName>.flow]
"""
import json
import re

from advisory_flow_utils import (
    connection_binding_values,
    fail,
    is_real_uuid,
    load_flow,
    node_dependencies,
    source_depends_on,
)

REQUIRED_OUTPUTS = {
    "determination": "string",
    "recommendedAction": "string",
    "creditAmount": "number",
    "rationale": "string",
    "resolutionEmailBody": "string",
}

AGENT_TYPE = "uipath.agent.autonomous"


def expr_of(value):
    """The expression text behind an input/source value, whichever spelling it is.

    A value is either a plain string (`"=js:…"` / a literal) or the current
    format's envelope `{type, expression, fieldType}`. Returns
    ``(kind, text)`` where kind is 'jsExpression', 'literal', or 'other'.
    """
    if isinstance(value, dict):
        return str(value.get("type") or ""), str(value.get("expression") or "")
    if isinstance(value, str):
        return ("jsExpression", value[len("=js:"):]) if value.startswith("=js:") else ("literal", value)
    return "other", ""


def main():
    _, flow, nodes = load_flow("BillingDisputeResolution.flow")
    agents = {n["id"] for n in nodes if str(n.get("type") or "") == AGENT_TYPE}

    # ── 1. the connection bindings the platform resolves the connector through ──
    conn = connection_binding_values(flow)
    if not conn:
        fail(
            "the flow declares NO `connection` binding. The two Data Service lookups are Integration "
            "Service calls, and the platform resolves their connection through the flow's native "
            "bindings declaration — without the pair it deploys and faults with [102010] Integration Services "
            "invalid value in input. (Give the connector its connection + folder: either a `bindings.json` "
            "mapping your symbolic names to the tenant's keys, or the keys inline.)"
        )
    bad = [(identifier, values) for identifier, values in conn if not values or any(not is_real_uuid(v) for v in values)]
    if bad:
        fail(
            "connection binding(s) "
            + ", ".join(f"{identifier!r}={json.dumps(values)}" for identifier, values in bad)
            + " do not carry a real tenant key (a uuid, and not a zero-prefixed stub). The platform "
            "substitutes these by name into the connector node, so a symbolic name or a placeholder "
            "reaches Integration Services verbatim -> [102010]. Look the connection up with "
            "`uip is connections list --all-folders` and use its `Id` / `FolderKey`."
        )
    print(f"OK: {len(conn)} connection binding(s), each carrying a real tenant key")

    # ── 2. the IxP fileRef spelling `uip maestro flow validate` requires ───────
    ixp = [n for n in nodes if str(n.get("type") or "").startswith("uipath.ixp.")]
    if not ixp:
        fail("no IxP extraction node (`uipath.ixp.*`) — the invoice must be read by the trained model")
    for n in ixp:
        ref = (n.get("inputs") or {}).get("fileRef")
        if not isinstance(ref, str) or not re.match(r"^=js:\$vars\.[A-Za-z_$]", ref):
            fail(
                f"IxP node {n.get('id')!r} has `fileRef` = {json.dumps(ref)[:160]}, which the platform "
                "refuses: its `ixp-node` validator tests `typeof fileRef !== \"string\"` and wants a plain "
                "`=js:$vars.<upstream>.output.<field>` expression. The envelope form the rest of the file "
                "uses fails `uip maestro flow validate` here — and a `flow debug` run will NOT tell you, "
                "because the runtime accepts both."
            )
    print(f"OK: {len(ixp)} IxP node(s), each with `fileRef` in the plain `=js:` spelling the validator requires")

    # ── 3. the five declared outputs, and the rejection paths' own body ────────
    globals_ = ((flow.get("variables") or {}).get("globals")) or []
    outs = {v.get("id"): v for v in globals_ if v.get("direction") == "out"}
    missing = [k for k in REQUIRED_OUTPUTS if k not in outs]
    if missing:
        fail(
            f"the flow does not declare `out` variable(s) {missing}. It declares {sorted(outs)}. "
            "All five are part of the contract — the caller gets the resolution back instead of an email, "
            "so dropping one drops the answer."
        )
    mistyped = [
        f"{k} is {outs[k].get('type')!r}, expected {t!r}"
        for k, t in REQUIRED_OUTPUTS.items()
        if str(outs[k].get("type")) != t
    ]
    if mistyped:
        fail("declared output type(s) do not match the contract: " + "; ".join(mistyped))
    print(f"OK: all five outputs declared with the contract's types: {sorted(REQUIRED_OUTPUTS)}")

    # Which end nodes map `resolutionEmailBody`, and from what.
    dependencies = node_dependencies(nodes)
    writers = {agent for agent in agents if "writer" in agent.lower()} or agents
    from_agent, not_from_agent = [], []
    for n in nodes:
        if str(n.get("type") or "") != "core.control.end":
            continue
        mapped = (n.get("outputs") or {}).get("resolutionEmailBody")
        if not isinstance(mapped, dict) and not isinstance(mapped, str):
            continue
        source = mapped.get("source") if isinstance(mapped, dict) and "source" in mapped else mapped
        kind, text = expr_of(source)
        drafted = any(source_depends_on(source, writer, dependencies) for writer in writers)
        (from_agent if drafted else not_from_agent).append((n.get("id"), kind, text[:80]))

    if not from_agent:
        fail(
            "no end node maps `resolutionEmailBody` from an inline agent's output. The resolution path has "
            "to return the WRITER AGENT's drafted body — a hand-written string there is the flow answering "
            f"for the agent. End nodes mapping it: {not_from_agent or 'none'}"
        )
    if not not_from_agent:
        fail(
            "EVERY end node maps `resolutionEmailBody` from an agent's output, including the rejection "
            "path(s). A rejected dispute drafts no resolution email — the writer agent never runs on that "
            "path, so reading its output there resolves to nothing. Map a short literal instead. "
            f"End nodes mapping it: {from_agent}"
        )
    print(
        f"OK: `resolutionEmailBody` comes from the writer agent on {len(from_agent)} end node(s) "
        f"({', '.join(e[0] for e in from_agent)}) and from a non-agent value on {len(not_from_agent)} "
        f"({', '.join(e[0] for e in not_from_agent)}) — no writer is read on a path it does not run on"
    )

    # A sanity read the message above depends on: the two agents are distinct
    # instances, not one node read twice. v1 asserts this via topology; here it is
    # the reason "the writer agent" is a meaningful phrase at all.
    if len(agents) < 2:
        fail(f"expected 2 inline agents (analyst + writer), found {len(agents)}: {sorted(agents)}")
    print(f"OK: {len(agents)} distinct inline agents ({', '.join(sorted(agents))})")


if __name__ == "__main__":
    main()
