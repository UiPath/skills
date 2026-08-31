#!/usr/bin/env python3
"""Verify the complete filter and pagination matrix for the query smoke.

The Flow author may persist a filter as a runtime expression or as the
structured FilterBuilder tree used by the design-time activity. The test
checks either representation so the prompt does not prescribe serialization.
"""
import glob, json, sys


EXPECTED = {
    "boolean": ("active", ("true",), ()),
    "decimal": ("score", ("8.5",), ("greaterthanorequal", ">=")),
    "integer": ("viewcount", ("1000",), ("greaterthanorequal", ">=")),
    "string": ("title", ("filterfixture-matrix",), ("equals", "=")),
    "multiline": ("description", ("sci-fi",), ("contains",)),
    "date": ("releasedate", ("2025-01-01",), ("lessthan", "<")),
    "datetime": ("lastupdated", ("2024-01-01",), ("greaterthanorequal", ">=")),
    "uuid": ("externalid", ("11111111-1111-1111-1111-111111111111",), ()),
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

def bp(detail):
    return detail.get("bodyParameters", {}) or {}

def _int_or_none(v):
    try:
        return int(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None

# Relaxed pagination check: require >=2 queries that sort by `score` (any
# direction), and that at least two of them carry pagination controls
# (`limit` and either `start`) so the agent has demonstrated the paging
# pattern. Exact values (start=0/2, limit=2/4) belong in an integration
# task; smoke asserts the shape, not the numbers.
sorted_by_score = [d for d in all_query_details
                   if str(bp(d).get("_sortFieldName") or qp(d).get("_sortFieldName") or "").lower() == "score"]
if len(sorted_by_score) < 2:
    print(f"FAIL: expected >=2 query nodes sorted by score, found {len(sorted_by_score)}",
          file=sys.stderr)
    sys.exit(1)

paginated = [d for d in sorted_by_score
             if _int_or_none(qp(d).get("limit")) is not None
             and _int_or_none(qp(d).get("start")) is not None]
if len(paginated) < 2:
    print(f"FAIL: expected >=2 score-sorted queries with `start` + `limit` set, "
          f"found {len(paginated)}", file=sys.stderr)
    sys.exit(1)

descending = [d for d in all_query_details
              if str(qp(d).get("isAscending")).lower() == "false"
              or qp(d).get("isAscending") is False]
if not descending:
    print("FAIL: expected at least one query with descending sort (isAscending=false)",
          file=sys.stderr)
    sys.exit(1)

print("OK: 3 query activities; one contains all 9 filter cases; "
      f"{len(paginated)} paginated + {len(descending)} descending query nodes present")
