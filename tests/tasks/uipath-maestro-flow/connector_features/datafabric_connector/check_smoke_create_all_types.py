#!/usr/bin/env python3
"""Verify smoke_create_all_types: single .flow with a DF Create node whose
bodyParameters cover all 8 supported field types on FlowCodeEvalEntity, each
carrying either the correct JSON literal shape or a `=js:` expression binding.

Any value starting with `=js:` is accepted for the type-check (agent may be
binding the value to a workflow variable — grade wiring, not literal choice)."""
import glob
import json
import re
import sys

ENTITY = "FlowCodeEvalEntity"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2})?")


def _is_expression(v):
    return isinstance(v, str) and v.startswith("=js:")


def _check_str(v):
    return isinstance(v, str)


def _check_number(v):
    # DECIMAL accepts int OR float (7.25 or 7)
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _check_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _check_bool(v):
    return isinstance(v, bool)


def _check_date(v):
    return isinstance(v, str) and bool(DATE_RE.match(v))


def _check_datetime(v):
    return isinstance(v, str) and bool(DATETIME_RE.match(v))


def _check_uuid(v):
    return isinstance(v, str) and bool(UUID_RE.match(v))


EXPECTED = {
    "title":        ("STRING",         _check_str),
    "description":  ("MULTILINE_TEXT", _check_str),
    "score":        ("DECIMAL",        _check_number),
    "viewCount":    ("INTEGER",        _check_int),
    "active":       ("BOOLEAN",        _check_bool),
    "releaseDate":  ("DATE",           _check_date),
    "lastUpdated":  ("DATETIME",       _check_datetime),
    "externalId":   ("UUID",           _check_uuid),
}


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
            missing = set(EXPECTED) - set(body.keys())
            if missing:
                print(f"FAIL: {path} Create node missing bodyParameters: {sorted(missing)}", file=sys.stderr)
                return 1
            if path_params.get("entityName") != ENTITY:
                print(f"FAIL: {path} Create pathParameters.entityName={path_params.get('entityName')!r}, expected {ENTITY!r}", file=sys.stderr)
                return 1
            type_errors = []
            for field, (label, check) in EXPECTED.items():
                v = body[field]
                if _is_expression(v):
                    continue
                if not check(v):
                    type_errors.append((field, label, type(v).__name__, v))
            if type_errors:
                print(f"FAIL: {path} type mismatches in Create body:", file=sys.stderr)
                for f, lbl, got, val in type_errors:
                    print(f"  {f} ({lbl}): got {got}={val!r}", file=sys.stderr)
                return 1
            print(f"OK: {path} — Create body covers all 8 fields on {ENTITY} with matching JSON-literal shapes")
            return 0

    print("FAIL: no create-entity-record node in any .flow", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
