#!/usr/bin/env python3
"""Shape check for the coded Integration Service smoke task.

Verifies the invariants the capability doc teaches, AST-linked to the actual
`invoke_activity(_async)` call so dead-code / unused literals cannot satisfy it:

  1. `bindings.json` carries a `connection` resource with the Connection
     Service envelope (capital-C `ConnectionId`,
     `metadata.UseConnectionService == "True"`).
  2. `main.py` actually calls `sdk.connections.invoke_activity(_async)` and
     resolves the connection by binding key — either an explicit
     `retrieve(<key>)` / `retrieve_async(<key>)` or a one-shot
     `invoke_activity(connection_id="<key>")` (both documented).
  3. The `ActivityMetadata` passed to that call (inline OR a resolved
     module/function constant) maps the describe fixture: `object_path`,
     `method_name`, `query_params`, and `body_fields` (deduped requestField
     first-segments). Param info may be an inline
     `ActivityParameterLocationInfo(...)`, a named constant, or a dict; lists
     and tuples both accepted.
  4. `main.py` does NOT instantiate `UiPath` at module level (anti-pattern #6),
     alias-aware, and constructs it somewhere.
  5. No lowcode-only `resources/<Tool>/resource.json` sidecar.
  6. `__uipath/uipath.json` resourceOverwrites carries non-empty `connectionId`
     and `folderKey` (alias `ConnectionId`) for `connection.<key>`;
     `ConnectionResourceOverwrite` (`uipath/platform/common/_bindings.py:100`)
     defines only those two with `extra="ignore"`, so an `elementInstanceId`
     entry is rejected here as a skill-hygiene anti-pattern (#1) — the SDK would
     silently drop it.

Exits 0 on PASS, with `FAIL: ...` on the first violation.
"""

from __future__ import annotations

import ast
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.bindings_assertions import (  # noqa: E402
    assert_metadata_field,
    assert_value_field,
    find_resource,
    load_bindings,
)
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("slack-notifier")
BINDING_KEY = "slack-notifier"


def _read(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


# --------------------------------------------------------------------------
# AST helpers
# --------------------------------------------------------------------------

def _parse_main() -> ast.Module:
    path = ROOT / "main.py"
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as e:
        sys.exit(f"FAIL: main.py is not valid Python: {e}")


def _import_aliases(tree: ast.Module) -> dict[str, str]:
    """Map each locally-bound name → canonical imported symbol (handles `as`)."""
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for a in node.names:
                local = a.asname or a.name
                aliases[local.split(".")[0]] = a.name.split(".")[-1]
    return aliases


def _assignments(tree: ast.Module) -> dict[str, ast.AST]:
    """name → assigned value node (covers module and function scope; last wins)."""
    out: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.value is not None:
                out[node.target.id] = node.value
    return out


def _resolves_to(call: ast.Call, target: str, aliases: dict[str, str]) -> bool:
    fn = call.func
    if isinstance(fn, ast.Attribute):
        return fn.attr == target
    if isinstance(fn, ast.Name):
        return aliases.get(fn.id, fn.id) == target
    return False


def _attr_name(call: ast.Call) -> str | None:
    fn = call.func
    if isinstance(fn, ast.Attribute):
        return fn.attr
    if isinstance(fn, ast.Name):
        return fn.id
    return None


def _str_seq(node: ast.AST | None) -> list[str] | None:
    """A list/tuple of string constants → [str]; else None."""
    if not isinstance(node, (ast.List, ast.Tuple)):
        return None
    out: list[str] = []
    for el in node.elts:
        if isinstance(el, ast.Constant) and isinstance(el.value, str):
            out.append(el.value)
        else:
            return None
    return out


def _deref(node: ast.AST | None, assigns: dict[str, ast.AST]) -> ast.AST | None:
    """If node is a Name bound to a value, return that value; else node itself."""
    if isinstance(node, ast.Name) and node.id in assigns:
        return assigns[node.id]
    return node


def _kw_or_pos(call: ast.Call, name: str, pos: int) -> ast.AST | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    if pos < len(call.args):
        return call.args[pos]
    return None


# --------------------------------------------------------------------------
# Checks
# --------------------------------------------------------------------------

def check_bindings_connection() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="connection", key=BINDING_KEY)
    assert_value_field(entry, field="ConnectionId", expected=BINDING_KEY)
    assert_metadata_field(entry, field="UseConnectionService", expected="True")
    print("OK: bindings.json connection envelope is well-formed")


def check_no_lowcode_sidecar() -> None:
    bad = list(ROOT.glob("resources/**/resource.json"))
    if bad:
        sys.exit(
            "FAIL: found lowcode-only `resources/<Tool>/resource.json` sidecar(s) "
            "in a coded agent — coded agents inline ActivityMetadata in .py "
            f"(see capability § Coded vs Low-code): {bad}"
        )
    print("OK: no lowcode `resources/<Tool>/resource.json` sidecar present")


def check_lazy_sdk_init(tree: ast.Module, aliases: dict[str, str]) -> None:
    violations = find_module_level_llm_clients(ROOT / "main.py")
    if violations:
        sys.exit(
            "FAIL: module-level UiPath* construction detected (anti-pattern #6): "
            + " | ".join(violations)
        )
    constructed = any(
        isinstance(n, ast.Call) and _resolves_to(n, "UiPath", aliases)
        for n in ast.walk(tree)
    )
    if not constructed:
        sys.exit(
            "FAIL: main.py never constructs `UiPath()` (alias-aware) — the agent "
            "cannot have called `sdk.connections.invoke_activity`."
        )
    print("OK: main.py constructs UiPath() lazily (not at module scope)")


def _find_invoke_call(tree: ast.Module) -> ast.Call:
    invokes = [
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and _attr_name(n) in ("invoke_activity", "invoke_activity_async")
        and isinstance(n.func, ast.Attribute)  # must be sdk.connections.invoke_*
    ]
    if not invokes:
        sys.exit(
            "FAIL: main.py has no executable `sdk.connections.invoke_activity"
            "(_async)` call — the capability's runtime pattern is missing "
            "(substrings in comments/strings do not count)."
        )
    return invokes[0]


def _binding_key_resolves(
    invoke: ast.Call, tree: ast.Module, assigns: dict[str, ast.AST]
) -> bool:
    """The connection must be resolved by the binding key — either the
    one-shot `connection_id="<key>"` or an explicit retrieve(<key>)."""
    conn = _deref(_kw_or_pos(invoke, "connection_id", 1), assigns)
    if isinstance(conn, ast.Constant) and conn.value == BINDING_KEY:
        return True
    for c in ast.walk(tree):
        if isinstance(c, ast.Call) and _attr_name(c) in ("retrieve", "retrieve_async"):
            first = _deref(_kw_or_pos(c, "key", 0), assigns)
            if isinstance(first, ast.Constant) and first.value == BINDING_KEY:
                return True
    return False


def _resolve_metadata_call(
    node: ast.AST | None, assigns: dict[str, ast.AST], aliases: dict[str, str]
) -> ast.Call | None:
    node = _deref(node, assigns)
    if isinstance(node, ast.Call) and _resolves_to(node, "ActivityMetadata", aliases):
        return node
    return None


def _resolve_param_info(
    node: ast.AST | None, assigns: dict[str, ast.AST], aliases: dict[str, str]
) -> dict[str, list[str]] | None:
    node = _deref(node, assigns)
    kw: dict[str, ast.AST] = {}
    if isinstance(node, ast.Call) and _resolves_to(
        node, "ActivityParameterLocationInfo", aliases
    ):
        kw = {k.arg: k.value for k in node.keywords if k.arg}
    elif isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                kw[k.value] = v
    else:
        return None
    body = _str_seq(kw.get("body_fields"))
    if body is None:
        return None
    query = _str_seq(kw.get("query_params")) if "query_params" in kw else []
    if query is None:
        return None
    return {"body_fields": body, "query_params": query}


def _expected_from_fixture() -> dict:
    """Derive the ActivityMetadata shape the agent should have mapped from the
    pre-recorded `uip is resources describe` fixture (staged in the task dir)."""
    fixture = Path(__file__).resolve().parent / "fixtures" / "slack_send_message_describe.json"
    doc = _load_json(fixture)
    body_fields: list[str] = []
    for f in doc.get("requestFields", []):
        first = f["name"].split(".", 1)[0]
        if first not in body_fields:
            body_fields.append(first)
    return {
        "object_path": doc["operation"]["path"],
        "method": doc["operation"]["method"],
        "query_params": [
            p["name"] for p in doc.get("parameters", []) if p.get("type") == "query"
        ],
        "body_fields": body_fields,
    }


def check_invocation_and_metadata(
    tree: ast.Module, assigns: dict[str, ast.AST], aliases: dict[str, str]
) -> None:
    invoke = _find_invoke_call(tree)

    if not _binding_key_resolves(invoke, tree, assigns):
        sys.exit(
            f"FAIL: the invoke_activity call does not resolve connection by the "
            f"binding key {BINDING_KEY!r} — pass `connection_id=\"{BINDING_KEY}\"` "
            f"or `retrieve(\"{BINDING_KEY}\")` (do NOT hardcode a raw connection UUID)."
        )
    print("OK: main.py invokes invoke_activity and resolves the binding key")

    meta_arg = _kw_or_pos(invoke, "activity_metadata", 0)
    meta = _resolve_metadata_call(meta_arg, assigns, aliases)
    if meta is None:
        sys.exit(
            "FAIL: the `activity_metadata=` argument of invoke_activity is not an "
            "`ActivityMetadata(...)` literal (inline or a resolvable constant). The "
            "SDK builds the request from the object actually passed — keep it a "
            "literal so the shape is verifiable."
        )

    kw = {k.arg: k.value for k in meta.keywords if k.arg}
    # positional fallback: ActivityMetadata(object_path, method_name, content_type, parameter_location_info)
    pos_names = ["object_path", "method_name", "content_type", "parameter_location_info"]
    for i, a in enumerate(meta.args):
        if i < len(pos_names) and pos_names[i] not in kw:
            kw[pos_names[i]] = a

    object_path = kw.get("object_path")
    method_name = kw.get("method_name")
    if not (isinstance(object_path, ast.Constant) and isinstance(object_path.value, str)):
        sys.exit("FAIL: ActivityMetadata.object_path is not a string literal.")
    if not (isinstance(method_name, ast.Constant) and isinstance(method_name.value, str)):
        sys.exit("FAIL: ActivityMetadata.method_name is not a string literal.")

    pinfo = _resolve_param_info(kw.get("parameter_location_info"), assigns, aliases)
    if pinfo is None:
        sys.exit(
            "FAIL: could not resolve `parameter_location_info` to query_params/"
            "body_fields (accepts inline ActivityParameterLocationInfo(...), a named "
            "constant, or a dict; list or tuple values)."
        )

    expected = _expected_from_fixture()
    if object_path.value != expected["object_path"]:
        sys.exit(
            f"FAIL: object_path={object_path.value!r} != describe fixture "
            f"operation.path={expected['object_path']!r} — map it from the fixture."
        )
    if str(method_name.value).upper() != expected["method"].upper():
        sys.exit(
            f"FAIL: method_name={method_name.value!r} != fixture "
            f"operation.method={expected['method']!r}."
        )
    if set(pinfo["body_fields"]) != set(expected["body_fields"]):
        miss = sorted(set(expected["body_fields"]) - set(pinfo["body_fields"]))
        extra = sorted(set(pinfo["body_fields"]) - set(expected["body_fields"]))
        sys.exit(
            "FAIL: body_fields do not match the fixture's deduped requestField "
            f"first-segments. missing={miss} extra={extra} (Body-Field Reframing)."
        )
    if set(pinfo["query_params"]) != set(expected["query_params"]):
        sys.exit(
            f"FAIL: query_params={sorted(pinfo['query_params'])} != fixture "
            f"query parameters={sorted(expected['query_params'])}."
        )
    print(
        "OK: ActivityMetadata passed to invoke_activity is mapped from the describe "
        "fixture (object_path/method/body_fields/query_params)"
    )


def check_resource_overwrites() -> None:
    path = ROOT / "__uipath" / "uipath.json"
    if not path.is_file():
        sys.exit(
            "FAIL: missing __uipath/uipath.json — the local-runtime binding "
            "recipe requires resourceOverwrites to live here "
            "(cli_run.py reads runtime_dir/uipath.json at local run)."
        )
    doc = _load_json(path)
    overwrites = (
        doc.get("runtime", {})
        .get("internalArguments", {})
        .get("resourceOverwrites", {})
    )
    key = f"connection.{BINDING_KEY}"
    if key not in overwrites:
        sys.exit(
            f"FAIL: resourceOverwrites is missing key `{key}` (must match "
            "the bindings.json connection resource key exactly)."
        )
    entry = overwrites[key]
    if not isinstance(entry, dict):
        sys.exit(f"FAIL: resourceOverwrites[`{key}`] is not an object.")

    conn_id = entry.get("connectionId", entry.get("ConnectionId"))
    folder_key = entry.get("folderKey")
    # Non-empty strings: `ResourceOverwriteParser.parse` would reject null/empty
    # and the override is silently skipped (`_common.py:217-225`).
    for field, val in (("connectionId (or ConnectionId)", conn_id), ("folderKey", folder_key)):
        if not (isinstance(val, str) and val.strip()):
            sys.exit(
                f"FAIL: resourceOverwrites for `{key}` field {field} must be a "
                f"non-empty string (got {val!r}); the SDK skips invalid overrides "
                "and the binding key 400s at local run."
            )
    if "elementInstanceId" in entry:
        sys.exit(
            f"FAIL: resourceOverwrites for `{key}` contains `elementInstanceId`. "
            "`ConnectionResourceOverwrite` has `extra=\"ignore\"` and silently "
            "drops it (capability anti-pattern #1). Remove it; `element_instance_id` "
            "is exposed on the live `Connection.element_instance_id` after retrieve()."
        )
    print("OK: resourceOverwrites carries non-empty connectionId + folderKey, no elementInstanceId")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    tree = _parse_main()
    aliases = _import_aliases(tree)
    assigns = _assignments(tree)

    check_bindings_connection()
    check_no_lowcode_sidecar()
    check_lazy_sdk_init(tree, aliases)
    check_invocation_and_metadata(tree, assigns, aliases)
    check_resource_overwrites()
    print("PASS: coded IS smoke shape checks complete")


if __name__ == "__main__":
    main()
