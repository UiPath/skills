#!/usr/bin/env python3
"""Check that a PII detection middleware guardrail was correctly added to graph.py.

Validates:
- UiPathPIIDetectionMiddleware is imported from uipath_langchain.guardrails
- GuardrailScope is imported from uipath.core.guardrails
- The middleware is spread (*) into create_agent(middleware=[...])
- At least one entry covers Agent scope (GuardrailScope.AGENT)
- At least one entry covers Tool scope (GuardrailScope.TOOL) with tools=[...]
- LogAction (not just BlockAction) is used
- PIIDetectionEntityType.EMAIL and PIIDetectionEntityType.PHONE_NUMBER are referenced
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
        "UiPathPIIDetectionMiddleware" in src,
        "UiPathPIIDetectionMiddleware not found in graph.py — missing import or usage",
    )
    print("OK: UiPathPIIDetectionMiddleware referenced")

    check(
        "GuardrailScope" in src,
        "GuardrailScope not found — import from uipath.core.guardrails is missing",
    )
    print("OK: GuardrailScope referenced")

    # Spread pattern: *UiPathPIIDetectionMiddleware(
    check(
        bool(re.search(r"\*UiPathPIIDetectionMiddleware\s*\(", src)),
        "UiPathPIIDetectionMiddleware not spread with * into middleware list",
    )
    print("OK: *UiPathPIIDetectionMiddleware(...) spread pattern found")

    check(
        "middleware=" in src,
        "create_agent() has no middleware= argument",
    )
    print("OK: middleware= argument present in create_agent()")

    check(
        "GuardrailScope.AGENT" in src,
        "GuardrailScope.AGENT not present — Agent scope not configured",
    )
    print("OK: GuardrailScope.AGENT used")

    check(
        "GuardrailScope.TOOL" in src,
        "GuardrailScope.TOOL not present — Tool scope not configured",
    )
    print("OK: GuardrailScope.TOOL used")

    check(
        "tools=" in src,
        "tools= argument not found — Tool-scoped middleware missing tools=[...] parameter",
    )
    print("OK: tools= parameter present for Tool-scoped middleware")

    check(
        "LogAction" in src,
        "LogAction not found — expected log (not block) action for PII detection",
    )
    print("OK: LogAction used")

    check(
        "EMAIL" in src,
        "PIIDetectionEntityType.EMAIL not referenced",
    )
    print("OK: EMAIL entity referenced")

    check(
        "PHONE_NUMBER" in src,
        "PIIDetectionEntityType.PHONE_NUMBER not referenced",
    )
    print("OK: PHONE_NUMBER entity referenced")

    print("OK: PII middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
