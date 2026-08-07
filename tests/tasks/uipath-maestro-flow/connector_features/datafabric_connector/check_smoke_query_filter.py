#!/usr/bin/env python3
"""Verify 3 query nodes each carry a CEQL queryExpression using SQL symbols."""
import glob, json, re, sys
found = []
for path in glob.glob("**/*.flow", recursive=True):
    with open(path) as f: doc = json.load(f)
    for n in doc.get("nodes", []):
        if not n.get("type","").endswith(".query-entity-records"): continue
        qp = n.get("inputs",{}).get("detail",{}).get("queryParameters",{}) or {}
        qe = qp.get("queryExpression")
        if qe: found.append(qe)
if len(found) < 3:
    print(f"FAIL: expected >=3 query nodes with queryExpression, got {len(found)}", file=sys.stderr); sys.exit(1)
# forbid enum-style operator names
banned = re.compile(r'\b(Equals|GreaterThan|LessThan|Contains|NotEquals)\b')
for qe in found:
    if banned.search(qe):
        print(f"FAIL: enum-style operator found in {qe!r}", file=sys.stderr); sys.exit(1)
print(f"OK: {len(found)} queryExpressions, all SQL-symbol"); sys.exit(0)
