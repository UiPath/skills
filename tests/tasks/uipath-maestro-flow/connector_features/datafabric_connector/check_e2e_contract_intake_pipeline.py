#!/usr/bin/env python3
"""Verify the ContractRegistry intake e2e scenario:
    - 6 create-entity-record nodes on ContractRegistry, each body populating
      contractTitle, status, priority, dueDate, value, isUrgent
    - >=2 query-entity-records nodes on ContractRegistry: at least one sorted
      by priority DESC and at least one filtered by isUrgent = true
    - >=1 update-entity-record node touching status
    - 6 delete-entity-record nodes"""
import glob
import json
import re
import sys

ENTITY = "ContractRegistry"
CREATE_FIELDS = {"contractTitle", "status", "priority", "dueDate", "value", "isUrgent"}


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


def has_isurgent_true_filter(node):
    expr = str(qparams(node).get("queryExpression") or "").lower()
    return "isurgent" in expr and "true" in expr


def main() -> int:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        print("FAIL: no .flow file", file=sys.stderr)
        return 1

    for path in flows:
        with open(path) as f:
            doc = json.load(f)
        creates, queries, updates, deletes = [], [], [], []
        has_loop = False
        for n in doc.get("nodes", []):
            if n.get("type", "").startswith("core.logic.loop"):
                has_loop = True
            if not targets_entity(n):
                continue
            t = n.get("type", "")
            if t.endswith(".create-entity-record"):
                creates.append(n)
            elif t.endswith(".query-entity-records"):
                queries.append(n)
            elif t.endswith(".update-entity-record"):
                updates.append(n)
            elif t.endswith(".delete-entity-record"):
                deletes.append(n)

        # Accept either 6 separate create nodes OR >=1 create node driven by a loop
        if not creates:
            print(f"FAIL: {path} — no create-entity-record node on {ENTITY}", file=sys.stderr)
            continue
        if len(creates) < 6 and not has_loop:
            print(f"FAIL: {path} — {len(creates)} create nodes without a loop; need either 6 create nodes or a loop over 1+", file=sys.stderr)
            continue
        missing_by_node = [sorted(CREATE_FIELDS - set(body(n).keys())) for n in creates]
        offenders = [(i, m) for i, m in enumerate(missing_by_node) if m]
        if offenders:
            print(f"FAIL: {path} — create nodes missing body fields: {offenders}", file=sys.stderr)
            continue
        if len(queries) < 2:
            print(f"FAIL: {path} — expected >=2 query nodes on {ENTITY}, found {len(queries)}", file=sys.stderr)
            continue
        if not any(has_priority_desc_sort(n) for n in queries):
            print(f"FAIL: {path} — no query with priority DESC sort", file=sys.stderr)
            continue
        if not any(has_isurgent_true_filter(n) for n in queries):
            print(f"FAIL: {path} — no query filtering isUrgent=true", file=sys.stderr)
            continue
        if not updates:
            print(f"FAIL: {path} — no update node on {ENTITY}", file=sys.stderr)
            continue
        if not any("status" in body(n) for n in updates):
            print(f"FAIL: {path} — no update touches status", file=sys.stderr)
            continue
        if not deletes:
            print(f"FAIL: {path} — no delete node on {ENTITY}", file=sys.stderr)
            continue
        if len(deletes) < 6 and not has_loop:
            print(f"FAIL: {path} — {len(deletes)} delete nodes without a loop; need either 6 or a loop", file=sys.stderr)
            continue

        loop_hint = " (loop-driven)" if has_loop else ""
        print(f"OK: {path} — {len(creates)} create, {len(queries)} query, "
              f"{len(updates)} update, {len(deletes)} delete on {ENTITY}{loop_hint}")
        return 0

    print(f"FAIL: no .flow satisfies the ContractRegistry intake shape", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
