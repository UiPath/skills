#!/usr/bin/env python3
"""Advisory: the Data Service query should filter server-side.

A build that pulls the whole entity (paging params only) and filters in a
script passes the 8-row oracle on seeded data but silently breaks once the
entity outgrows the page limit. This check records which route the build took;
it is advisory (pass_threshold 0) and never gates the score.

Passes when the query-entity-records node carries a non-empty filter — a
`queryExpression` (inline or `=js:` bound) or a structured filter/filterGroup,
including the `{var_…}` + `filterVariables` form `node configure` emits for
dynamic operands.
"""
import glob
import json
import sys


def find_flow() -> dict:
    for p in glob.glob("**/*.flow", recursive=True):
        try:
            return json.load(open(p, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    print("ADVISORY FAIL: no .flow file found")
    sys.exit(1)


def has_filter(obj) -> bool:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("queryExpression", "filter", "filterGroup", "filterVariables") and v not in (None, "", {}, []):
                return True
            if has_filter(v):
                return True
    elif isinstance(obj, list):
        return any(has_filter(v) for v in obj)
    return False


flow = find_flow()
queries = [n for n in flow.get("nodes", []) if "query-entity-records" in n.get("type", "")]
if not queries:
    print("ADVISORY FAIL: no query-entity-records node")
    sys.exit(1)

unfiltered = [n["id"] for n in queries if not has_filter(n.get("inputs", {}))]
if unfiltered:
    print(f"ADVISORY FAIL: no server-side filter on {', '.join(unfiltered)} — "
          "entity fetched whole and filtered client-side; breaks silently past the page limit")
    sys.exit(1)
print("OK: query filters server-side")
