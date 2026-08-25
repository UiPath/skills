#!/usr/bin/env python3
"""Check that a user prompt attacks MIDDLEWARE guardrail was added to graph.py.

Validates (middleware style, LangChain agent):
- guardrail symbols imported from uipath_langchain.guardrails (NOT
  uipath.platform.guardrails — the platform path silently no-ops for LangChain)
- UiPathUserPromptAttacksMiddleware is spread (*) into create_agent(middleware=[...])
- Scope is LLM (user prompt attacks is LLM-only): either GuardrailScope.LLM is
  passed explicitly, or scopes= is omitted (the SDK defaults this middleware to
  LLM). An explicit AGENT/TOOL scope fails.
- BlockAction is used (block adversarial inputs)
- Decorator style is NOT used (no @guardrail decorator) — this test specifically
  covers the middleware path, distinct from the decorator-style sibling test

NOT validated: execution stage. The *Middleware classes take no ``stage``
argument (only the @guardrail decorator does); user prompt attacks runs at PRE
internally, fixed by the validator. Requiring a literal
``GuardrailExecutionStage.PRE`` token would force dead code.
"""

import ast
import os
import re
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
MIDDLEWARE = "UiPathUserPromptAttacksMiddleware"


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def check(condition: bool, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")

    # Import source — the #1 coded-guardrail correctness rule.
    check(
        "from uipath_langchain.guardrails import" in src,
        "guardrail symbols not imported from uipath_langchain.guardrails — the "
        "uipath.platform.guardrails path silently no-ops for LangChain agents",
    )
    print("OK: imports from uipath_langchain.guardrails")

    check(MIDDLEWARE in src, f"{MIDDLEWARE} not found in graph.py")
    print(f"OK: {MIDDLEWARE} referenced")

    middleware_calls = [c for c in spread_middleware_calls(tree) if call_name(c) == MIDDLEWARE]
    check(
        bool(middleware_calls),
        f"{MIDDLEWARE} not spread with * into the middleware list "
        f"(accepts inline `[*{MIDDLEWARE}(...)]` or a variable "
        f"`m = {MIDDLEWARE}(...); middleware=[*m]`)",
    )
    print(f"OK: {MIDDLEWARE} spread with * into middleware list")

    check("middleware=" in src, "create_agent() has no middleware= argument")
    print("OK: middleware= argument present")

    # LLM-only scope. scopes= is optional and defaults to LLM, so accept either an
    # explicit GuardrailScope.LLM or an omitted scopes=; reject an explicit AGENT/TOOL.
    def scope_ok(call: ast.Call) -> bool:
        scopes = call_kwarg(call, "scopes")
        if scopes is None:
            return True  # defaults to LLM (user prompt attacks is LLM-only)
        rendered = ast.unparse(scopes)
        return (
            "GuardrailScope.LLM" in rendered
            and "GuardrailScope.AGENT" not in rendered
            and "GuardrailScope.TOOL" not in rendered
        )

    check(
        all(scope_ok(c) for c in middleware_calls),
        "user prompt attacks is LLM-scoped only — pass scopes=[GuardrailScope.LLM] "
        "or omit scopes= (it defaults to LLM); do not use AGENT or TOOL scope",
    )
    print("OK: LLM scope (explicit or default)")

    check(
        "BlockAction" in src,
        "BlockAction not found — adversarial inputs should be blocked",
    )
    print("OK: BlockAction used")

    # Must NOT be decorator style — this is the middleware variant.
    check(
        not bool(re.search(r"@guardrail\s*\(", src)),
        "@guardrail(...) decorator found — this task requires the middleware style, "
        "not the decorator style (see the decorator-style sibling test)",
    )
    print("OK: no @guardrail decorator (middleware style confirmed)")

    print("OK: user prompt attacks middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
