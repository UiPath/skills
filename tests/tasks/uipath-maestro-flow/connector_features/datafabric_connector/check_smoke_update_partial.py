#!/usr/bin/env python3
"""Update node's bodyParameters must contain only 'score' (partial update)."""
import glob, json, sys
for path in glob.glob("**/*.flow", recursive=True):
    with open(path) as f: doc = json.load(f)
    for n in doc.get("nodes", []):
        if not n.get("type","").endswith(".update-entity-record"): continue
        body = (n.get("inputs",{}).get("detail",{}).get("bodyParameters") or {})
        keys = set(body.keys())
        if keys == {"score"}:
            print(f"OK: {path} update body = {sorted(keys)}"); sys.exit(0)
        print(f"FAIL: {path} update body has {sorted(keys)}, expected only 'score'", file=sys.stderr)
        sys.exit(1)
print("FAIL: no update-entity-record node found", file=sys.stderr); sys.exit(1)
