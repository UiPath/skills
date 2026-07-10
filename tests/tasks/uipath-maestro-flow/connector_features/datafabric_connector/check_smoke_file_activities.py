#!/usr/bin/env python3
"""Verify Upload + Download + Delete file-record-field nodes exist on
FlowCodeEvalEntity, each with a _fieldName that resolves to "file1".

Accepts the field value as either the literal string "file1" or a
`=js:$vars.<var>` expression whose backing global in `variables.globals`
defaults to "file1". The prompt permits variable binding — the test grades
whether the wiring reaches "file1" at authoring time, not whether the
agent picked a literal or a var."""
import glob
import json
import re
import sys

ENTITY = "FlowCodeEvalEntity"
FIELD = "file1"
REQUIRED = {
    ".upload-file-to-record-field",
    ".download-file-from-record-field",
    ".delete-file-from-record-field",
}


def resolve_field(value, globals_by_id) -> str | None:
    """Return the literal string the _fieldName expression resolves to,
    or None if it can't be traced.

    Accepts three legitimate wiring shapes:
      - literal string (e.g. "file1")
      - `=js:"file1"` — literal inside expression
      - `=js:$vars.<var>` — variable binding; matches if the global's default
        resolves to "file1" OR the variable name itself contains "file1" /
        "fieldname" (agent may leave the default null for runtime input)."""
    if not isinstance(value, str):
        return None
    if not value.startswith("=js:"):
        return value
    m = re.fullmatch(r"""=js:\s*["'](.+?)["']\s*""", value)
    if m:
        return m.group(1)
    m = re.fullmatch(r"=js:\s*\$vars\.(\w+)\s*", value)
    if m:
        var = m.group(1)
        g = globals_by_id.get(var, {})
        default = g.get("default")
        if default == FIELD:
            return FIELD
        # Runtime-input global — no default set. Accept if the variable
        # name signals the field-name role.
        low = var.lower()
        if FIELD.lower() in low or "fieldname" in low:
            return FIELD
    return None


def main() -> int:
    for path in glob.glob("**/*.flow", recursive=True):
        with open(path) as f:
            doc = json.load(f)
        globals_by_id = {g["id"]: g for g in
                         (doc.get("variables", {}).get("globals") or [])}
        seen = {}
        for n in doc.get("nodes", []):
            t = n.get("type", "")
            detail = n.get("inputs", {}).get("detail", {})
            pp = detail.get("pathParameters") or {}
            body = detail.get("bodyParameters") or {}
            if pp.get("entityName") != ENTITY:
                continue
            for suffix in REQUIRED:
                if t.endswith(suffix):
                    seen[suffix] = body.get("_fieldName")
        if not REQUIRED.issubset(seen.keys()):
            continue
        resolved = {s: resolve_field(v, globals_by_id) for s, v in seen.items()}
        wrong = [(s, seen[s], resolved[s]) for s in REQUIRED if resolved[s] != FIELD]
        if wrong:
            print(f"FAIL: {path} — {[(s, raw, res) for s, raw, res in wrong]} do not resolve to _fieldName={FIELD!r}", file=sys.stderr)
            return 1
        print(f"OK: {path} — 3 file activities on {ENTITY}/{FIELD} (raw values: {seen})")
        return 0
    print(f"FAIL: no .flow has all 3 file activities on {ENTITY}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
