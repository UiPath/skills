#!/usr/bin/env python3
"""Check that a callable deterministic guardrail blocks secret customer IDs."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

GRAPH = Path("graph.py")
TARGET_TOOL = "lookup_account_info"


def check(condition: bool, message: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {message}")


def call_name(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((item.value for item in call.keywords if item.arg == name), None)


def mentions_secret(node: ast.AST) -> bool:
    return any(
        isinstance(item, ast.Constant)
        and isinstance(item.value, str)
        and "secret" in item.value.lower()
        for item in ast.walk(node)
    )


def is_callable_rule(node: ast.expr, functions: dict[str, ast.AST]) -> bool:
    if isinstance(node, ast.Lambda):
        return mentions_secret(node)
    if isinstance(node, ast.Name) and node.id in functions:
        return mentions_secret(functions[node.id])
    return False


def list_contains_name(node: ast.expr | None, expected: str) -> bool:
    if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return False
    return any(call_name(item) == expected for item in node.elts)


def create_agent_middleware_calls(tree: ast.AST) -> list[ast.Call]:
    """Return calls actually spread into a create_agent middleware list."""
    assignments: dict[str, ast.expr] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assignments[target.id] = node.value

    calls: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or call_name(node) != "create_agent":
            continue
        middleware = keyword(node, "middleware")
        if isinstance(middleware, ast.Name):
            middleware = assignments.get(middleware.id)
        if not isinstance(middleware, (ast.List, ast.Tuple)):
            continue
        for item in middleware.elts:
            if not isinstance(item, ast.Starred):
                continue
            value = item.value
            if isinstance(value, ast.Name):
                value = assignments.get(value.id)
            if isinstance(value, ast.Call):
                calls.append(value)
    return calls


def valid_middleware(tree: ast.AST, functions: dict[str, ast.AST]) -> bool:
    for node in create_agent_middleware_calls(tree):
        if call_name(node) != "UiPathDeterministicGuardrailMiddleware":
            continue
        rules = keyword(node, "rules")
        if not isinstance(rules, (ast.List, ast.Tuple)) or not rules.elts:
            continue
        if not any(is_callable_rule(rule, functions) for rule in rules.elts):
            continue
        if not list_contains_name(keyword(node, "tools"), TARGET_TOOL):
            continue
        if call_name(keyword(node, "action")) != "BlockAction":
            continue
        return True
    return False


def valid_decorator(tree: ast.AST, functions: dict[str, ast.AST]) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != TARGET_TOOL:
            continue
        if not any(call_name(item) == "tool" for item in node.decorator_list):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or call_name(decorator) != "guardrail":
                continue
            validator = keyword(decorator, "validator")
            if not isinstance(validator, ast.Call) or call_name(validator) != "CustomValidator":
                continue
            rule = keyword(validator, "rule")
            if (
                rule is not None
                and is_callable_rule(rule, functions)
                and call_name(keyword(decorator, "action")) == "BlockAction"
            ):
                return True
    return False


def main() -> None:
    check(GRAPH.is_file(), f"{GRAPH} not found in {Path.cwd()}")
    source = GRAPH.read_text()
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")

    functions = {
        node.name: node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    middleware = valid_middleware(tree, functions)
    decorator = valid_decorator(tree, functions)

    check(
        middleware or decorator,
        "No deterministic guardrail targets lookup_account_info with a callable "
        "rule that checks for 'secret' and uses BlockAction",
    )
    print(f"OK: callable deterministic rule used ({'middleware' if middleware else 'decorator'} style)")
    print("OK: BlockAction used")
    print("OK: deterministic guardrail with callable 'secret' rule targets lookup_account_info")


if __name__ == "__main__":
    main()
