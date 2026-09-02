#!/usr/bin/env python3
"""Verify Upload + Download + Delete file-record-field nodes exist on
FlowCodeEvalEntity, each with a _fieldName that resolves to "file1", and
that upload's multipart file input carries a non-empty variable binding
(any `=js:$vars.<var>...` expression — download output, typed file global,
or start-input file parameter all pass).

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
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
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
        delete_node = None
        create_node = None
        # Connector nodes that carry no `inputs.detail` at all. The platform reads
        # a connector's entity/body/connection from `detail`, so such a node can
        # never run — it is an unconfigured node (SDK `rawNode`, a hand-written
        # node, or `node add` without `node configure`), not a missing one.
        # Naming it keeps "no create-entity-record" from being read as "the
        # agent forgot the step" (2026-09-01 v2: the step was there, raw).
        unconfigured = []
        for n in doc.get("nodes", []):
            t = n.get("type", "")
            detail = n.get("inputs", {}).get("detail", {})
            if t.startswith("uipath.connector.") and (not isinstance(detail, dict) or not detail):
                unconfigured.append(f"{n.get('id')} ({t.rsplit('.', 1)[-1]})")
                detail = {}
            pp = detail.get("pathParameters") or {}
            query = detail.get("queryParameters") or {}
            body = detail.get("bodyParameters") or {}
            if resolve_entity(pp.get("entityName"), globals_by_id) != ENTITY:
                continue
            if t.endswith(".create-entity-record") and not create_node:
                create_node = n
            for suffix in REQUIRED:
                if t.endswith(suffix):
                    seen[suffix] = query.get("_fieldName") or body.get("_fieldName")
                    if suffix == ".download-file-from-record-field":
                        download_node = n
                    elif suffix == ".upload-file-to-record-field":
                        upload_node = n
                    elif suffix == ".delete-file-from-record-field":
                        delete_node = n
        if not REQUIRED.issubset(seen.keys()):
            continue
        unconfigured_note = (
            f" Unconfigured connector node(s) with no inputs.detail: {unconfigured} — "
            f"the platform reads entity, body and connection from detail, so these can never run."
            if unconfigured else ""
        )
        resolved = {s: resolve_field(v, globals_by_id) for s, v in seen.items()}
        wrong = [(s, seen[s], resolved[s]) for s in REQUIRED if resolved[s] != FIELD]
        if wrong:
            print(f"FAIL: {path} — {[(s, raw, res) for s, raw, res in wrong]} do not resolve to _fieldName={FIELD!r}", file=sys.stderr)
            return 1
        # Upload's multipart file must carry a variable binding (any =js:$vars
        # expression — download output, typed file global, or start-input file
        # parameter all pass). Roundtrip wiring is not enforced at smoke tier.
        multipart = (upload_node.get("inputs", {}).get("detail", {}) or {}).get("multipartParameters") or []
        upload_file_values = [str(p.get("value", "")) for p in multipart if p.get("name") == "file"]
        if not any(re.match(r"=js:\s*\$vars\.\w+", v) for v in upload_file_values):
            print(f"FAIL: {path} — upload multipart file has no =js:$vars.* variable binding. "
                  f"upload file values: {upload_file_values}", file=sys.stderr)
            return 1

        # Download's recordId is a concrete UUID so either authoring path can
        # choose its own neutral fixture value.
        dl_recid = (download_node.get("inputs", {}).get("detail", {}).get("queryParameters") or {}).get("recordId", "")
        if not UUID_RE.fullmatch(str(dl_recid)):
            print(f"FAIL: {path} — download recordId is not a UUID literal: {dl_recid!r}", file=sys.stderr)
            return 1

        # create-entity-record on ENTITY must exist and upload+delete recordId must reference its output
        if not create_node:
            print(f"FAIL: {path} — no create-entity-record on {ENTITY} with inputs.detail.pathParameters.entityName={ENTITY!r}.{unconfigured_note}", file=sys.stderr)
            return 1
        create_body = (create_node.get("inputs", {}).get("detail", {}).get("bodyParameters") or {})
        required_body = {"title", "description", "score"}
        missing = required_body - set(create_body.keys())
        if missing:
            print(f"FAIL: {path} — create body missing required fields: {sorted(missing)}", file=sys.stderr)
            return 1
        create_id = create_node.get("id", "")

        def refs_create_output(rid_expr: str) -> bool:
            if create_id and create_id in str(rid_expr):
                return True
            m = re.fullmatch(r"=js:\s*\$vars\.(\w+)\s*", str(rid_expr))
            if m:
                var = m.group(1)
                for entries in variable_updates.values():
                    for item in entries:
                        if item.get("variableId") == var and create_id in str(item.get("expression", "")):
                            return True
            return False

        for label, node_ref in [("upload", upload_node), ("delete", delete_node)]:
            rid = (node_ref.get("inputs", {}).get("detail", {}).get("queryParameters") or {}).get("recordId", "")
            if not refs_create_output(rid):
                print(f"FAIL: {path} — {label} recordId {rid!r} does not reference create output ({create_id})", file=sys.stderr)
                return 1

        print(f"OK: {path} — download(valid UUID) + create + upload/delete(recId=create.out) on {ENTITY}/{FIELD}; upload has variable binding")
        return 0
    print(f"FAIL: no .flow has all 3 file activities on {ENTITY}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
