#!/usr/bin/env python3
"""STRUCTURAL gate for the `billing_invoice_lookup` port — the facts no behaviour
rung can see.

v1's own checker asserts one structural thing (`assert_flow_has_node_type
(["uipath-dataservice.query"])`) and then drives three `flow debug` runs. Our
ladder covers the behaviour half in its own rungs (`expect` ×3 offline, `live`
×1); this file asserts what neither can:

1. **The query is a Data Service connector node**, exactly one of them, and its
   `entityName` really went to the PATH slot (the `{entityName}` of
   `/v2/{entityName}/qer`). A `body` placement compiles and 404s live on an
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
5. **The connection bindings are a pair** (ConnectionId + FolderKey) and the
   folder binding does not carry the CONNECTION id — measured while writing this
   card: a bindings.json whose FolderKey entry pointed at the connection id
   collapsed both entries into one at FIL emission and the live dispatch sent the
   FOLDER key as `--connection-id`, answering 401.

Usage: advisory_billing_invoice_lookup.py [<FlowName>.flow]
"""
import re

from advisory_flow_utils import (
    carries_literal,
    end_bindings,
    fail,
    load_flow,
    node_dependencies,
    query_references_input,
    source_depends_on,
    successful_end_ids,
    unwrap,
)

CANONICAL = "MCS-2026-04872"
# The three malformed forms the offline rungs drive. A flow may not carry any of
# them as a literal.
RAW_INPUTS = ["2026-04872", "mcs-2026-04872"]
DS_TYPE_PREFIX = "uipath.connector.uipath-uipath-dataservice."
ENTITY = "BillingDisputeERP"


def main():
    _, f, nodes = load_flow("BillingInvoiceLookup.flow")
    types_seen = sorted({str(n.get("type")) for n in nodes})

    # ── 1. exactly one Data Service query node ────────────────────────────────
    ds = [n for n in nodes if str(n.get("type", "")).startswith(DS_TYPE_PREFIX)]
    if len(ds) != 1:
        fail(f"expected exactly ONE Data Service connector node, found {len(ds)}; node types: {types_seen}")
    q = ds[0]
    if not q["type"].endswith(".query-entity-records"):
        fail(f"the Data Service node is {q['type']!r}; the lookup is the query-entity-records operation")
    # A raw HTTP call would satisfy every behaviour rung, so name it out.
    http = [n for n in nodes if str(n.get("type", "")) in ("core.action.http", "uipath.connector.uipath-uipath-http.http-request")]
    if http:
        fail(f"the flow calls Data Service over raw HTTP ({[n['id'] for n in http]}); use the connector action")

    detail = (q.get("inputs") or {}).get("detail") or {}
    pathp = {k: unwrap(v) for k, v in (detail.get("pathParameters") or {}).items()}
    queryp = {k: unwrap(v) for k, v in (detail.get("queryParameters") or {}).items()}

    # ── 2. the entity is a PATH parameter, and it is the seeded entity ────────
    if "entityName" not in pathp:
        fail(
            f"the query node's pathParameters are {sorted(pathp)}; `entityName` belongs there — "
            f"it is the {{entityName}} of /v2/{{entityName}}/qer. queryParameters: {sorted(queryp)}"
        )
    if str(pathp["entityName"]).strip() != ENTITY:
        fail(f"entityName is {pathp['entityName']!r}, not {ENTITY!r} — the entity the task names")

    # ── 3. the FILTER is computed from the flow's input, not a constant ───────
    if "queryExpression" not in queryp:
        fail(f"the query node sets no queryExpression; queryParameters: {sorted(queryp)}")
    expr = str(queryp["queryExpression"])
    if not query_references_input(detail, "invoiceNumber"):
        fail(
            f"queryExpression is {expr!r}, likely a hand-authored =js: concat. filterVariables "
            f"has no placeholder for invoiceNumber. Author the filter via --detail.filter so "
            f"the CLI compiles it: dynamic operands become {{var_...}} placeholders in "
            f"filterVariables"
        )
    # A CEQL string literal must be single-quoted; an unquoted RHS parses as
    # subtraction server-side and 400s (the `sql-where` grammar fil-run enforces).
    if "'" not in expr:
        fail(f"queryExpression is {expr!r} — a CEQL string literal has to be single-quoted")

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

    # ── 7. the RESOLVED connection: two DISTINCT uuids on the node ────────────
    # The compiler resolves `bindings.json`'s symbolic `connection`/`folder` into
    # the node's own `detail`, so that is where the outcome is checkable (the
    # emitted `.flow` carries no `bindings[]` of its own for a connector — the
    # separate bindings-hygiene criterion covers the file the author wrote).
    #
    # The failure this catches is not hypothetical: measured while writing this
    # card, a `bindings.json` whose FolderKey entry carried the CONNECTION id
    # collapsed both entries into one at FIL emission, and the live dispatch sent
    # the folder key as `--connection-id` → `401 Unauthorized … invalid Element
    # token`. Two distinct uuids is the checkable form of "the pair is right".
    conn_id = str(unwrap(detail.get("connectionId")) or "")
    folder = str(unwrap(detail.get("connectionFolderKey")) or "")
    UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", re.ASCII)
    for label, v in (("connectionId", conn_id), ("connectionFolderKey", folder)):
        if not UUID.match(v):
            fail(
                f"the query node's detail.{label} is {v!r}, not a uuid — `bindings.json` has to name "
                f"the real Data Fabric connection and its folder (uip is connections list --all-folders)"
            )
        if re.match(r"^0{8}-0{4}-", v):
            fail(f"the query node's detail.{label} is the stub uuid {v!r}")
    if conn_id == folder:
        fail(
            f"detail.connectionId and detail.connectionFolderKey are the SAME uuid ({conn_id}) — the "
            f"folder binding needs the connection's FOLDER key, not its id. Measured: the two collapse "
            f"into one binding at FIL emission and the live dispatch sends the folder key as "
            f"--connection-id (401 Unauthorized)"
        )

    print(
        f"{len(nodes)} nodes; DS query {q['id']} entityName={pathp['entityName']!r} (path) "
        f"queryExpression computed from $vars; outputs read from {q['id']}; "
        f"connection={conn_id[:8]}… folder={folder[:8]}…"
    )


if __name__ == "__main__":
    main()
