"""Shared AST helpers for coded-guardrail check scripts.

Detects UiPath ``…Middleware`` classes spread (``*``) into a
``create_agent(middleware=[...])`` list, accepting BOTH valid forms:

  - inline:   ``middleware=[*UiPathPIIDetectionMiddleware(...)]``
  - variable: ``m = UiPathPIIDetectionMiddleware(...); middleware=[*m]``

A middleware instance is iterable, so ``[*var]`` and ``[*Class(...)]`` are
equivalent. The original checks matched only the inline form via regex and
wrongly rejected the (equally valid) variable form.
"""

from __future__ import annotations

import ast


def call_name(call: ast.Call) -> str | None:
    """Callee name of a Call node — ``Foo(...)`` -> ``"Foo"``, ``mod.Foo(...)`` -> ``"Foo"``."""
    fn = call.func
    if isinstance(fn, ast.Attribute):
        return fn.attr
    if isinstance(fn, ast.Name):
        return fn.id
    return None


def _var_to_call(tree: ast.AST) -> dict:
    """Map each variable name to the Call it was last assigned (resolves ``*name`` spreads)."""
    mapping: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    mapping[target.id] = node.value
    return mapping


def spread_middleware_calls(tree: ast.AST) -> list:
    """Every Call spread with ``*`` into a list — directly (``[*Foo(...)]``) or via a
    one-level variable (``m = Foo(...); [*m]``). Returns the underlying Call nodes
    (the same node objects produced by ``ast.walk``, so callers may key on ``id()``)."""
    var_to_call = _var_to_call(tree)
    calls: list = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Starred):
            value = node.value
            if isinstance(value, ast.Call):
                calls.append(value)
            elif isinstance(value, ast.Name) and value.id in var_to_call:
                calls.append(var_to_call[value.id])
    return calls
