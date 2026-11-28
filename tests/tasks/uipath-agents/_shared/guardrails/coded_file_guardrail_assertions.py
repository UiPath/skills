"""AST assertions for coded-agent guardrails that inspect files (``detection_scope``).

Each ``require_*`` helper exits with ``FAIL: ...`` on a failed assertion and
prints one ``OK: ...`` line when it passes. Names, arguments and enum values are
read the way Python and the UiPath SDK read them, so a check judges what the code
sends at runtime, not how it is spelled.
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Iterator
from dataclasses import dataclass

from _shared.guardrails.guardrail_middleware import call_name

# Copied from the UiPath SDK. The enums are str enums, and the SDK sends the value.
ENUMS: dict[str, dict[str, str]] = {
    "PIIDetectionEntityType": {
        "PERSON": "Person",
        "ADDRESS": "Address",
        "DATE": "Date",
        "PHONE_NUMBER": "PhoneNumber",
        "EUGPS_COORDINATES": "EugpsCoordinates",
        "EMAIL": "Email",
        "CREDIT_CARD_NUMBER": "CreditCardNumber",
        "INTERNATIONAL_BANKING_ACCOUNT_NUMBER": "InternationalBankingAccountNumber",
        "SWIFT_CODE": "SwiftCode",
        "ABA_ROUTING_NUMBER": "ABARoutingNumber",
        "US_DRIVERS_LICENSE_NUMBER": "USDriversLicenseNumber",
        "UK_DRIVERS_LICENSE_NUMBER": "UKDriversLicenseNumber",
        "US_INDIVIDUAL_TAXPAYER_IDENTIFICATION": "USIndividualTaxpayerIdentification",
        "UK_UNIQUE_TAXPAYER_NUMBER": "UKUniqueTaxpayerNumber",
        "US_BANK_ACCOUNT_NUMBER": "USBankAccountNumber",
        "US_SOCIAL_SECURITY_NUMBER": "USSocialSecurityNumber",
        "USUK_PASSPORT_NUMBER": "UsukPassportNumber",
        "URL": "URL",
        "IP_ADDRESS": "IPAddress",
    },
    "GuardrailScope": {"AGENT": "Agent", "LLM": "Llm", "TOOL": "Tool"},
    "GuardrailExecutionStage": {"PRE": "pre", "POST": "post", "PRE_AND_POST": "pre&post"},
    "DetectionScope": {"TEXT": "Text", "FILES": "Files", "BOTH": "Both"},
}
# The SDK parameter order of the calls whose arguments a check may find by position.
POSITIONAL_PARAMS: dict[str, tuple[str, ...]] = {
    "UiPathPIIDetectionMiddleware": ("scopes", "action", "entities"),
    "UiPathLLMAsJudgeMiddleware": ("scopes", "action", "guardrail_text", "model"),
    "LLMAsJudgeValidator": ("guardrail_text", "model"),
    "PIIDetectionEntity": ("name", "threshold"),
    "BlockAction": ("title", "detail"),
}
DETECTION_SCOPE_VALUES = tuple(ENUMS["DetectionScope"].values())
_REFERENCE_KEY_SETS = ({"ID", "FullName", "MimeType"}, {"id", "full_name", "mime_type"})
RENDER = "render_attachments_block"
_MAX_HOPS = 5


@dataclass(frozen=True)
class _Binding:
    """One binding of a name: an assigned ``value``, an ``imported`` name, or neither (a parameter, a loop target)."""

    line: int
    column: int
    value: ast.expr | None = None
    imported: str | None = None


class Bindings:
    """Where each name is bound, per scope, so a name resolves as Python resolves it where it is used."""

    def __init__(self, tree: ast.Module) -> None:
        self.tree = tree
        self._parent = {id(child): parent for parent in ast.walk(tree) for child in ast.iter_child_nodes(parent)}
        self._bound: dict[tuple[int, str], list[_Binding]] = {}
        self._added: dict[tuple[int, str], list[tuple[ast.expr, bool]]] = {}
        for node in ast.walk(tree):
            for scope, name, binding in self._bindings_of(node):
                self._bound.setdefault((id(scope), name), []).append(binding)
            for name, added, single in _list_updates(node):
                self._added.setdefault((id(self.scopes(node)[0]), name), []).append((added, single))
        for entries in self._bound.values():
            entries.sort(key=lambda binding: (binding.line, binding.column))

    def scopes(self, at: ast.AST) -> list[ast.AST]:
        """The scopes whose names ``at`` sees, innermost first. A class body is seen only from itself."""
        found: list[ast.AST] = []
        child, node = at, self._parent.get(id(at))
        while node is not None:
            if _in_body(node, child) and (not isinstance(node, ast.ClassDef) or not found):
                found.append(node)
            child, node = node, self._parent.get(id(node))
        return [*found, self.tree]

    def resolve(self, node: ast.expr | None) -> ast.expr | None:
        """Follow a name to the value assigned to it where it is used, up to five hops.

        A name bound by a parameter, a loop target or an import stays unresolved.
        """
        for _ in range(_MAX_HOPS):
            if not isinstance(node, ast.Name):
                break
            found = self._lookup(node.id, node)
            if found is None or found[1].value is None:
                break
            node = found[1].value
        return node

    def imported_name(self, node: ast.Name) -> str:
        """The original name behind ``node`` when it is a ``from m import x as y`` alias visible where it is used."""
        found = self._lookup(node.id, node)
        return found[1].imported if found and found[1].imported else node.id

    def added(self, node: ast.Name) -> list[tuple[ast.expr, bool]]:
        """What the code adds to the list ``node`` names, in its scope: ``(items, False)`` or ``(item, True)``."""
        found = self._lookup(node.id, node)
        return self._added.get((id(found[0]), node.id), []) if found else []

    def _lookup(self, name: str, at: ast.AST) -> tuple[ast.AST, _Binding] | None:
        line = getattr(at, "lineno", None)
        holding = self._ancestors(at)
        for depth, scope in enumerate(self.scopes(at)):
            entries = [b for b in self._bound.get((id(scope), name), []) if b.value is None or id(b.value) not in holding]
            if not entries:
                continue
            before = [b for b in entries if depth == 0 and line is not None and b.line <= line]
            return scope, (before or entries)[-1]
        return None

    def _ancestors(self, node: ast.AST | None) -> set[int]:
        found: set[int] = set()
        while node is not None:
            found.add(id(node))
            node = self._parent.get(id(node))
        return found

    def _bindings_of(self, node: ast.AST) -> Iterator[tuple[ast.AST, str, _Binding]]:
        """The names ``node`` binds, each with the scope it binds in."""
        if isinstance(node, ast.Module):
            return
        here = self.scopes(node)[0]
        at = (node.lineno, node.col_offset) if isinstance(node, (ast.stmt, ast.expr, ast.excepthandler)) else (0, 0)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            arguments = node.args
            for arg in (*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs, arguments.vararg, arguments.kwarg):
                if arg is not None:
                    yield node, arg.arg, _Binding(*at)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield here, node.name, _Binding(*at)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is not None:
                for target in targets:
                    for name, value in _paired(target, node.value):
                        yield here, name, _Binding(*at, value=value)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            yield from ((here, name, _Binding(*at)) for name in _target_names(node.target))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                yield from ((here, name, _Binding(*at)) for name in _target_names(item.optional_vars))
        elif isinstance(node, ast.ExceptHandler) and node.name:
            yield here, node.name, _Binding(*at)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield here, alias.asname or alias.name.split(".")[0], _Binding(*at)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    yield here, alias.asname or alias.name, _Binding(*at, imported=alias.name)


def _in_body(scope: ast.AST, child: ast.AST) -> bool:
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return any(child is stmt for stmt in scope.body)
    return isinstance(scope, ast.Lambda) and child is scope.body


def _target_names(target: ast.expr | None) -> list[str]:
    return [n.id for n in ast.walk(target) if isinstance(n, ast.Name)] if target is not None else []


def _paired(target: ast.expr, value: ast.expr) -> Iterator[tuple[str, ast.expr | None]]:
    """Each name ``target`` binds, with the value it gets, or ``None`` when unpacking hides it."""
    if isinstance(target, ast.Name):
        yield target.id, value
    elif (
        isinstance(target, (ast.Tuple, ast.List))
        and isinstance(value, (ast.Tuple, ast.List))
        and len(target.elts) == len(value.elts)
    ):
        for sub_target, sub_value in zip(target.elts, value.elts, strict=True):
            yield from _paired(sub_target, sub_value)
    else:
        yield from ((name, None) for name in _target_names(target))


def _list_updates(node: ast.AST) -> Iterator[tuple[str, ast.expr, bool]]:
    """``(name, added, single)`` for ``name += [...]``, ``name.extend(xs)`` (items) and ``name.append(x)`` /
    ``name.insert(i, x)`` (one item)."""
    if isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add) and isinstance(node.target, ast.Name):
        yield node.target.id, node.value, False
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.args
    ):
        if node.func.attr in ("append", "insert"):
            yield node.func.value.id, node.args[-1], True
        elif node.func.attr == "extend":
            yield node.func.value.id, node.args[0], False


def call_arg(call: ast.expr | None, name: str) -> ast.expr | None:
    """The argument ``name`` of ``call``, by keyword or by its SDK position (``POSITIONAL_PARAMS``)."""
    if not isinstance(call, ast.Call):
        return None
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    params = POSITIONAL_PARAMS.get(call_name(call) or "", ())
    if name not in params:
        return None
    index = params.index(name)
    leading = call.args[: index + 1]
    if len(leading) <= index or any(isinstance(arg, ast.Starred) for arg in leading):
        return None
    return call.args[index]


def elements(node: ast.expr | None, bindings: Bindings, depth: int = 0) -> Iterator[ast.expr]:
    """The items of a list, tuple or set argument: names resolved, ``*`` and ``+`` followed, and the items
    the code adds to a named list with ``+=``, ``.append``, ``.insert`` or ``.extend``."""
    if node is None or depth > _MAX_HOPS:
        return
    if isinstance(node, ast.Name):
        for added, single in bindings.added(node):
            if not single:
                yield from elements(added, bindings, depth + 1)
            elif (item := bindings.resolve(added)) is not None:
                yield item
    node = bindings.resolve(node)
    if node is None:
        return
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for item in node.elts:
            yield from elements(item.value if isinstance(item, ast.Starred) else item, bindings, depth + 1)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        yield from elements(node.left, bindings, depth + 1)
        yield from elements(node.right, bindings, depth + 1)
    else:
        yield node


def names_enum(node: ast.expr | None, enum: str, bindings: Bindings) -> bool:
    """True when ``node`` is the SDK enum class ``enum``: its name, an import alias, or ``module.enum``."""
    node = bindings.resolve(node)
    if isinstance(node, ast.Name):
        return bindings.imported_name(node) == enum
    return isinstance(node, ast.Attribute) and node.attr == enum


def enum_value(node: ast.expr | None, enum: str, bindings: Bindings) -> str | None:
    """The value ``node`` passes for an SDK ``enum`` parameter: ``Enum.MEMBER``, ``"value"`` or ``Enum("value")``."""
    node = bindings.resolve(node)
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Attribute) and names_enum(node.value, enum, bindings):
        return ENUMS[enum].get(node.attr)
    if isinstance(node, ast.Call) and names_enum(node.func, enum, bindings) and len(node.args) == 1:
        arg = bindings.resolve(node.args[0])
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            return arg.value
    return None


def enum_values(node: ast.expr | None, enum: str, bindings: Bindings) -> set[str]:
    """The values a list argument passes for an SDK ``enum`` (for example ``scopes=``)."""
    return {value for item in elements(node, bindings) if (value := enum_value(item, enum, bindings)) is not None}


def named_enum_values(node: ast.expr | None, enum: str, bindings: Bindings, depth: int = 0) -> set[str]:
    """The values of every ``Enum.MEMBER`` or ``Enum("value")`` an expression names anywhere, names followed.

    For an item the checker cannot evaluate, such as a comprehension or a helper call.
    """
    if node is None or depth > _MAX_HOPS:
        return set()
    found: set[str] = set()
    for sub in _flowing(node):
        if isinstance(sub, (ast.Attribute, ast.Call)) and (value := enum_value(sub, enum, bindings)) is not None:
            found.add(value)
        elif isinstance(sub, ast.Name) and (value := bindings.resolve(sub)) is not sub:
            found |= named_enum_values(value, enum, bindings, depth + 1)
    return found


def _flowing(node: ast.AST) -> Iterator[ast.AST]:
    """``node`` and the sub-nodes whose values can reach its result: comparisons, conditions and filters are skipped."""
    if isinstance(node, ast.Compare):
        return
    yield node
    skipped: list[ast.AST] = []
    if isinstance(node, ast.comprehension):
        skipped = list(node.ifs)
    elif isinstance(node, ast.IfExp):
        skipped = [node.test]
    elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
        skipped = list(node.values[:-1])
    for child in ast.iter_child_nodes(node):
        if not any(child is skip for skip in skipped):
            yield from _flowing(child)


def lists_tool(node: ast.expr | None, tool: str, bindings: Bindings) -> bool:
    """True when a ``tools=`` argument lists ``tool``, as the tool object or as its name."""
    return any(
        (isinstance(sub, ast.Name) and sub.id == tool) or (isinstance(sub, ast.Constant) and sub.value == tool)
        for item in elements(node, bindings)
        for sub in ast.walk(item)
    )


def imported_from(tree: ast.AST, module: str, symbol: str) -> bool:
    """True when ``symbol`` is imported from ``module`` (or a submodule), or ``module`` itself is imported."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(module):
            if any(alias.name == symbol for alias in node.names):
                return True
        if isinstance(node, ast.Import) and any(alias.name.startswith(module) for alias in node.names):
            return True
    return False


def detection_scope_value(node: ast.expr | None, bindings: Bindings) -> str | None:
    """The value a ``detection_scope=`` argument passes, ``None`` when absent.

    Anything that is not a ``DetectionScope`` member, a string or ``DetectionScope("...")``
    is returned as written, so the caller can report it (``GuardrailExecutionStage.FILES``).
    """
    if node is None:
        return None
    value = enum_value(node, "DetectionScope", bindings)
    return value if value is not None else ast.unparse(bindings.resolve(node) or node)


def wired_middleware_calls(bindings: Bindings) -> list[ast.Call]:
    """Middleware calls spread (``*``) into a ``create_agent(middleware=[...])`` list, inline or through names."""
    calls: list[ast.Call] = []
    for node in ast.walk(bindings.tree):
        if not (isinstance(node, ast.Call) and call_name(node) == "create_agent"):
            continue
        listing = bindings.resolve(next((kw.value for kw in node.keywords if kw.arg == "middleware"), None))
        if not isinstance(listing, (ast.List, ast.Tuple)):
            continue
        for item in listing.elts:
            target = bindings.resolve(item.value) if isinstance(item, ast.Starred) else None
            if isinstance(target, ast.Call):
                calls.append(target)
    return calls


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
        elif isinstance(node, (ast.For, ast.AsyncFor)) and isinstance(node.target, ast.Name) and node.target.id == name:
            values.extend(node.iter.elts if isinstance(node.iter, (ast.Tuple, ast.List)) else [node.iter])
    return values


def _appended(fn: ast.AST, name: str, before: ast.AST) -> list[ast.expr]:
    """The items the code adds to the list ``name`` with ``.append``, ``.insert`` or ``.extend`` before ``before``."""
    items: list[ast.expr] = []
    for node in ast.walk(fn):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == name
            and node.args
            and (node.lineno, node.col_offset) < (before.lineno, before.col_offset)
        ):
            continue
        if node.func.attr in ("append", "insert"):
            items.append(node.args[-1])
        elif node.func.attr == "extend":
            for added in _resolve(node.args[0], fn):
                items.extend(added.elts if isinstance(added, (ast.List, ast.Tuple)) else [added])
    return items


def _alternatives(node: ast.expr) -> Iterator[ast.expr]:
    """``node``, or each value it can take: both branches of ``a if c else b``, each operand of ``a or b``,
    and the last operand of ``a and b`` (its value when every operand is truthy)."""
    if isinstance(node, ast.IfExp):
        yield from _alternatives(node.body)
        yield from _alternatives(node.orelse)
    elif isinstance(node, ast.BoolOp):
        for operand in node.values if isinstance(node.op, ast.Or) else node.values[-1:]:
            yield from _alternatives(operand)
    else:
        yield node


def _resolve(expr: ast.expr, fn: ast.AST) -> list[ast.expr]:
    values = _assigned_values(fn, expr.id) if isinstance(expr, ast.Name) else []
    return [alternative for value in values or [expr] for alternative in _alternatives(value)]


def _reads_field_by_name(node: ast.AST, fields: list[str]) -> bool:
    """``getattr(<obj>, "<field>"[, default])``, the same read as ``<obj>.<field>``."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "getattr"
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value in fields
    )


def _names_field(expr: ast.AST, fn: ast.AST, fields: list[str], seen: frozenset[str] = frozenset()) -> bool:
    """True when ``expr`` reads an input Attachment field, directly or through local names."""
    for sub in ast.walk(expr):
        if (isinstance(sub, ast.Attribute) and sub.attr in fields) or _reads_field_by_name(sub, fields):
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
    if isinstance(arg, ast.Name) and any(_valid_reference(item, fn, fields) for item in _appended(fn, arg.id, call)):
        return True
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
            f"FAIL: render_attachments_block receives no reference built from the input's Attachment field ({fields}): "
            "pass <field>.model_dump(mode=\"json\", exclude_none=True), or an {\"ID\", \"FullName\", \"MimeType\"} "
            f"dict built from it, where <field> is read as <state>.<field> or getattr(<state>, \"<field>\"). Got: {got}"
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


def require_detection_scope(call: ast.Call, expected: str, bindings: Bindings, reason: str) -> None:
    value = detection_scope_value(call_arg(call, "detection_scope"), bindings)
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
