#!/usr/bin/env python3
"""Verify the ContractRegistry linear CRUD chain — DF activity ownership only:

- >=1 create-entity-record on ContractRegistry, body contains contractTitle
- >=1 get-entity-record-by-id on ContractRegistry, recordId bound to create output
- >=1 query-entity-records on ContractRegistry, sorted by priority DESC
- >=1 update-entity-record on ContractRegistry, recordId bound to create output,
      body contains ONLY the `status` key
- >=1 delete-entity-record on ContractRegistry, recordId bound to create output

Loop / branch / multi-node orchestration is intentionally NOT enforced —
that's core-flow ownership, not the DF connector's."""
import glob
import json
import sys

ENTITY = "ContractRegistry"


def detail(node):
    return node.get("inputs", {}).get("detail", {}) or {}


def targets_entity(node):
    return (detail(node).get("pathParameters") or {}).get("entityName") == ENTITY


def qparams(node):
    return detail(node).get("queryParameters") or {}


def body(node):
    return detail(node).get("bodyParameters") or {}


def record_id_expr(node):
    """recordId lives in queryParameters for every activity except Create;
    fall back to pathParameters for older CLI encodings."""
    return str(qparams(node).get("recordId") or
               (detail(node).get("pathParameters") or {}).get("recordId") or "")


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


def wired_to_create(node, create_ids):
    """recordId must reference one of the create nodes' output ids."""
    expr = record_id_expr(node)
    if not expr.startswith("=js:"):
        return False
    return any(cid and cid in expr for cid in create_ids)


def main() -> int:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        print("FAIL: no .flow file", file=sys.stderr)
        return 1

    for path in flows:
        with open(path) as f:
            doc = json.load(f)
        creates, gets, queries, updates, deletes = [], [], [], [], []
        for n in doc.get("nodes", []):
            if not targets_entity(n):
                continue
            t = n.get("type", "")
            if t.endswith(".create-entity-record"):
                creates.append(n)
            elif t.endswith(".get-entity-record-by-id"):
                gets.append(n)
            elif t.endswith(".query-entity-records"):
                queries.append(n)
            elif t.endswith(".update-entity-record"):
                updates.append(n)
            elif t.endswith(".delete-entity-record"):
                deletes.append(n)

        if not creates:
            print(f"FAIL: {path} — no create-entity-record on {ENTITY}", file=sys.stderr)
            continue
        if not any("contractTitle" in body(c) for c in creates):
            print(f"FAIL: {path} — create body missing contractTitle", file=sys.stderr)
            continue

        create_ids = [c.get("id") for c in creates]

        if not gets:
            print(f"FAIL: {path} — no get-entity-record-by-id on {ENTITY}", file=sys.stderr)
            continue
        if not any(wired_to_create(g, create_ids) for g in gets):
            print(f"FAIL: {path} — get recordId not wired to create output", file=sys.stderr)
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
        partial_status_update = [u for u in updates if set(body(u).keys()) == {"status"}]
        if not partial_status_update:
            keys_seen = [sorted(body(u).keys()) for u in updates]
            print(f"FAIL: {path} — no update whose body is exactly {{'status'}} "
                  f"(found: {keys_seen})", file=sys.stderr)
            continue
        if not any(wired_to_create(u, create_ids) for u in partial_status_update):
            print(f"FAIL: {path} — status-only update recordId not wired to create output",
                  file=sys.stderr)
            continue

        if not deletes:
            print(f"FAIL: {path} — no delete-entity-record on {ENTITY}", file=sys.stderr)
            continue
        if not any(wired_to_create(d, create_ids) for d in deletes):
            print(f"FAIL: {path} — delete recordId not wired to create output", file=sys.stderr)
            continue

        print(f"OK: {path} — Create → Get → Query(priority DESC) → "
              f"Update(status only) → Delete, all on {ENTITY}, recordId chained "
              f"from create output")
        return 0

    print("FAIL: no .flow satisfies the CRUD-chain shape", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
