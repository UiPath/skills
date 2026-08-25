#!/usr/bin/env python3
"""Check that a BYOG middleware guardrail was correctly added to graph.py.

Validates:
- graph.py still parses as Python
- UiPathByoGuardrailMiddleware is spread (*) into create_agent(middleware=[...])
- It is pinned to the tenant's configuration via validator_name="byog-smoke-agent-pin"
  — the point of the test. A built-in validator (UiPathPIIDetectionMiddleware) or a
  wrong/absent name means the BYO configuration was not actually wired.
- action=BlockAction(...)
- Imported from uipath_langchain.guardrails, not uipath.platform.guardrails
  (Rule 8: the platform import type-checks but skips LangChain adapter
  registration, so the guardrail silently no-ops). The middleware only exists in
  the adapter package, so a platform import is also just wrong.
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from _shared.guardrail_middleware import (  # noqa: E402
    call_kwarg,
    call_name,
    spread_middleware_calls,
)

GRAPH = Path("graph.py")

MIDDLEWARE = "UiPathByoGuardrailMiddleware"
VALIDATOR_NAME = "byog-smoke-agent-pin"


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def check(condition: bool, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def const_str(node: ast.expr | None) -> str | None:
    """The literal str value of a node, or None if it isn't a string constant."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def is_call(node: ast.expr | None, name: str) -> bool:
    return isinstance(node, ast.Call) and call_name(node) == name


def imported_from(tree: ast.AST, symbol: str) -> str | None:
    """Module a symbol was imported from, or None if it is never imported."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == symbol:
                    return node.module
    return None


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src, filename=str(GRAPH))
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")

    # --- the middleware is spread into the middleware list ---
    # spread_middleware_calls accepts both `[*Cls(...)]` and `m = Cls(...); [*m]`.
    byo_calls = [c for c in spread_middleware_calls(tree) if call_name(c) == MIDDLEWARE]
    if not byo_calls:
        spread = sorted({call_name(c) or "?" for c in spread_middleware_calls(tree)})
        check(
            False,
            f"{MIDDLEWARE} not spread with * into the middleware list "
            f"(accepts inline `[*{MIDDLEWARE}(...)]` or a variable "
            f"`m = {MIDDLEWARE}(...); middleware=[*m]`). "
            f"Spread middleware found: {spread or 'none'}",
        )
    print(f"OK: {MIDDLEWARE} spread with * into the middleware list")

    # --- pinned to the seeded BYOG configuration (the point of the test) ---
    pinned = [
        c for c in byo_calls
        if const_str(call_kwarg(c, "validator_name")) == VALIDATOR_NAME
    ]
    if not pinned:
        seen = [const_str(call_kwarg(c, "validator_name")) for c in byo_calls]
        check(
            False,
            f"no {MIDDLEWARE} pinned to the tenant's BYOG configuration. Expected "
            f'validator_name="{VALIDATOR_NAME}", got: {seen}',
        )
    call = pinned[0]
    print(f'OK: pinned to the BYOG configuration (validator_name="{VALIDATOR_NAME}")')

    # --- block action ---
    check(
        is_call(call_kwarg(call, "action"), "BlockAction"),
        "action=BlockAction(...) not found on the BYOG middleware — the user asked "
        "to block on violations",
    )
    print("OK: action=BlockAction(...)")

    # --- adapter import (Rule 8) ---
    module = imported_from(tree, MIDDLEWARE)
    check(
        module is not None,
        f"{MIDDLEWARE} is used but never imported",
    )
    check(
        module == "uipath_langchain.guardrails",
        f"{MIDDLEWARE} imported from {module!r} — a LangChain agent must import "
        "guardrail symbols from 'uipath_langchain.guardrails' so the adapter "
        "registers; otherwise the guardrail silently no-ops",
    )
    print("OK: imported from uipath_langchain.guardrails")

    print("OK: BYOG middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
