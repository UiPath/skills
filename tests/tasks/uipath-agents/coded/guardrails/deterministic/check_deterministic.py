#!/usr/bin/env python3
"""Check that a deterministic guardrail blocking 'secret' was correctly added to graph.py.

Validates (middleware or decorator style both accepted):
- Either UiPathDeterministicGuardrailMiddleware or CustomValidator is used
- The configured callable checks customer_id for the word "secret"
- BlockAction is configured on that guardrail
- The guardrail targets or decorates the lookup_account_info tool
"""

import ast
import sys
from pathlib import Path

GRAPH = Path("graph.py")


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def check(condition: bool, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def call_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((item.value for item in call.keywords if item.arg == name), None)


def positional_or_keyword(call: ast.Call, index: int, name: str) -> ast.expr | None:
    """Like `keyword`, but also accepts the argument passed positionally at `index`.

    `CustomValidator`'s `rule` is a regular (positional-or-keyword) constructor
    parameter, so `CustomValidator(lambda args: ...)` is as valid as
    `CustomValidator(rule=lambda args: ...)` — both bind the same parameter.
    """
    found = keyword(call, name)
    if found is not None:
        return found
    if len(call.args) > index:
        return call.args[index]
    return None


def is_call(node: ast.expr | None, name: str) -> bool:
    return isinstance(node, ast.Call) and call_name(node.func) == name


def collection_items(node: ast.expr | None) -> list[ast.expr]:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return list(node.elts)
    return []


def contains_reference(node: ast.AST, name: str) -> bool:
    return any(
        (isinstance(item, ast.Name) and item.id == name)
        or (isinstance(item, ast.Constant) and item.value == name)
        for item in ast.walk(node)
    )


def contains_string_literal(node: ast.AST, value: str) -> bool:
    return any(
        isinstance(item, ast.Constant)
        and isinstance(item.value, str)
        and item.value.casefold() == value.casefold()
        for item in ast.walk(node)
    )


def contains_substring_literal(node: ast.AST, value: str) -> bool:
    """Return whether any string constant under `node` contains `value` (casefolded).

    Looser than `contains_string_literal` — a regex pattern carries `secret` inside
    delimiters (e.g. `r"\\bsecret\\b"`), so an exact-match check would never fire.
    """
    return any(
        isinstance(item, ast.Constant)
        and isinstance(item.value, str)
        and value.casefold() in item.value.casefold()
        for item in ast.walk(node)
    )


def checks_secret_customer_id_membership(node: ast.AST) -> bool:
    """Return whether `node` contains `"secret" in <customer_id expression>`."""
    for item in ast.walk(node):
        if not isinstance(item, ast.Compare):
            continue

        operands = [item.left, *item.comparators]
        for index, operator in enumerate(item.ops):
            if not isinstance(operator, ast.In):
                continue
            if contains_string_literal(operands[index], "secret") and contains_reference(
                operands[index + 1], "customer_id"
            ):
                return True
    return False


def checks_secret_customer_id_regex(node: ast.AST) -> bool:
    """Return whether `node` contains a `re.search`/`re.match`/`re.fullmatch` call
    whose pattern argument mentions "secret" and whose target argument references
    `customer_id` — the regex-based equivalent of the membership check above (e.g.
    `re.search(r"\\bsecret\\b", str(tool_input.get("customer_id", "")), re.IGNORECASE)`).
    """
    for item in ast.walk(node):
        if not isinstance(item, ast.Call) or call_name(item.func) not in ("search", "match", "fullmatch"):
            continue
        args = item.args
        if len(args) < 2:
            continue
        pattern, target = args[0], args[1]
        if contains_substring_literal(pattern, "secret") and contains_reference(target, "customer_id"):
            return True
    return False


def checks_secret_customer_id(node: ast.Lambda | ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    """Return whether a callable checks customer_id for "secret" — either via
    `"secret" in <expr>` membership, or an equivalent `re.search`/`match`/`fullmatch`."""
    return checks_secret_customer_id_membership(node) or checks_secret_customer_id_regex(node)


def resolve_rule(
    node: ast.expr,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> ast.Lambda | ast.FunctionDef | ast.AsyncFunctionDef | None:
    if isinstance(node, ast.Lambda):
        return node
    if isinstance(node, ast.Name):
        return functions.get(node.id)
    return None


def has_valid_rule(
    node: ast.expr | None,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> bool:
    for item in collection_items(node):
        rule = resolve_rule(item, functions)
        if rule is not None and checks_secret_customer_id(rule):
            return True
    return False


def valid_middleware(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node.func) != "UiPathDeterministicGuardrailMiddleware":
            continue

        tools = collection_items(keyword(node, "tools"))
        targets_lookup = any(isinstance(tool, ast.Name) and tool.id == "lookup_account_info" for tool in tools)
        if (
            targets_lookup
            and has_valid_rule(keyword(node, "rules"), functions)
            and is_call(keyword(node, "action"), "BlockAction")
        ):
            return True
    return False


def valid_decorator(
    tree: ast.Module,
    functions: dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
) -> bool:
    lookup_functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "lookup_account_info"
    ]
    for function in lookup_functions:
        for decorator in function.decorator_list:
            if not isinstance(decorator, ast.Call) or call_name(decorator.func) != "guardrail":
                continue

            validator = keyword(decorator, "validator")
            if not is_call(validator, "CustomValidator"):
                continue
            assert isinstance(validator, ast.Call)
            rule = positional_or_keyword(validator, 0, "rule")
            resolved = resolve_rule(rule, functions) if rule is not None else None
            if (
                resolved is not None
                and checks_secret_customer_id(resolved)
                and is_call(keyword(decorator, "action"), "BlockAction")
            ):
                return True
    return False


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src, filename=str(GRAPH))
    except SyntaxError as error:
        sys.exit(f"FAIL: {GRAPH} is not valid Python: {error}")

    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    middleware_ok = valid_middleware(tree, functions)
    decorator_ok = valid_decorator(tree, functions)
    check(
        middleware_ok or decorator_ok,
        "No deterministic guardrail with a callable rule checking customer_id for 'secret', "
        "a BlockAction, and lookup_account_info targeting was found",
    )
    if middleware_ok:
        print("OK: UiPathDeterministicGuardrailMiddleware used (middleware style)")
    else:
        print("OK: CustomValidator used (decorator style)")
    print("OK: callable rule checks customer_id for 'secret'")
    print("OK: BlockAction used")
    print("OK: lookup_account_info referenced (target tool)")
    print("OK: Deterministic guardrail with 'secret' rule correctly added to graph.py")


if __name__ == "__main__":
    main()
