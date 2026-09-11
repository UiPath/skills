#!/usr/bin/env python3
"""Advisory: the Data Service query should filter server-side.

A build that pulls the whole entity (paging params only) and filters in a
script passes the 8-row oracle on seeded data but silently breaks once the
entity outgrows the page limit. This check records which route the build took;
it is advisory (pass_threshold 0) and never gates the score.

Passes when the read carries a non-empty filter. On the Data Service connector
that is a `queryExpression` (inline or `=js:` bound) or a structured
filter/filterGroup, including the `{var_…}` + `filterVariables` form `node
configure` emits for dynamic operands. On the native `core.datafabric.read` node
it is at least one `entityConfig._filters` row — the container is always present,
so its emptiness is what matters.
"""
import glob
import json
import os
import sys

_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d) and not os.path.isdir(os.path.join(_d, "_shared")):
    _d = os.path.dirname(_d)
sys.path.insert(0, _d)
from _shared.advisory_flow_utils import (  # noqa: E402
    NATIVE_READ_TYPE,
    native_filter_rows,
)


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


def filters_server_side(node) -> bool:
    if node.get("type") == NATIVE_READ_TYPE:
        return bool(native_filter_rows(node))
    return has_filter(node.get("inputs", {}))


flow = find_flow()
queries = [
    n
    for n in flow.get("nodes", [])
    if "query-entity-records" in n.get("type", "") or n.get("type") == NATIVE_READ_TYPE
]
if not queries:
    print("ADVISORY FAIL: no entity-read node (query-entity-records or core.datafabric.read)")
    sys.exit(1)

unfiltered = [n["id"] for n in queries if not filters_server_side(n)]
if unfiltered:
    print(f"ADVISORY FAIL: no server-side filter on {', '.join(unfiltered)} — "
          "entity fetched whole and filtered client-side; breaks silently past the page limit")
    sys.exit(1)
print("OK: query filters server-side")
