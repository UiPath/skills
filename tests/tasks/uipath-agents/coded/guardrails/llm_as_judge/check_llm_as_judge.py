#!/usr/bin/env python3
"""Check that a UiPathLLMAsJudgeMiddleware guardrail was correctly added to graph.py.

Validates:
- UiPathLLMAsJudgeMiddleware is imported from uipath_langchain.guardrails (not uipath.platform.guardrails)
- GuardrailScope is imported from uipath.core.guardrails
- The middleware is spread (*) into create_agent(middleware=[...])
- guardrail_text= keyword argument is present (the rule text)
- model= keyword argument is present
- BlockAction is referenced
- GuardrailScope.AGENT is used
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from _shared.guardrail_middleware import call_name, spread_middleware_calls  # noqa: E402

GRAPH = Path("graph.py")


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

    check(
        "UiPathLLMAsJudgeMiddleware" in src,
        "UiPathLLMAsJudgeMiddleware not found in graph.py — missing import or usage",
    )
    print("OK: UiPathLLMAsJudgeMiddleware referenced")

    # Import must come from uipath_langchain.guardrails, not uipath.platform.guardrails,
    # so the LangChain adapter registers and the guardrail is actually active.
    check(
        "uipath_langchain.guardrails" in src,
        "Import not from uipath_langchain.guardrails — guardrail would silently no-op "
        "(import from uipath.platform.guardrails bypasses the LangChain adapter)",
    )
    print("OK: imported from uipath_langchain.guardrails")

    check(
        "GuardrailScope" in src,
        "GuardrailScope not found — import from uipath.core.guardrails is missing",
    )
    print("OK: GuardrailScope referenced")

    check(
        any(call_name(c) == "UiPathLLMAsJudgeMiddleware" for c in spread_middleware_calls(tree)),
        "UiPathLLMAsJudgeMiddleware not spread with * into the middleware list "
        "(accepts inline `[*UiPathLLMAsJudgeMiddleware(...)]` or a variable "
        "`m = UiPathLLMAsJudgeMiddleware(...); middleware=[*m]`)",
    )
    print("OK: UiPathLLMAsJudgeMiddleware spread with * into middleware list")

    check(
        "middleware=" in src,
        "create_agent() has no middleware= argument",
    )
    print("OK: middleware= argument present in create_agent()")

    check(
        "guardrail_text=" in src,
        "guardrail_text= not found — the rule text parameter is required",
    )
    print("OK: guardrail_text= parameter present")

    check(
        "model=" in src,
        "model= not found — the model parameter is required for UiPathLLMAsJudgeMiddleware",
    )
    print("OK: model= parameter present")

    check(
        "BlockAction" in src,
        "BlockAction not found — expected block action for LLM as Judge guardrail",
    )
    print("OK: BlockAction used")

    check(
        "GuardrailScope.AGENT" in src,
        "GuardrailScope.AGENT not present — Agent scope not configured",
    )
    print("OK: GuardrailScope.AGENT used")

    print("OK: LLM as Judge middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
