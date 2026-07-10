#!/usr/bin/env python3
"""Verify a .flow file contains the given DF ops on the given entity.

Usage: check_ops_present.py <entity> <op-suffix> [<op-suffix>...]

Op-suffix is the tail of node.type after the last dot, e.g. `create-entity-record`.
Passes if any single .flow under CWD has >=1 node of every requested op-type
on that entity."""
import glob, json, sys

if len(sys.argv) < 3:
    print("usage: check_ops_present.py <entity> <op-suffix>...", file=sys.stderr); sys.exit(2)

entity, *ops = sys.argv[1], *sys.argv[2:]
required = {f".{op}" for op in ops}

for path in glob.glob("**/*.flow", recursive=True):
    with open(path) as f: doc = json.load(f)
    seen = set()
    for n in doc.get("nodes", []):
        t = n.get("type", "")
        pp = n.get("inputs", {}).get("detail", {}).get("pathParameters") or {}
        if pp.get("entityName") != entity: continue
        for suffix in required:
            if t.endswith(suffix): seen.add(suffix)
    if required.issubset(seen):
        print(f"OK: {path} has {sorted(seen)} on {entity}"); sys.exit(0)
print(f"FAIL: no .flow has all {len(required)} ops on {entity}: {sorted(required)}", file=sys.stderr); sys.exit(1)
