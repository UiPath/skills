#!/usr/bin/env python3
"""Check that an intellectual property middleware guardrail was added to graph.py.

Validates (middleware style, LangChain agent):
- guardrail symbols imported from uipath_langchain.guardrails (NOT
  uipath.platform.guardrails — the LangChain adapter only registers from the
  framework module; the platform path silently no-ops)
- UiPathIntellectualPropertyMiddleware is spread (*) into create_agent(middleware=[...])
- IntellectualPropertyEntityType entities TEXT and CODE are referenced
- GuardrailExecutionStage.POST is used (IP is an output-only / POST-stage concern)
- An LLM or Agent scope is configured, and Tool scope is NOT used
  (intellectual_property does not support Tool scope)
- BlockAction is used (block, not log)
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
MIDDLEWARE = "UiPathIntellectualPropertyMiddleware"


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

    check(
        any(call_name(c) == MIDDLEWARE for c in spread_middleware_calls(tree)),
        f"{MIDDLEWARE} not spread with * into the middleware list "
        f"(accepts inline `[*{MIDDLEWARE}(...)]` or a variable "
        f"`m = {MIDDLEWARE}(...); middleware=[*m]`)",
    )
    print(f"OK: {MIDDLEWARE} spread with * into middleware list")

    check("middleware=" in src, "create_agent() has no middleware= argument")
    print("OK: middleware= argument present")

    # Entities — Text and Code.
    check(
        "IntellectualPropertyEntityType" in src,
        "IntellectualPropertyEntityType not referenced — entities not configured",
    )
    check("TEXT" in src, "IntellectualPropertyEntityType.TEXT not referenced")
    check("CODE" in src, "IntellectualPropertyEntityType.CODE not referenced")
    print("OK: IntellectualPropertyEntityType TEXT and CODE referenced")

    # POST stage — IP is output-only.
    check(
        "GuardrailExecutionStage.POST" in src,
        "GuardrailExecutionStage.POST not found — intellectual property runs at POST stage only",
    )
    print("OK: GuardrailExecutionStage.POST used")

    # Scope — LLM or Agent, never Tool.
    check(
        "GuardrailScope.LLM" in src or "GuardrailScope.AGENT" in src,
        "no GuardrailScope.LLM or GuardrailScope.AGENT — intellectual property "
        "must be scoped to LLM or Agent",
    )
    check(
        "GuardrailScope.TOOL" not in src,
        "GuardrailScope.TOOL present — intellectual property does NOT support Tool scope",
    )
    print("OK: LLM/Agent scope configured, Tool scope absent")

    check(
        "BlockAction" in src,
        "BlockAction not found — protected material should be blocked",
    )
    print("OK: BlockAction used")

    print("OK: intellectual property middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
