#!/usr/bin/env python3
"""Verify smoke_create_all_types: single .flow with a DF Create node whose
bodyParameters cover all 8 supported field types on FlowCodeEvalEntity."""
import glob
import json
import sys

EXPECTED_FIELDS = {"title", "description", "score", "viewCount",
                   "active", "releaseDate", "lastUpdated", "externalId"}
ENTITY = "FlowCodeEvalEntity"


def main() -> int:
    flows = glob.glob("**/*.flow", recursive=True)
    if not flows:
        print("FAIL: no .flow file found", file=sys.stderr)
        return 1

    for path in flows:
        with open(path) as f:
            doc = json.load(f)
        for node in doc.get("nodes", []):
            ntype = node.get("type", "")
            if not ntype.endswith(".create-entity-record"):
                continue
            detail = node.get("inputs", {}).get("detail", {})
            body = detail.get("bodyParameters") or {}
            path_params = detail.get("pathParameters") or {}
            missing = EXPECTED_FIELDS - set(body.keys())
            if missing:
                print(f"FAIL: {path} Create node missing bodyParameters: {sorted(missing)}", file=sys.stderr)
                return 1
            if path_params.get("entityName") != ENTITY:
                print(f"FAIL: {path} Create pathParameters.entityName={path_params.get('entityName')!r}, expected {ENTITY!r}", file=sys.stderr)
                return 1
            print(f"OK: {path} — Create body covers all 8 fields on {ENTITY}")
            return 0

    print("FAIL: no create-entity-record node in any .flow", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
