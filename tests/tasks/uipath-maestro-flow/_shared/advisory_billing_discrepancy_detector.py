#!/usr/bin/env python3
"""STRUCTURAL gate for the `billing_discrepancy_detector` port.

v1 asserts two node types exist (`uipath-dataservice.query`, `core.logic.merge`)
and then drives one `flow debug`. Two node types existing is a weak reading of the
thing its own prompt demands — *"run them as parallel branches that fan out from
the trigger and rejoin at a merge — do not chain them"* — because
`start → ERP → CRM → merge` satisfies it exactly while being a chain with a merge
bolted on. So this gate asserts the SHAPE:

1. **Two Data Service query nodes**, one on `BillingDisputeERP` and one on
   `BillingDisputeCRM`, each with its entity in the PATH slot.
2. **Exactly one `core.logic.merge`**, carrying the `bpmn:ParallelGateway`
   definition that makes it a join once deployed, fed by ≥2 distinct sources, and
   continuing downstream.
3. **The two queries are MUTUALLY UNREACHABLE** — neither lies downstream of the
   other — and both are reachable from the trigger. This is the assertion v1's
   node-type read cannot make, and the authoring failure its own prompt polices.
4. **Both filters are computed**, each from the input it belongs to: the ERP
   filter from `invoiceNumber`, the CRM filter from `accountNumber`.
5. **None of the answers is written in.** `1610`, `2590`, `4200` and
   `"Enterprise"` may not appear as literals; the tenant is the only source.
6. **The outputs are declared with the contract's names and types**, and each is
   read from the side it belongs to (the tier from the CRM query, the matched
   invoice from the ERP query, the two numbers computed downstream of ERP).
7. **The connection resolves to a connection/folder PAIR of distinct uuids** on
   both query nodes.

Usage: advisory_billing_discrepancy_detector.py [<FlowName>.flow]
"""
import re
from collections import Counter, defaultdict

from advisory_flow_utils import (
    LOOP_BACK_PORTS,
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

MERGE = "core.logic.merge"
DS_PREFIX = "uipath.connector.uipath-uipath-dataservice."
ERP, CRM = "BillingDisputeERP", "BillingDisputeCRM"
# The measured answers (live 2026-07-31). A flow may not carry any of them.
FORBIDDEN_LITERALS = ["1610", "2590", "4200", "Enterprise"]
OUT_CONTRACT = {
    "totalOvercharge": "number",
    "discrepancyCount": "number",
    "matchedInvoiceNumber": "string",
    "accountTier": "string",
}
IN_CONTRACT = ["invoiceNumber", "accountNumber", "disputedLineNumber",
               "disputedUnitPrice", "disputedQuantity"]


def main():
    _, f, nodes = load_flow("BillingDiscrepancyDetector.flow")
    edges = f.get("edges") or []
    types_seen = sorted({str(n.get("type")) for n in nodes})

    # ── 1. two Data Service query nodes, one per entity ───────────────────────
    ds = [n for n in nodes if str(n.get("type", "")).startswith(DS_PREFIX)]
    if len(ds) != 2:
        fail(f"expected exactly TWO Data Service query nodes (ERP + CRM), found {len(ds)}; node types: {types_seen}")
    for n in ds:
        if not n["type"].endswith(".query-entity-records"):
            fail(f"Data Service node {n['id']!r} is {n['type']!r}; the lookup is query-entity-records")

    def detail(n):
        return (n.get("inputs") or {}).get("detail") or {}

    def entity_of(n):
        p = {k: unwrap(v) for k, v in (detail(n).get("pathParameters") or {}).items()}
        if "entityName" not in p:
            q = {k: unwrap(v) for k, v in (detail(n).get("queryParameters") or {}).items()}
            fail(
                f"query node {n['id']!r} has pathParameters {sorted(p)}; `entityName` belongs in the PATH "
                f"slot — it is the {{entityName}} of /v2/{{entityName}}/qer. queryParameters: {sorted(q)}"
            )
        return str(p["entityName"]).strip()

    by_entity = {}
    for n in ds:
        e = entity_of(n)
        if e in by_entity:
            fail(f"both query nodes address {e!r}; the scenario needs one {ERP} and one {CRM}")
        by_entity[e] = n
    missing = [e for e in (ERP, CRM) if e not in by_entity]
    if missing:
        fail(f"no query node addresses {missing}; entities queried: {sorted(by_entity)}")
    erp, crm = by_entity[ERP], by_entity[CRM]

    # ── 2. exactly one merge, a real join, continuing downstream ──────────────
    merges = [n for n in nodes if n.get("type") == MERGE]
    if len(merges) != 1:
        fail(f"expected exactly one {MERGE!r} node (the join), found {len(merges)}; node types: {types_seen}")
    mid = merges[0]["id"]
    defs = [d for d in (f.get("definitions") or []) if d.get("nodeType") == MERGE]
    if len(defs) != 1:
        fail(f"expected exactly one {MERGE!r} definitions[] entry, got {len(defs)}")
    model = defs[0].get("model") or {}
    if model.get("type") != "bpmn:ParallelGateway":
        fail(f"merge definition model.type={model.get('type')!r}; a join is a 'bpmn:ParallelGateway'")
    incoming = [e for e in edges if e.get("targetNodeId") == mid]
    sources = sorted({e.get("sourceNodeId") for e in incoming if e.get("sourceNodeId")})
    if len(sources) < 2:
        fail(f"merge {mid!r} is fed by {len(sources)} distinct source(s) ({sources}); a join needs two branches")
    if not [e for e in edges if e.get("sourceNodeId") == mid]:
        fail(f"merge {mid!r} has no outgoing edge; the joined path must continue (the computation reads both arms)")
    out_counts = Counter(e.get("sourceNodeId") for e in edges if e.get("sourceNodeId"))
    if not [n for n, c in out_counts.items() if c >= 2]:
        fail("no fork found: no node has 2+ outgoing edges, so nothing fans out before the join")

    # ── 3. the two QUERIES are on mutually unreachable branches ───────────────
    adj = defaultdict(list)
    for e in edges:
        if e.get("targetPort") not in LOOP_BACK_PORTS:
            adj[e.get("sourceNodeId")].append(e.get("targetNodeId"))

    def reaches(a, b, block):
        seen, stack = {a}, [a]
        while stack:
            cur = stack.pop()
            for nxt in adj.get(cur, ()):
                if nxt == block or nxt in seen:
                    continue
                if nxt == b:
                    return True
                seen.add(nxt)
                stack.append(nxt)
        return False

    if reaches(erp["id"], crm["id"], mid) or reaches(crm["id"], erp["id"], mid):
        first, second = (erp, crm) if reaches(erp["id"], crm["id"], mid) else (crm, erp)
        fail(
            f"the {second['id']!r} query is downstream of the {first['id']!r} query — that is the two "
            f"lookups CHAINED with a merge on the end, not a fan-out. v1's own prompt asks for parallel "
            f"branches from the trigger ('do not chain them'), and its node-type check cannot see this"
        )
    triggers = [n for n in nodes if str(n.get("type")).startswith("core.trigger.")]
    if len(triggers) != 1:
        fail(f"a flow has exactly one trigger, found {len(triggers)}")
    start = triggers[0]["id"]
    for n in (erp, crm):
        if n["id"] != start and not reaches(start, n["id"], None):
            fail(f"query {n['id']!r} is not reachable from the trigger {start!r}")

    # ── 4. both filters computed, each from its own input ─────────────────────
    for label, node, wanted_input in ((ERP, erp, "invoiceNumber"), (CRM, crm, "accountNumber")):
        q = {k: unwrap(v) for k, v in (detail(node).get("queryParameters") or {}).items()}
        if "queryExpression" not in q:
            fail(f"the {label} query sets no queryExpression; queryParameters: {sorted(q)}")
        expr = str(q["queryExpression"])
        if not query_references_input(detail(node), wanted_input):
            fail(
                f"the {label} queryExpression is {expr!r} and its filterVariables do not reference "
                f"{wanted_input!r} — each lookup must filter on its own flow input"
            )
        if "'" not in expr:
            fail(f"the {label} queryExpression is {expr!r} — a CEQL string literal has to be single-quoted")

    # ── 5. no answer is written in ─────────────────────────────────────────────
    for bad in FORBIDDEN_LITERALS:
        if carries_literal(f, bad):
            fail(
                f"the flow carries the literal {bad!r}. Every one of the answers "
                f"({', '.join(FORBIDDEN_LITERALS)}) has to come from the tenant — a flow that writes one in "
                f"passes the live rung while querying nothing"
            )

    # ── 6. the declared contract, and where each output comes from ────────────
    globs = {g["id"]: g for g in ((f.get("variables") or {}).get("globals") or [])}
    ins = {k: v for k, v in globs.items() if v.get("direction") == "in"}
    outs = {k: v for k, v in globs.items() if v.get("direction") == "out"}
    for name in IN_CONTRACT:
        if name not in ins:
            fail(f"the flow declares in-globals {sorted(ins)}; the contract asks for {name}")
    for name, want in OUT_CONTRACT.items():
        if name not in outs:
            fail(f"the flow declares out-globals {sorted(outs)}; the contract asks for {name}")
        if outs[name].get("type") != want:
            fail(f"output {name} is declared {outs[name].get('type')!r}; the contract asks for {want}")

    ends = [n for n in nodes if n.get("type") == "core.control.end"]
    if not ends:
        fail("the flow has no End node, so it declares no outputs")
    dependencies = node_dependencies(nodes)

    def sourced_from(out_name, node_id, what):
        success_ends = successful_end_ids(nodes, edges, node_id)
        bindings = end_bindings(nodes, success_ends, out_name)
        if not bindings:
            fail(f"no successful End node binds an output named {out_name!r}")
        if any(source_depends_on(value, node_id, dependencies) for value in bindings):
            return
        fail(
            f"successful output {out_name} has bindings {[str(unwrap(v)) for v in bindings]!r}, and none "
            f"depends on $vars.{node_id}.output — {what}"
        )

    sourced_from("accountTier", crm["id"], f"the tier comes from the {CRM} query")
    sourced_from("matchedInvoiceNumber", erp["id"], f"the matched invoice comes from the {ERP} query")
    for name in ("totalOvercharge", "discrepancyCount"):
        sourced_from(name, erp["id"], f"the contracted amount it is computed from lives in the {ERP} rows")

    # ── 7. the resolved connection: two DISTINCT uuids, on BOTH query nodes ───
    UUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-", re.ASCII)
    for label, node in ((ERP, erp), (CRM, crm)):
        conn = str(unwrap(detail(node).get("connectionId")) or "")
        folder = str(unwrap(detail(node).get("connectionFolderKey")) or "")
        for attr, v in (("connectionId", conn), ("connectionFolderKey", folder)):
            if not UUID.match(v) or re.match(r"^0{8}-0{4}-", v):
                fail(f"the {label} query's detail.{attr} is {v!r}, not a real uuid")
        if conn == folder:
            fail(
                f"the {label} query's detail.connectionId and detail.connectionFolderKey are the SAME uuid "
                f"({conn}) — the folder binding needs the connection's FOLDER key, not its id (measured: the "
                f"live dispatch then sends the folder key as --connection-id and answers 401)"
            )

    print(
        f"{len(nodes)} nodes; {ERP}={erp['id']!r} and {CRM}={crm['id']!r} on mutually unreachable branches "
        f"from {start!r}, converging on {MERGE} {mid!r} (bpmn:ParallelGateway, {len(sources)} sources, "
        f"continues downstream); both filters computed from their own inputs; no answer literals; "
        f"outputs {sorted(OUT_CONTRACT)} each read from its own side"
    )


if __name__ == "__main__":
    main()
