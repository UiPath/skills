#!/usr/bin/env python3
"""Verify Data Fabric created/updated trigger regression coverage."""
import glob
import json
import sys


def load_nodes():
    for path in glob.glob("**/*.flow", recursive=True):
        with open(path) as f:
            doc = json.load(f)
        for node in doc.get("nodes", []):
            yield path, doc, node


def detail(node):
    return node.get("inputs", {}).get("detail", {}) or {}


def text(value):
    return str(value or "").lower()


def has_due_filter(d):
    values = [d.get("filterExpression"), d.get("filter")]
    config = d.get("configuration")
    if config:
        values.append(config)
    joined = text(values)
    return "duedate" in joined and "2026-08-04" in joined and "<" in joined


def main():
    all_nodes = list(load_nodes())
    created = []
    updated = []
    queries = []
    gets = []
    deletes = []

    for path, doc, node in all_nodes:
        t = node.get("type", "")
        d = detail(node)
        if t.endswith(".record-created"):
            created.append((path, node))
        elif t.endswith(".record-updated"):
            updated.append((path, node))
        elif t.endswith(".query-entity-records"):
            queries.append((path, node))
        elif t.endswith(".get-entity-record-by-id"):
            gets.append((path, node))
        elif t.endswith(".delete-entity-record"):
            deletes.append((path, node))

    contract_created = [n for _, n in created if detail(n).get("objectName") == "ContractRegistry"]
    if not contract_created:
        print("FAIL: Record Created trigger for ContractRegistry missing", file=sys.stderr)
        return 1
    if not any(has_due_filter(detail(n)) for n in contract_created):
        print("FAIL: ContractRegistry Record Created trigger lacks dueDate < 2026-08-04 filter", file=sys.stderr)
        return 1

    contract_queries = []
    for _, n in queries:
        if (detail(n).get("pathParameters") or {}).get("entityName") == "ContractRegistry":
            contract_queries.append(n)
    if not contract_queries:
        print("FAIL: Query Entity Records after ContractRegistry trigger missing", file=sys.stderr)
        return 1
    qfilters = [detail(n).get("queryParameters", {}).get("queryExpression") for n in contract_queries]
    if not any("duedate" in text(q) and "2026-08-04" in text(q) and "<" in text(q) for q in qfilters):
        print(f"FAIL: ContractRegistry query lacks dueDate filter: {qfilters}", file=sys.stderr)
        return 1
    if not any(str(detail(n).get("queryParameters", {}).get("limit")) == "100" for n in contract_queries):
        print("FAIL: ContractRegistry query does not set limit=100", file=sys.stderr)
        return 1

    file_updated = [n for _, n in updated if detail(n).get("objectName") == "FileUploadVerify_20260618"]
    if not file_updated:
        print("FAIL: Record Updated trigger for FileUploadVerify_20260618 missing", file=sys.stderr)
        return 1
    trigger_ids = {n.get("id", "") for n in file_updated}
    file_gets = [n for _, n in gets if (detail(n).get("pathParameters") or {}).get("entityName") == "FileUploadVerify_20260618"]
    file_deletes = [n for _, n in deletes if (detail(n).get("pathParameters") or {}).get("entityName") == "FileUploadVerify_20260618"]
    if not file_gets or not file_deletes:
        print("FAIL: FileUploadVerify updated flow must contain Get and Delete activities", file=sys.stderr)
        return 1
    get_ids = [str((detail(n).get("queryParameters") or {}).get("recordId", "")) for n in file_gets]
    delete_ids = [str((detail(n).get("queryParameters") or {}).get("recordId", "")) for n in file_deletes]
    if not any(any(tid in value for tid in trigger_ids) for value in get_ids):
        print(f"FAIL: Get recordId is not bound to Record Updated trigger output: {get_ids}", file=sys.stderr)
        return 1
    if not any(any(tid in value or "get" in value.lower() for tid in trigger_ids) for value in delete_ids):
        print(f"FAIL: Delete recordId is not bound to trigger/Get output: {delete_ids}", file=sys.stderr)
        return 1

    print("OK: ContractRegistry created trigger/query and FileUploadVerify updated trigger/get/delete are fully bound")
    return 0


if __name__ == "__main__":
    sys.exit(main())
