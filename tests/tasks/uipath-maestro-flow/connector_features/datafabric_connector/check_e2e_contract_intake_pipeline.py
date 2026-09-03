#!/usr/bin/env python3
"""Verify the shrunk ContractRegistry bulk lifecycle:

- >=1 ForEach loop node in the flow
- >=1 create-entity-record on ContractRegistry (typically single, inside a loop)
- >=1 query-entity-records on ContractRegistry, sorted by priority DESC
- >=1 update-entity-record on ContractRegistry touching `status`, with a
  recordId expression bound to the query's output (not a hard-coded literal)
- >=1 delete-entity-record on ContractRegistry (typically single, inside a loop)

Only what's UNIQUE to this e2e: the loop-driven bulk pattern + the query→update
wiring. Single-node CRUD assertions live in smoke_update; multi-condition
FilterBuilder in integration_query.
"""
import glob
import json
import re
import sys

ENTITY = "ContractRegistry"


def detail(node):
    return node.get("inputs", {}).get("detail", {}) or {}


def targets_entity(node):
    pp = (detail(node).get("pathParameters") or {})
    return pp.get("entityName") == ENTITY


def qparams(node):
    return detail(node).get("queryParameters") or {}


def body(node):
    return detail(node).get("bodyParameters") or {}


def has_priority_desc_sort(node):
    q = qparams(node)
    b = body(node)
    sort_field = str(
        b.get("_sortFieldName") or b.get("sortFieldName")
        or q.get("_sortFieldName") or q.get("sortFieldName")
        or ""
    )
    if sort_field.startswith("=js:"):
        if "priority" not in sort_field.lower():
            return False
    elif sort_field.lower() != "priority":
        return False
    asc = q.get("isAscending", b.get("isAscending"))
    if isinstance(asc, str):
        if asc.startswith("=js:"):
            return True
        return asc.lower() == "false"
    return asc is False


def update_wired_to_query(update_node, query_node_ids):
    """The update's recordId must reference an upstream query output (not a
    hard-coded literal). We accept any =js:$vars.<id>. expression whose <id>
    matches a query node's id — that's the CLI-emitted binding form."""
    pp = detail(update_node).get("pathParameters") or {}
    rec = str(pp.get("recordId", ""))
    if not rec.startswith("=js:"):
        return False
    for qid in query_node_ids:
        if qid and qid in rec:
            return True
    return False


def main() -> int:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        print("FAIL: no .flow file", file=sys.stderr)
        return 1

    for path in flows:
        with open(path) as f:
            doc = json.load(f)
        loops, creates, queries, updates, deletes = [], [], [], [], []
        for n in doc.get("nodes", []):
            t = n.get("type", "")
            if t.startswith("core.logic.loop"):
                loops.append(n)
            if not targets_entity(n):
                continue
            if t.endswith(".create-entity-record"):
                creates.append(n)
            elif t.endswith(".query-entity-records"):
                queries.append(n)
            elif t.endswith(".update-entity-record"):
                updates.append(n)
            elif t.endswith(".delete-entity-record"):
                deletes.append(n)

        if not loops:
            print(f"FAIL: {path} — no ForEach loop; the bulk pattern requires >=1 loop", file=sys.stderr)
            continue
        if not creates:
            print(f"FAIL: {path} — no create-entity-record on {ENTITY}", file=sys.stderr)
            continue
        if not queries:
            print(f"FAIL: {path} — no query-entity-records on {ENTITY}", file=sys.stderr)
            continue
        if not any(has_priority_desc_sort(q) for q in queries):
            print(f"FAIL: {path} — no query with priority DESC sort", file=sys.stderr)
            continue
        if not updates:
            print(f"FAIL: {path} — no update-entity-record on {ENTITY}", file=sys.stderr)
            continue
        if not any("status" in body(u) for u in updates):
            print(f"FAIL: {path} — no update touching status", file=sys.stderr)
            continue
        q_ids = [q.get("id") for q in queries]
        if not any(update_wired_to_query(u, q_ids) for u in updates):
            print(f"FAIL: {path} — update recordId not wired to a query output (found literals or unrelated references)", file=sys.stderr)
            continue
        if not deletes:
            print(f"FAIL: {path} — no delete-entity-record on {ENTITY}", file=sys.stderr)
            continue

        print(f"OK: {path} — {len(loops)} loop(s), "
              f"{len(creates)} create, {len(queries)} query (priority DESC), "
              f"{len(updates)} update (status), {len(deletes)} delete on {ENTITY}")
        return 0

    print("FAIL: no .flow satisfies the bulk-lifecycle shape", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
