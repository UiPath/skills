#!/usr/bin/env python3
"""Verify smoke_error targets the right entities: Create on NonExistentEntity,
Queries on FlowCodeEvalEntity. Closes the wrong-reason pass where an agent
builds a valid FlowCodeEvalEntity Create + 2 Queries and satisfies the loose
command_executed criteria.

Note: entity-binding check only; topology (parallel branch) is not parsed —
the prompt-driven shape plus entity split already blocks the common wrong-reason
paths. Add topology parsing if a live case slips through."""
import glob, json, sys

CREATE_ENTITY = "NonExistentEntity"
QUERY_ENTITY = "FlowCodeEvalEntity"


def entity_of(node):
    pp = node.get("inputs", {}).get("detail", {}).get("pathParameters") or {}
    return pp.get("entityName")


for path in glob.glob("**/*.flow", recursive=True):
    with open(path) as f:
        doc = json.load(f)
    nodes = doc.get("nodes", [])
    error_creates = [n for n in nodes
                     if n.get("type", "").endswith(".create-entity-record")
                     and entity_of(n) == CREATE_ENTITY]
    good_queries = [n for n in nodes
                    if n.get("type", "").endswith(".query-entity-records")
                    and entity_of(n) == QUERY_ENTITY]

    if not error_creates:
        print(f"FAIL: {path} — no create-entity-record targeting {CREATE_ENTITY!r}",
              file=sys.stderr)
        continue
    if len(good_queries) < 2:
        print(f"FAIL: {path} — expected >=2 query nodes on {QUERY_ENTITY!r}, "
              f"found {len(good_queries)}", file=sys.stderr)
        continue

    print(f"OK: {path} — create on {CREATE_ENTITY}, "
          f"{len(good_queries)} query on {QUERY_ENTITY}")
    sys.exit(0)

print("FAIL: no .flow satisfies the error-path shape", file=sys.stderr)
sys.exit(1)
