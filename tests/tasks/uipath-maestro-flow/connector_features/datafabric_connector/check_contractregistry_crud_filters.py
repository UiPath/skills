#!/usr/bin/env python3
"""Verify the ContractRegistry CRUD/filter regression scenario."""
import glob
import json
import re
import sys

ENTITY = "ContractRegistry"
FIELDS = {"contractTitle", "status", "priority", "dueDate", "value", "isUrgent"}


def nodes():
    for path in glob.glob("**/*.flow", recursive=True):
        with open(path) as f:
            doc = json.load(f)
        for node in doc.get("nodes", []):
            yield path, doc, node


def detail(node):
    return node.get("inputs", {}).get("detail", {}) or {}


def entity_is_contract(detail_value, doc):
    entity = (detail_value.get("pathParameters") or {}).get("entityName")
    if entity == ENTITY:
        return True
    if not isinstance(entity, str):
        return False
    # Accept a workflow expression only when its backing global has an
    # explicit ContractRegistry default; an unresolved/null expression is the
    # regression this task is intended to catch.
    for global_var in (doc.get("variables", {}).get("globals") or []):
        if global_var.get("id") and global_var.get("id") in entity:
            return global_var.get("defaultValue", global_var.get("default")) == ENTITY
    return False


def expr_contains(value, *parts):
    text = str(value or "").lower()
    return all(part.lower() in text for part in parts)


def main():
    all_nodes = list(nodes())
    if not all_nodes:
        print("FAIL: no .flow file found", file=sys.stderr)
        return 1

    manual = [n for _, _, n in all_nodes if n.get("type") == "core.trigger.manual"]
    if not manual:
        print("FAIL: manual trigger missing", file=sys.stderr)
        return 1

    creates = []
    queries = []
    updates = []
    gets = []
    for path, doc, node in all_nodes:
        d = detail(node)
        if not entity_is_contract(d, doc):
            continue
        t = node.get("type", "")
        if t.endswith(".create-entity-record"):
            creates.append((path, node))
        elif t.endswith(".query-entity-records"):
            queries.append((path, node))
        elif t.endswith(".update-entity-record"):
            updates.append((path, node))
        elif t.endswith(".get-entity-record-by-id"):
            gets.append((path, node))

    if not creates:
        print("FAIL: ContractRegistry Create Entity Record missing", file=sys.stderr)
        return 1
    body = detail(creates[0][1]).get("bodyParameters") or {}
    missing = FIELDS - set(body)
    if missing:
        print(f"FAIL: Create body missing fields: {sorted(missing)}", file=sys.stderr)
        return 1
    if len(queries) < 2:
        print(f"FAIL: expected 2 ContractRegistry Query nodes, found {len(queries)}", file=sys.stderr)
        return 1

    expressions = [((detail(n).get("queryParameters") or {}).get("queryExpression")) for _, n in queries]
    if not any(expr_contains(e, "duedate", "<", "2026-08-04") for e in expressions):
        print(f"FAIL: no Query filter for dueDate < 2026-08-04: {expressions}", file=sys.stderr)
        return 1
    if not any(expr_contains(e, "contracttitle", "null") for e in expressions):
        print(f"FAIL: no Query filter for contractTitle null: {expressions}", file=sys.stderr)
        return 1
    for _, n in queries:
        limit = (detail(n).get("queryParameters") or {}).get("limit")
        if str(limit) != "100":
            print(f"FAIL: Query limit must be 100, found {limit!r}", file=sys.stderr)
            return 1

    if not updates:
        print("FAIL: ContractRegistry Update Entity Record missing", file=sys.stderr)
        return 1
    update_body = detail(updates[0][1]).get("bodyParameters") or {}
    if "contractTitle" not in update_body:
        print("FAIL: update body does not update contractTitle", file=sys.stderr)
        return 1
    title_value = str(update_body["contractTitle"])
    if not ("$vars." in title_value or "random" in title_value.lower() or "title" in title_value.lower()):
        print(f"FAIL: contractTitle update is not variable/random-bound: {title_value!r}", file=sys.stderr)
        return 1

    if not gets:
        print("FAIL: ContractRegistry Get Entity Record by ID missing", file=sys.stderr)
        return 1
    record_ids = [str((detail(n).get("queryParameters") or {}).get("recordId", "")) for _, n in gets]
    if not any("$vars." in value and ("update" in value.lower() or "record" in value.lower()) for value in record_ids):
        print(f"FAIL: Get-by-Id is not wired to an upstream update output: {record_ids}", file=sys.stderr)
        return 1

    if not any(n.get("outputs") for _, _, n in all_nodes if n.get("type") == "core.control.end"):
        print("FAIL: no mapped flow output found on End node", file=sys.stderr)
        return 1

    print(f"OK: {len(creates)} create, {len(queries)} query, {len(updates)} update, {len(gets)} get nodes; filters and bindings present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
