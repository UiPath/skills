"""AST assertions for coded-agent guardrails that inspect files (``detection_scope``).

Each ``require_*`` helper exits with ``FAIL: ...`` on a failed assertion and
prints one ``OK: ...`` line when it passes.
"""

from __future__ import annotations

import ast
import sys

DETECTION_SCOPE_VALUES = ("Text", "Files", "Both")
_MEMBER_TO_VALUE = {"TEXT": "Text", "FILES": "Files", "BOTH": "Both"}
_REFERENCE_KEY_SETS = ({"ID", "FullName", "MimeType"}, {"id", "full_name", "mime_type"})
RENDER = "render_attachments_block"


def imported_from(tree: ast.AST, module: str, symbol: str) -> bool:
    """True when ``symbol`` is imported from ``module`` (or a submodule), or ``module`` itself is imported."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(module):
            if any(alias.name == symbol for alias in node.names):
                return True
        if isinstance(node, ast.Import) and any(alias.name.startswith(module) for alias in node.names):
            return True
    return False


def module_constants(tree: ast.AST) -> dict[str, ast.expr]:
    """Module-level ``NAME = <expr>`` bindings, so a scope held in a constant resolves."""
    consts: dict[str, ast.expr] = {}
    body = tree.body if isinstance(tree, ast.Module) else []
    for node in body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    consts[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            consts[node.target.id] = node.value
    return consts


def detection_scope_value(node: ast.expr | None, consts: dict[str, ast.expr]) -> str | None:
    """Resolve a ``detection_scope=`` value to its wire string, or ``None`` when absent.

    Accepts ``DetectionScope.FILES``, ``"Files"``, ``DetectionScope("Files")``, or a
    module constant bound to one of them. Anything else is returned as written so
    the caller can report it (a lowercase ``"files"``, ``GuardrailExecutionStage.FILES``).
    """
    seen = 0
    while isinstance(node, ast.Name) and node.id in consts and seen < 5:
        node = consts[node.id]
        seen += 1
    if node is None:
        return None
    if isinstance(node, ast.Attribute) and node.attr in _MEMBER_TO_VALUE and _names_detection_scope(node.value):
        return _MEMBER_TO_VALUE[node.attr]
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if (
        isinstance(node, ast.Call)
        and _names_detection_scope(node.func)
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and isinstance(node.args[0].value, str)
    ):
        return node.args[0].value
    return ast.unparse(node)


def wired_middleware_calls(tree: ast.AST) -> list[ast.Call]:
    """Middleware calls spread into a ``create_agent(middleware=[...])`` list, inline or through variables."""
    assigned: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned[target.id] = node.value

    def deref(node: ast.expr | None) -> ast.expr | None:
        seen = 0
        while isinstance(node, ast.Name) and node.id in assigned and seen < 5:
            node = assigned[node.id]
            seen += 1
        return node

    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute))):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else node.func.attr
        if name != "create_agent":
            continue
        listing = deref(next((kw.value for kw in node.keywords if kw.arg == "middleware"), None))
        if not isinstance(listing, (ast.List, ast.Tuple)):
            continue
        for elt in listing.elts:
            target = deref(elt.value) if isinstance(elt, ast.Starred) else None
            if isinstance(target, ast.Call):
                calls.append(target)
    return calls


def _names_detection_scope(node: ast.expr) -> bool:
    return (isinstance(node, ast.Name) and node.id == "DetectionScope") or (
        isinstance(node, ast.Attribute) and node.attr == "DetectionScope"
    )


def _annotation_mentions_attachment(annotation: ast.expr | None) -> bool:
    if annotation is None:
        return False
    for sub in ast.walk(annotation):
        if isinstance(sub, ast.Name) and sub.id == "Attachment":
            return True
        if isinstance(sub, ast.Attribute) and sub.attr == "Attachment":
            return True
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and "Attachment" in sub.value:
            return True
    return False


def attachment_fields(tree: ast.AST) -> list[str]:
    """Fields annotated with ``Attachment`` (optional or not) on the input model (``Input`` or ``*Input``)."""
    return [
        stmt.target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name.endswith("Input")
        for stmt in node.body
        if isinstance(stmt, ast.AnnAssign)
        and isinstance(stmt.target, ast.Name)
        and _annotation_mentions_attachment(stmt.annotation)
    ]


def require_attachment_input(tree: ast.AST) -> None:
    fields = attachment_fields(tree)
    if not fields:
        sys.exit(
            "FAIL: the Input model declares no Attachment field for the uploaded file "
            "(from uipath.platform.attachments import Attachment)"
        )
    if not imported_from(tree, "uipath.platform.attachments", "Attachment"):
        sys.exit("FAIL: Attachment must be imported from uipath.platform.attachments")
    print(f"OK: Input declares Attachment field(s): {fields}")


def _is_render_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and (
        (isinstance(node.func, ast.Name) and node.func.id == RENDER)
        or (isinstance(node.func, ast.Attribute) and node.func.attr == RENDER)
    )


def _assigned_values(fn: ast.AST, name: str) -> list[ast.expr]:
    values: list[ast.expr] = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            values.append(node.value)
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                values.append(node.value)
    return values


def _resolve(expr: ast.expr, fn: ast.AST) -> list[ast.expr]:
    if isinstance(expr, ast.Name):
        return _assigned_values(fn, expr.id) or [expr]
    return [expr]


def _names_field(expr: ast.AST, fn: ast.AST, fields: list[str], seen: frozenset[str] = frozenset()) -> bool:
    """True when ``expr`` reads an input Attachment field, directly or through local names."""
    for sub in ast.walk(expr):
        if isinstance(sub, ast.Attribute) and sub.attr in fields:
            return True
        if isinstance(sub, ast.Name) and sub.id not in seen:
            if any(_names_field(v, fn, fields, seen | {sub.id}) for v in _assigned_values(fn, sub.id)):
                return True
    return False


def _is_json_model_dump(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "model_dump"
        and any(kw.arg == "mode" and isinstance(kw.value, ast.Constant) and kw.value.value == "json" for kw in node.keywords)
    )


def _valid_reference(expr: ast.expr, fn: ast.AST, fields: list[str]) -> bool:
    """A job-attachment reference built from the input's Attachment field."""
    for value in _resolve(expr, fn):
        if _is_json_model_dump(value) and _names_field(value.func.value, fn, fields):
            return True
        if isinstance(value, ast.Dict):
            keys = {k.value for k in value.keys if isinstance(k, ast.Constant)}
            if any(keys >= required for required in _REFERENCE_KEY_SETS) and _names_field(value, fn, fields):
                return True
    return False


def _valid_render_argument(call: ast.Call, fn: ast.AST, fields: list[str]) -> bool:
    arg = call.args[0] if call.args else next((kw.value for kw in call.keywords if kw.arg == "attachments"), None)
    if arg is None:
        return False
    for value in _resolve(arg, fn):
        if isinstance(value, ast.List) and value.elts and all(_valid_reference(e, fn, fields) for e in value.elts):
            return True
        if (
            isinstance(value, ast.ListComp)
            and _is_json_model_dump(value.elt)
            and any(_names_field(gen.iter, fn, fields) for gen in value.generators)
        ):
            return True
    return False


def _is_message_sink(node: ast.AST) -> list[ast.AST]:
    """The parts of ``node`` that become user-message content, if ``node`` builds a user message."""
    if isinstance(node, ast.Call) and (
        (isinstance(node.func, ast.Name) and node.func.id == "HumanMessage")
        or (isinstance(node.func, ast.Attribute) and node.func.attr == "HumanMessage")
    ):
        return [*node.args, *(kw.value for kw in node.keywords)]
    if isinstance(node, ast.Dict):
        return [v for k, v in zip(node.keys, node.values) if isinstance(k, ast.Constant) and k.value == "content"]
    if isinstance(node, ast.Tuple) and len(node.elts) == 2:
        role = node.elts[0]
        if isinstance(role, ast.Constant) and role.value in ("user", "human"):
            return [node.elts[1]]
    return []


def _contains(expr: ast.AST, tainted: set[str], render_calls: set[int], tainted_funcs: set[str]) -> bool:
    for sub in ast.walk(expr):
        if id(sub) in render_calls:
            return True
        if isinstance(sub, ast.Name) and sub.id in tainted:
            return True
        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) and sub.func.id in tainted_funcs:
            return True
    return False


def _functions(tree: ast.AST) -> list[ast.AST]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))] or [tree]


def _taint(fn: ast.AST, render_calls: set[int], tainted_funcs: set[str]) -> set[str]:
    tainted: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in ast.walk(fn):
            targets: list[ast.expr] = []
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, (ast.AnnAssign, ast.AugAssign)) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            if _contains(value, tainted, render_calls, tainted_funcs):
                for target in targets:
                    if isinstance(target, ast.Name) and target.id not in tainted:
                        tainted.add(target.id)
                        changed = True
    return tainted


def require_rendered_attachments(tree: ast.AST) -> None:
    fields = attachment_fields(tree)
    renders = [(fn, node) for fn in _functions(tree) for node in ast.walk(fn) if _is_render_call(node)]
    if not renders:
        sys.exit(
            "FAIL: the uploaded file is never rendered into the user message — "
            "call render_attachments_block(...) so the guardrails can see it"
        )
    valid = [(fn, call) for fn, call in renders if _valid_render_argument(call, fn, fields)]
    if not valid:
        got = ", ".join(ast.unparse(call)[:120] for _, call in renders)
        sys.exit(
            "FAIL: render_attachments_block must receive the input's Attachment as "
            "<state>.<field>.model_dump(mode=\"json\", exclude_none=True) (or an "
            "{\"ID\", \"FullName\", \"MimeType\"} dict built from it); any other shape never reaches "
            f"the guardrails. Got: {got}"
        )
    render_calls = {id(call) for _, call in valid}
    tainted_funcs: set[str] = set()
    for _ in range(3):
        for fn in _functions(tree):
            tainted = _taint(fn, render_calls, tainted_funcs)
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                isinstance(n, ast.Return) and n.value is not None and _contains(n.value, tainted, render_calls, tainted_funcs)
                for n in ast.walk(fn)
            ):
                tainted_funcs.add(fn.name)
    for fn in _functions(tree):
        tainted = _taint(fn, render_calls, tainted_funcs)
        for node in ast.walk(fn):
            if any(_contains(part, tainted, render_calls, tainted_funcs) for part in _is_message_sink(node)):
                print("OK: render_attachments_block(...) puts the file into the user message")
                return
    sys.exit(
        "FAIL: the render_attachments_block(...) result never reaches the user message — "
        "put it in the HumanMessage content"
    )


def require_detection_scope(call: ast.Call, expected: str, consts: dict[str, ast.expr], reason: str) -> None:
    node = next((kw.value for kw in call.keywords if kw.arg == "detection_scope"), None)
    value = detection_scope_value(node, consts)
    if value is None:
        sys.exit(f"FAIL: detection_scope= is missing on {ast.unparse(call.func)}(...) — without it no file is inspected")
    if value not in DETECTION_SCOPE_VALUES:
        sys.exit(
            f"FAIL: detection_scope must be DetectionScope.TEXT/FILES/BOTH or exactly "
            f"{', '.join(DETECTION_SCOPE_VALUES)}; got {value!r}"
        )
    if value != expected:
        sys.exit(f"FAIL: {reason}: detection_scope must be {expected!r}, got {value!r}")
    print(f"OK: detection_scope == {expected!r} on {ast.unparse(call.func)}(...)")
