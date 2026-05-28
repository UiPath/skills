#!/usr/bin/env python3
"""Check that a deterministic guardrail blocking 'secret' was correctly added to graph.py.

Validates (middleware or decorator style both accepted):
- Either UiPathDeterministicGuardrailMiddleware or CustomValidator is used
- A lambda/rule that checks for the word "secret" in the input is present
- BlockAction is used
- The guardrail targets the lookup_account_info tool
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

    # Accept either middleware or decorator style
    has_middleware = "UiPathDeterministicGuardrailMiddleware" in src
    has_decorator = "CustomValidator" in src

    check(
        has_middleware or has_decorator,
        "Neither UiPathDeterministicGuardrailMiddleware nor CustomValidator found in graph.py "
        "— deterministic guardrail not added",
    )
    if has_middleware:
        print("OK: UiPathDeterministicGuardrailMiddleware used (middleware style)")
    else:
        print("OK: CustomValidator used (decorator style)")

    # Rule must check for "secret" somewhere in the source
    check(
        "secret" in src.lower(),
        "No reference to 'secret' found in graph.py — the blocking rule must check for this word",
    )
    print("OK: 'secret' keyword referenced in the rule")

    # A lambda (or function) must be the rule
    has_lambda = bool(re.search(r"lambda\s+\w+.*secret", src, re.IGNORECASE))
    has_func_rule = bool(re.search(r"def\s+\w+.*\(.*\).*:\s*\n.*secret", src, re.IGNORECASE))
    check(
        has_lambda or has_func_rule,
        "No lambda or function rule checking for 'secret' found — the rule must be a callable",
    )
    print("OK: lambda/function rule checking for 'secret' found")

    check(
        "BlockAction" in src,
        "BlockAction not found — deterministic guardrail must use a block action",
    )
    print("OK: BlockAction used")

    # lookup_account_info should be referenced near the guardrail
    check(
        "lookup_account_info" in src,
        "lookup_account_info not referenced after modification — Tool-scoped guardrail "
        "should target this tool",
    )
    print("OK: lookup_account_info referenced (target tool)")

    print("OK: Deterministic guardrail with 'secret' rule correctly added to graph.py")


if __name__ == "__main__":
    main()
