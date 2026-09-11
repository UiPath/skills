#!/usr/bin/env python3
"""STRUCTURAL gate for the `billing_invoice_lookup` port — the facts no behaviour
rung can see.

v1's own checker asserts one structural thing (`assert_flow_has_node_type
(["uipath-dataservice.query"])`) and then drives three `flow debug` runs. Our
ladder covers the behaviour half in its own rungs (`expect` ×3 offline, `live`
×1); this file asserts what neither can:

1. **The read is one entity-read node**, in whichever of the two shapes the
   tenant's flags left available, and its entity really went to the slot that
   shape reads. On the connector that is the PATH slot (the `{entityName}` of
   `/v2/{entityName}/qer`) — a `body` placement compiles and 404s live on an
   unsubstituted template.
2. **The filter is COMPUTED, not constant.** This is the anti-hardcode gate, and
   it is the whole reason the three offline `expect` rungs mean anything: a flow
   whose `queryExpression` is the literal
   `invoiceNumber = 'MCS-2026-04872'` satisfies all three of them (each input
   "normalizes" to the answer because the answer was written in). So the
   expression must reference the flow's own input, and the canonical string must
   not appear anywhere in the flow.
3. **Neither is the normalisation a lookup table.** None of the three raw test
   inputs may appear as a literal — an `if raw == '2026-04872' → …` chain passes
   every behaviour rung and generalises to nothing.
4. **The outputs are READ FROM the query step**, and declared with the contract's
   names and types (`matchedInvoiceNumber` string, `lineItemCount` number).
5. **The read resolves to the tenant it is pointed at.** On the connector that
   is a ConnectionId + FolderKey pair where the folder binding does not carry the
   CONNECTION id — measured while writing this card: a bindings.json whose
   FolderKey entry pointed at the connection id collapsed both entries into one
   at FIL emission and the live dispatch sent the FOLDER key as
   `--connection-id`, answering 401. The native node has no connection to
   resolve, so what is checkable there is its entity scope.

Usage: advisory_billing_invoice_lookup.py [<FlowName>.flow]
"""
from advisory_flow_utils import (
    CONNECTOR_READ,
    assert_read_filters_input,
    assert_read_resolves,
    carries_literal,
    end_bindings,
    entity_name,
    entity_reads,
    fail,
    load_flow,
    node_dependencies,
    source_depends_on,
    successful_end_ids,
    unwrap,
)

CANONICAL = "MCS-2026-04872"
# The three malformed forms the offline rungs drive. A flow may not carry any of
# them as a literal.
RAW_INPUTS = ["2026-04872", "mcs-2026-04872"]
ENTITY = "BillingDisputeERP"


def main():
    _, f, nodes = load_flow("BillingInvoiceLookup.flow")
    types_seen = sorted({str(n.get("type")) for n in nodes})

    # ── 1. exactly one entity-read node, in whichever shape the tenant left ───
    shape, reads = entity_reads(nodes)
    if len(reads) != 1:
        fail(f"expected exactly ONE entity-read node, found {len(reads)}; node types: {types_seen}")
    q = reads[0]
    if shape == CONNECTOR_READ and not q["type"].endswith(".query-entity-records"):
        fail(f"the Data Service node is {q['type']!r}; the lookup is the query-entity-records operation")
    # A raw HTTP call would satisfy every behaviour rung, so name it out.
    http = [n for n in nodes if str(n.get("type", "")) in ("core.action.http", "uipath.connector.uipath-uipath-http.http-request")]
    if http:
        fail(f"the flow calls Data Service over raw HTTP ({[n['id'] for n in http]}); use the connector action")

    # ── 2. the entity slot carries the seeded entity ──────────────────────────
    entity = entity_name(q, shape)
    if entity != ENTITY:
        fail(f"the read addresses {entity!r}, not {ENTITY!r} — the entity the task names")

    # ── 3. the FILTER is computed from the flow's input, not a constant ───────
    assert_read_filters_input(q, shape, "invoiceNumber", "invoice", nodes)

    # ── 4. the ANSWER is nowhere in the flow, and neither is a lookup table ───
    if carries_literal(f, CANONICAL):
        fail(
            f"the flow carries the literal {CANONICAL!r}. Offline, every rung is satisfied by a flow "
            f"that hardcodes the answer — so the canonical invoice number must be COMPUTED from the "
            f"input, never written in"
        )
    for bad in RAW_INPUTS:
        if carries_literal(f, bad):
            fail(
                f"the flow carries the test input {bad!r} as a literal — normalising by matching the "
                f"known inputs passes every rung and generalises to nothing"
            )

    # ── 5. the outputs are declared with the contract's names AND types ───────
    globs = {g["id"]: g for g in ((f.get("variables") or {}).get("globals") or [])}
    ins = {k: v for k, v in globs.items() if v.get("direction") == "in"}
    outs = {k: v for k, v in globs.items() if v.get("direction") == "out"}
    if "invoiceNumber" not in ins:
        fail(f"the flow declares in-globals {sorted(ins)}; the trigger input is `invoiceNumber`")
    for name, want in (("matchedInvoiceNumber", "string"), ("lineItemCount", "number")):
        if name not in outs:
            fail(f"the flow declares out-globals {sorted(outs)}; the contract asks for {name}")
        if outs[name].get("type") != want:
            fail(f"output {name} is declared {outs[name].get('type')!r}; the contract asks for {want}")

    # ── 6. both outputs are READ FROM the query step ──────────────────────────
    # Either the End node reads `$vars.<query>.output…` directly, or it reads a
    # step that does (a script hop is a legitimate authoring choice).
    ends = [n for n in nodes if n.get("type") == "core.control.end"]
    if not ends:
        fail("the flow has no End node, so it declares no outputs")
    dependencies = node_dependencies(nodes)
    success_ends = successful_end_ids(nodes, f.get("edges") or [], q["id"])
    if not success_ends:
        fail(f"no End node is reachable from query {q['id']!r} without taking its error port")
    for name in ("matchedInvoiceNumber", "lineItemCount"):
        bindings = end_bindings(nodes, success_ends, name)
        if not bindings:
            fail(f"no successful End node binds an output named {name!r}")
        if not any(source_depends_on(value, q["id"], dependencies) for value in bindings):
            fail(
                f"successful output {name} has bindings {[str(unwrap(v)) for v in bindings]!r}, and none "
                f"depends on $vars.{q['id']}.output — the value has to come FROM the query step"
            )

    # ── 7. the read resolves to the tenant it is pointed at ───────────────────
    # For the connector, the compiler resolves `bindings.json`'s symbolic
    # `connection`/`folder` into the node's own `detail`, so that is where the
    # outcome is checkable (the emitted `.flow` carries no `bindings[]` of its own
    # for a connector — the separate bindings-hygiene criterion covers the file the
    # author wrote). The native node resolves no connection at all.
    resolution = assert_read_resolves(q, shape, "invoice", f)

    print(
        f"{len(nodes)} nodes; {shape} read {q['id']} on {entity!r}; filter computed from $vars; "
        f"outputs read from {q['id']}; {resolution}"
    )


if __name__ == "__main__":
    main()
