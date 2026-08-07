#!/usr/bin/env python3
"""Verify Upload + Download + Delete file-record-field nodes exist on
FlowCodeEvalEntity, each with a _fieldName that resolves to "file1", and
that Download -> typed file variable -> Upload wiring is preserved.

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


def resolve_entity(value, globals_by_id) -> str | None:
    """Resolve entityName to the literal string it targets. Accepts a plain
    string OR a `=js:$vars.<var>` expression whose backing global has
    defaultValue == ENTITY."""
    if not isinstance(value, str):
        return None
    if not value.startswith("=js:"):
        return value
    m = re.fullmatch(r"""=js:\s*["'](.+?)["']\s*""", value)
    if m:
        return m.group(1)
    m = re.fullmatch(r"=js:\s*\$vars\.(\w+)\s*", value)
    if m:
        g = globals_by_id.get(m.group(1), {})
        if g.get("defaultValue", g.get("default")) == ENTITY:
            return ENTITY
    return None


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
        typed_file_ids = {g_id for g_id, g in globals_by_id.items()
                          if g.get("type") == "file"}
        variable_updates = doc.get("variables", {}).get("variableUpdates", {}) or {}
        seen = {}
        download_node = None
        upload_node = None
        for n in doc.get("nodes", []):
            t = n.get("type", "")
            detail = n.get("inputs", {}).get("detail", {})
            pp = detail.get("pathParameters") or {}
            body = detail.get("bodyParameters") or {}
            if resolve_entity(pp.get("entityName"), globals_by_id) != ENTITY:
                continue
            for suffix in REQUIRED:
                if t.endswith(suffix):
                    seen[suffix] = body.get("_fieldName")
                    if suffix == ".download-file-from-record-field":
                        download_node = n
                    elif suffix == ".upload-file-to-record-field":
                        upload_node = n
        if not REQUIRED.issubset(seen.keys()):
            continue
        resolved = {s: resolve_field(v, globals_by_id) for s, v in seen.items()}
        wrong = [(s, seen[s], resolved[s]) for s in REQUIRED if resolved[s] != FIELD]
        if wrong:
            print(f"FAIL: {path} — {[(s, raw, res) for s, raw, res in wrong]} do not resolve to _fieldName={FIELD!r}", file=sys.stderr)
            return 1
        if not typed_file_ids:
            print(f"FAIL: {path} — no workflow-level variable with type=file", file=sys.stderr)
            return 1
        download_id = download_node.get("id", "")
        assigned_ids = {
            item.get("variableId")
            for entries in variable_updates.values()
            for item in entries
            if download_id in str(item.get("expression", ""))
        }
        reused_ids = assigned_ids & typed_file_ids
        if not reused_ids:
            print(f"FAIL: {path} — download output is not assigned to a typed file variable", file=sys.stderr)
            return 1
        multipart = (upload_node.get("inputs", {}).get("detail", {}) or {}).get("multipartParameters") or []
        upload_values = [p.get("value") for p in multipart if p.get("name") == "file"]
        if not any(any(var in str(value) for var in typed_file_ids) for value in upload_values):
            print(f"FAIL: {path} — upload multipart file is not bound to any typed file variable: {upload_values} (typed file vars: {sorted(typed_file_ids)})", file=sys.stderr)
            return 1
        print(f"OK: {path} — 3 file activities on {ENTITY}/{FIELD}; typed file variable reused (raw values: {seen})")
        return 0
    print(f"FAIL: no .flow has all 3 file activities on {ENTITY}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
