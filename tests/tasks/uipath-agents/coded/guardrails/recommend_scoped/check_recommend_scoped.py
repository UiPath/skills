#!/usr/bin/env python3
"""Tool-scoped guardrail recommendation check — SimpleCodedAgent.

Validates:
  - graph.py still parses as Python (ast.parse)
  - Exactly one Tool-scoped representation targets lookup_account_info:
      (a) Decorator: @guardrail(...) placed directly above @tool def lookup_account_info, OR
      (b) Middleware: a *<...>Middleware(...) spread that names lookup_account_info
          inside its tools=[...] argument AND uses GuardrailScope.TOOL in scopes=[...]
  - At most one of (a)/(b) is used — both is a redundant double-configuration.
  - Either form must reference lookup_account_info as a Python identifier (not a string).
"""

import ast
import re
import sys
from pathlib import Path

GRAPH = Path("graph.py")
TARGET_TOOL = "lookup_account_info"


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def deco_name(deco: ast.expr) -> str | None:
    target = deco.func if isinstance(deco, ast.Call) else deco
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def is_guardrail_call(deco: ast.expr) -> bool:
    return isinstance(deco, ast.Call) and deco_name(deco) == "guardrail"


def has_decorator_above_tool(tree: ast.AST) -> bool:
    """True iff a FunctionDef named TARGET_TOOL has both @tool and @guardrail decorators."""
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != TARGET_TOOL:
            continue
        has_tool = any(deco_name(d) == "tool" for d in node.decorator_list)
        has_guard = any(is_guardrail_call(d) for d in node.decorator_list)
        if has_tool and has_guard:
            return True
    return False


def attr_chain(node: ast.expr) -> str | None:
    """Return dotted name for a Name or Attribute chain, else None."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = attr_chain(node.value)
        return f"{prefix}.{node.attr}" if prefix else None
    return None


def find_middleware_with_target_tool(tree: ast.AST) -> list[str]:
    """Find *<X>Middleware(...) spread calls whose kwargs include
    scopes containing GuardrailScope.TOOL and tools containing the bare identifier
    TARGET_TOOL.

    Returns matching middleware class names (or [] if none).
    """
    hits: list[str] = []
    for node in ast.walk(tree):
        # `*Foo(...)` inside a list/call appears as ast.Starred(value=ast.Call(...))
        if not isinstance(node, ast.Starred):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        name = deco_name(call)
        if not name or not name.endswith("Middleware"):
            continue
        # Walk keyword args
        scopes_ok = False
        tools_ok = False
        for kw in call.keywords:
            if kw.arg == "scopes" and isinstance(kw.value, (ast.List, ast.Tuple)):
                for el in kw.value.elts:
                    if attr_chain(el) == "GuardrailScope.TOOL":
                        scopes_ok = True
                        break
            elif kw.arg == "tools" and isinstance(kw.value, (ast.List, ast.Tuple)):
                for el in kw.value.elts:
                    # bare identifier (Python object), not a string literal
                    if isinstance(el, ast.Name) and el.id == TARGET_TOOL:
                        tools_ok = True
                        break
        if scopes_ok and tools_ok:
            hits.append(name)
    return hits


def main() -> None:
    src = read()

    # 1. Syntactic
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {e}")
    print("OK: graph.py parses as valid Python")

    # 1b. Adapter-registration import: guardrail symbols must come from
    #     uipath_langchain.guardrails (registers the LangChain adapter as an import
    #     side effect). Importing from uipath.platform.guardrails makes guardrails no-op.
    if "uipath_langchain.guardrails" not in src:
        sys.exit(
            "FAIL: graph.py never imports from uipath_langchain.guardrails. Without it the "
            "LangChain guardrail adapter is not registered and the guardrail silently "
            "no-ops. Import guardrail/validators from uipath_langchain.guardrails."
        )
    if re.search(r"from\s+uipath\.platform\.guardrails\s+import", src):
        sys.exit(
            "FAIL: graph.py imports guardrail symbols from uipath.platform.guardrails. Use "
            "uipath_langchain.guardrails instead — the platform module exposes identical "
            "names but does not register the adapter, so the guardrail silently no-ops."
        )
    print("OK: guardrail symbols imported from uipath_langchain.guardrails (adapter registers)")

    # 2. lookup_account_info must still be the tool (sanity — the fixture defines it).
    has_target = any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == TARGET_TOOL
        for n in ast.walk(tree)
    )
    if not has_target:
        sys.exit(
            f"FAIL: {TARGET_TOOL!r} function definition not found in graph.py — "
            "fixture was modified unexpectedly"
        )
    print(f"OK: {TARGET_TOOL!r} tool definition still present")

    # 3. Detect both representations
    decorator_form = has_decorator_above_tool(tree)
    middleware_form = find_middleware_with_target_tool(tree)
    n_forms = int(decorator_form) + (1 if middleware_form else 0)

    if n_forms == 0:
        sys.exit(
            f"FAIL: no Tool-scoped guardrail targets {TARGET_TOOL!r}. Expected either\n"
            f"  (a) @guardrail(...) above @tool def {TARGET_TOOL}, OR\n"
            f"  (b) *<X>Middleware(... scopes=[GuardrailScope.TOOL], "
            f"tools=[{TARGET_TOOL}] ...) spread into create_agent(middleware=[...])"
        )
    if n_forms > 1:
        sys.exit(
            f"FAIL: both decorator and middleware representations target {TARGET_TOOL!r} — "
            "use exactly one to avoid double-configuration"
        )

    if decorator_form:
        print(f"OK: decorator-style guardrail placed above @tool def {TARGET_TOOL}")
    else:
        print(
            f"OK: middleware-style guardrail spread with tools=[{TARGET_TOOL}] and "
            f"GuardrailScope.TOOL — class(es): {middleware_form}"
        )

    print("OK: coded recommend-scoped check passed")


if __name__ == "__main__":
    main()
