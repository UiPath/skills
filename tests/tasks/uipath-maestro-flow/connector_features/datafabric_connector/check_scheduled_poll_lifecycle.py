#!/usr/bin/env python3
"""Verify the Data Fabric scheduled-poll regression coverage.

Data Fabric exposes no `uipath.connector.trigger.uipath-uipath-dataservice.*`
node, so the graded start is `core.trigger.scheduled`. Every flow must carry
one; a leftover `core.trigger.manual` fails.
"""
import glob
import json
import sys

SCHEDULED = "core.trigger.scheduled"
MANUAL = "core.trigger.manual"
CONTRACT_ENTITY = "ContractRegistry"
FILE_ENTITY = "FileUploadVerify_20260618"


def load_flows():
    for path in sorted(glob.glob("**/*.flow", recursive=True)):
        with open(path) as f:
            yield path, json.load(f)


def detail(node):
    return node.get("inputs", {}).get("detail", {}) or {}


def text(value):
    return str(value or "").lower()


def entity_name(d):
    return d.get("entityName") or (d.get("pathParameters") or {}).get("entityName")


def query_params(node):
    return detail(node).get("queryParameters") or {}


def has_due_filter(node):
    joined = text(query_params(node).get("queryExpression"))
    return "duedate" in joined and "2026-08-04" in joined and "<" in joined


def main():
    flows = list(load_flows())
    if len(flows) < 2:
        print(f"FAIL: expected two .flow projects, found {len(flows)}", file=sys.stderr)
        return 1

    queries = []
    gets = []
    deletes = []
    for path, doc in flows:
        types = [n.get("type", "") for n in doc.get("nodes", [])]
        if MANUAL in types:
            print(f"FAIL: {path} still starts on {MANUAL}", file=sys.stderr)
            return 1
        if SCHEDULED not in types:
            print(f"FAIL: {path} has no {SCHEDULED} node", file=sys.stderr)
            return 1
        for node in doc.get("nodes", []):
            t = node.get("type", "")
            if t.endswith(".query-entity-records"):
                queries.append((path, node))
            elif t.endswith(".get-entity-record-by-id"):
                gets.append((path, node))
            elif t.endswith(".delete-entity-record"):
                deletes.append((path, node))

    contract_queries = [n for p, n in queries if entity_name(detail(n)) == CONTRACT_ENTITY]
    if not contract_queries:
        print(f"FAIL: Query Entity Records on {CONTRACT_ENTITY} missing", file=sys.stderr)
        return 1
    if not any(has_due_filter(n) for n in contract_queries):
        expressions = [query_params(n).get("queryExpression") for n in contract_queries]
        print(f"FAIL: {CONTRACT_ENTITY} query lacks dueDate < 2026-08-04 filter: {expressions}", file=sys.stderr)
        return 1
    if not any(str(query_params(n).get("limit")) == "100" for n in contract_queries):
        print(f"FAIL: {CONTRACT_ENTITY} query does not set limit=100", file=sys.stderr)
        return 1

    contract_paths = {p for p, n in queries if entity_name(detail(n)) == CONTRACT_ENTITY}
    file_queries = [n for p, n in queries if entity_name(detail(n)) == FILE_ENTITY]
    file_paths = {p for p, n in queries if entity_name(detail(n)) == FILE_ENTITY}
    file_gets = [n for p, n in gets if entity_name(detail(n)) == FILE_ENTITY]
    file_deletes = [n for p, n in deletes if entity_name(detail(n)) == FILE_ENTITY]
    if not file_queries:
        print(f"FAIL: Query Entity Records on {FILE_ENTITY} missing", file=sys.stderr)
        return 1
    if not any(str(query_params(n).get("limit")) == "1" for n in file_queries):
        print(f"FAIL: {FILE_ENTITY} query does not set limit=1", file=sys.stderr)
        return 1
    if not file_gets or not file_deletes:
        print(f"FAIL: {FILE_ENTITY} flow must contain Get and Delete activities", file=sys.stderr)
        return 1

    shared = file_paths & contract_paths
    if shared:
        print(f"FAIL: {CONTRACT_ENTITY} and {FILE_ENTITY} must be polled by separate flows; both in {sorted(shared)}", file=sys.stderr)
        return 1

    query_ids = {n.get("id", "") for n in file_queries} - {""}
    get_ids = {n.get("id", "") for n in file_gets} - {""}
    get_values = [str(query_params(n).get("recordId", "")) for n in file_gets]
    delete_values = [str(query_params(n).get("recordId", "")) for n in file_deletes]
    if not any(any(qid in value for qid in query_ids) for value in get_values):
        print(f"FAIL: Get recordId is not bound to the {FILE_ENTITY} query output: {get_values}", file=sys.stderr)
        return 1
    if not any(any(gid in value for gid in get_ids) for value in delete_values):
        print(f"FAIL: Delete recordId is not bound to the Get output: {delete_values}", file=sys.stderr)
        return 1

    print(f"OK: both flows poll on {SCHEDULED}; {CONTRACT_ENTITY} query filtered and capped, {FILE_ENTITY} query/get/delete chained")
    return 0


if __name__ == "__main__":
    sys.exit(main())
