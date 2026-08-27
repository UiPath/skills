#!/usr/bin/env python3
"""Verify the complete filter and pagination matrix for the query smoke.

The Flow author may persist a filter as a runtime expression or as the
structured FilterBuilder tree used by the design-time activity. The test
checks either representation so the prompt does not prescribe serialization.
"""
import glob, json, re, sys


UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
EXPECTED = {
    "boolean": ("active", ("true",), ()),
    "decimal": ("score", ("8.5",), ("greaterthanorequal", ">=")),
    "integer": ("viewcount", ("1000",), ("greaterthanorequal", ">=")),
    "string": ("title", ("filterfixture-matrix",), ("equals", "=")),
    "multiline": ("description", ("sci-fi",), ("contains",)),
    "date": ("releasedate", ("2025-01-01",), ("lessthan", "<")),
    "datetime": ("lastupdated", ("2024-01-01",), ("greaterthanorequal", ">=")),
    "uuid": ("externalid", (), ()),
    "null": ("description", (), ("isnull", "is null")),
}


def structured_filter_leaves(detail):
    config = detail.get("configuration")
    if not isinstance(config, str):
        return []
    raw = config.removeprefix("=jsonString:")
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    trees = (parsed.get("essentialConfiguration", {})
             .get("savedFilterTrees", {}))
    tree = trees.get("queryExpression", {}) if isinstance(trees, dict) else {}
    leaves = []

    def walk(group):
        if not isinstance(group, dict):
            return
        leaves.extend(group.get("filters") or [])
        for child in group.get("groups") or []:
            walk(child)

    walk(tree)
    return leaves


def node_filter_text(detail):
    qp = detail.get("queryParameters", {}) or {}
    values = []
    if qp.get("queryExpression"):
        values.append(str(qp["queryExpression"]))
    leaves = structured_filter_leaves(detail)
    if leaves:
        values.append(json.dumps(leaves))
    return " ".join(values).lower()


def has_expected_filter(text, field, tokens, operators):
    return (field in text
            and all(token.lower() in text for token in tokens)
            and (field != "externalid" or UUID_RE.search(text))
            and (not operators or any(op.lower() in text for op in operators)))


filtered = []
all_query_details = []
for path in glob.glob("**/*.flow", recursive=True):
    with open(path) as f: doc = json.load(f)
    for n in doc.get("nodes", []):
        if not n.get("type","").endswith(".query-entity-records"): continue
        detail = n.get("inputs", {}).get("detail", {}) or {}
        all_query_details.append(detail)
        text = node_filter_text(detail)
        if text:
            filtered.append((detail, text))

missing = [name for name, (field, tokens, operators) in EXPECTED.items()
           if not any(has_expected_filter(text, field, tokens, operators)
                      for _, text in filtered)]
if missing:
    print(f"FAIL: missing filter coverage: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)

matrix_nodes = [text for _, text in filtered
                if all(has_expected_filter(text, field, tokens, operators)
                       for field, tokens, operators in EXPECTED.values())]
if not matrix_nodes:
    print("FAIL: the nine filter conditions are split across query nodes; "
          "one Query Entity Records node must contain the complete FilterBuilder tree",
          file=sys.stderr)
    sys.exit(1)

if len(all_query_details) != 3:
    print(f"FAIL: expected exactly 3 Query Entity Records activities, found {len(all_query_details)}",
          file=sys.stderr)
    sys.exit(1)

def qp(detail):
    return detail.get("queryParameters", {}) or {}

def sort_field(detail):
    query = qp(detail)
    body = detail.get("bodyParameters", {}) or {}
    return query.get("_sortFieldName") or body.get("_sortFieldName")

ascending_pages = [d for d in all_query_details
                   if sort_field(d) == "score"
                   and str(qp(d).get("isAscending")).lower() == "true"
                   and str(qp(d).get("limit")) == "2"]
if not any(str(qp(d).get("start")) == "0" for d in ascending_pages):
    print("FAIL: missing first ascending score page with start=0 and limit=2", file=sys.stderr)
    sys.exit(1)
if not any(str(qp(d).get("start")) == "2" for d in ascending_pages):
    print("FAIL: missing second ascending score page with start=2 and limit=2", file=sys.stderr)
    sys.exit(1)

descending_active = [d for d in all_query_details
                     if sort_field(d) == "score"
                     and str(qp(d).get("isAscending")).lower() == "false"
                     and str(qp(d).get("limit")) == "4"
                     and "active" in node_filter_text(d)
                     and "true" in node_filter_text(d)]
if not descending_active:
    print("FAIL: missing active descending score page with limit=4", file=sys.stderr)
    sys.exit(1)

print("OK: 3 query activities; one contains all 9 filter cases and pagination/sort checks pass")
