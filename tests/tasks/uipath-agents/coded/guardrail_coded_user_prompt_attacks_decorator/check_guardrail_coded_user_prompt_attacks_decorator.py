#!/usr/bin/env python3
"""Check that a user prompt attacks decorator guardrail was correctly added to graph.py.

Validates:
- guardrail decorator imported from uipath_langchain.guardrails
- UserPromptAttacksValidator imported and used
- @guardrail decorator present above an LLM-related function (create_llm or similar)
- GuardrailExecutionStage.PRE used (user prompt attacks is PRE-only)
- BlockAction used (user prompt attacks should block, not log)
- No middleware spread pattern (*UiPathUserPromptAttacksMiddleware) — must be decorator style
"""

import re
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


def main() -> None:
    src = read()

    check(
        "guardrail" in src and "from uipath_langchain.guardrails import" in src,
        "guardrail decorator not imported from uipath_langchain.guardrails",
    )
    print("OK: guardrail imported")

    check(
        "UserPromptAttacksValidator" in src,
        "UserPromptAttacksValidator not found in graph.py",
    )
    print("OK: UserPromptAttacksValidator referenced")

    # @guardrail decorator syntax
    check(
        bool(re.search(r"@guardrail\s*\(", src)),
        "@guardrail(...) decorator not found in graph.py",
    )
    print("OK: @guardrail(...) decorator found")

    # @guardrail must appear before a def (the LLM factory function)
    # Look for @guardrail followed eventually by def (allowing for stacked decorators)
    check(
        bool(re.search(r"@guardrail[\s\S]{0,500}?def\s+\w+", src)),
        "@guardrail decorator does not appear above any function definition",
    )
    print("OK: @guardrail placed above a function definition")

    has_validator_call = bool(re.search(r"UserPromptAttacksValidator\s*\(", src))
    check(
        has_validator_call,
        "UserPromptAttacksValidator(...) not instantiated in graph.py",
    )
    print("OK: UserPromptAttacksValidator() instantiated")

    check(
        "GuardrailExecutionStage.PRE" in src,
        "GuardrailExecutionStage.PRE not found — user prompt attacks must run at PRE stage",
    )
    print("OK: GuardrailExecutionStage.PRE used")

    check(
        "BlockAction" in src,
        "BlockAction not found — user prompt attacks should block adversarial inputs",
    )
    print("OK: BlockAction used")

    # Must NOT use middleware spread pattern
    check(
        not bool(re.search(r"\*UiPathUserPromptAttacksMiddleware\s*\(", src)),
        "Middleware spread *UiPathUserPromptAttacksMiddleware found — task requires decorator style",
    )
    print("OK: no middleware spread (decorator style confirmed)")

    print("OK: User prompt attacks decorator guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
