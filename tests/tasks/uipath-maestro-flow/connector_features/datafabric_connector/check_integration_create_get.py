#!/usr/bin/env python3
"""Verify integration_create_get: at least 2 Create nodes and >=1 Get node
with expansionLevel=3 on FlowCodeEvalEntity."""
import glob
import json
import sys

ENTITY = "FlowCodeEvalEntity"


def main() -> int:
    creates = 0
    gets = 0
    max_expansion = 0
    for path in glob.glob("**/*.flow", recursive=True):
        with open(path) as f:
            doc = json.load(f)
        for node in doc.get("nodes", []):
            ntype = node.get("type", "")
            detail = node.get("inputs", {}).get("detail", {})
            path_params = detail.get("pathParameters") or {}
            if path_params.get("entityName") != ENTITY:
                continue
            if ntype.endswith(".create-entity-record"):
                creates += 1
            elif ntype.endswith(".get-entity-record-by-id"):
                gets += 1
                exp = (detail.get("queryParameters") or {}).get("expansionLevel")
                try:
                    max_expansion = max(max_expansion, int(exp))
                except (TypeError, ValueError):
                    pass

    if creates < 2:
        print(f"FAIL: expected >=2 create nodes on {ENTITY}, found {creates}", file=sys.stderr)
        return 1
    if gets < 4:
        print(f"FAIL: expected >=4 get nodes on {ENTITY}, found {gets}", file=sys.stderr)
        return 1
    if max_expansion < 3:
        print(f"FAIL: no Get node with expansionLevel=3 (max found: {max_expansion})", file=sys.stderr)
        return 1
    print(f"OK: {creates} creates, {gets} gets, max expansionLevel={max_expansion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
