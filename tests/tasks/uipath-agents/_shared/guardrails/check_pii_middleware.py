#!/usr/bin/env python3
"""Check that a PII detection middleware guardrail was correctly added to graph.py.

Validates:
- UiPathPIIDetectionMiddleware is imported from uipath_langchain.guardrails
- The middleware is spread (*) into create_agent(middleware=[...]), inline or through a variable
- One wired entry covers Agent scope and does not run at POST only
- One wired entry covers Tool scope with tools=[lookup_account_info]
- Every wired PII entry logs (action=LogAction(...)), not blocks
- The entities cover Email and PhoneNumber
- The Input model declares an Attachment field and render_attachments_block puts it
  into the user message (the uploaded statement)
- The Agent-scope entry sets detection_scope to Both (text and file); any other
  detection_scope is a valid value

Arguments are read by keyword or SDK position, names resolve in the scope where the
middleware is built, and an enum may be a member, an alias of the enum or its value.
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.guardrails.coded_file_guardrail_assertions import (
    DETECTION_SCOPE_VALUES,
    Bindings,
    call_arg,
    detection_scope_value,
    elements,
    enum_value,
    enum_values,
    imported_from,
    lists_tool,
    require_attachment_input,
    require_detection_scope,
    require_rendered_attachments,
    wired_middleware_calls,
)
from _shared.guardrails.guardrail_middleware import call_name

GRAPH = Path("graph.py")
TOOL = "lookup_account_info"
REQUIRED_ENTITIES = {"EMAIL": "Email", "PHONE_NUMBER": "PhoneNumber"}


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def check(condition: object, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def entity_values(call: ast.Call, bindings: Bindings) -> set[str]:
    """The entity names one PII middleware sends: the name of each PIIDetectionEntity(...) in entities=."""
    return {
        value
        for item in elements(call_arg(call, "entities"), bindings)
        if isinstance(item, ast.Call) and call_name(item) == "PIIDetectionEntity"
        if (value := enum_value(call_arg(item, "name"), "PIIDetectionEntityType", bindings)) is not None
    }


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")
    bindings = Bindings(tree)

    check(
        imported_from(tree, "uipath_langchain.guardrails", "UiPathPIIDetectionMiddleware"),
        "UiPathPIIDetectionMiddleware is not imported from uipath_langchain.guardrails",
    )
    print("OK: UiPathPIIDetectionMiddleware imported from uipath_langchain.guardrails")

    pii_calls = [c for c in wired_middleware_calls(bindings) if call_name(c) == "UiPathPIIDetectionMiddleware"]
    check(
        pii_calls,
        "UiPathPIIDetectionMiddleware not spread with * into create_agent(middleware=[...]) "
        "(accepts inline `[*UiPathPIIDetectionMiddleware(...)]` or a variable "
        "`m = UiPathPIIDetectionMiddleware(...); middleware=[*m]`)",
    )
    print("OK: UiPathPIIDetectionMiddleware spread with * into create_agent(middleware=[...])")

    def scopes(c: ast.Call) -> set[str]:
        return enum_values(call_arg(c, "scopes"), "GuardrailScope", bindings)

    agent_calls = [c for c in pii_calls if "Agent" in scopes(c)]
    check(agent_calls, "no wired UiPathPIIDetectionMiddleware with GuardrailScope.AGENT in scopes")
    print("OK: Agent scope configured")

    tool_calls = [c for c in pii_calls if "Tool" in scopes(c) and lists_tool(call_arg(c, "tools"), TOOL, bindings)]
    check(tool_calls, f"no wired UiPathPIIDetectionMiddleware with GuardrailScope.TOOL in scopes and tools=[{TOOL}]")
    print(f"OK: Tool scope configured on {TOOL}")

    for c in pii_calls:
        action = bindings.resolve(call_arg(c, "action"))
        check(
            isinstance(action, ast.Call) and call_name(action) == "LogAction",
            f"expected a log (not block) action for PII detection, got action={ast.unparse(action) if action is not None else None}",
        )
    print("OK: LogAction used")

    entities = set().union(*(entity_values(c, bindings) for c in pii_calls))
    for member, value in REQUIRED_ENTITIES.items():
        check(
            value in entities,
            f"PIIDetectionEntityType.{member} is not in the middleware entities (found: {sorted(entities)})",
        )
    print("OK: EMAIL and PHONE_NUMBER entities configured")

    require_attachment_input(tree)
    require_rendered_attachments(tree)

    for c in pii_calls:
        value = detection_scope_value(call_arg(c, "detection_scope"), bindings)
        check(
            value is None or value in DETECTION_SCOPE_VALUES,
            f"detection_scope must be DetectionScope.TEXT/FILES/BOTH or exactly {', '.join(DETECTION_SCOPE_VALUES)}; got {value!r}",
        )
    with_scope = [c for c in agent_calls if call_arg(c, "detection_scope") is not None]
    agent_call = with_scope[0] if with_scope else agent_calls[0]
    check(
        enum_value(call_arg(agent_call, "stage"), "GuardrailExecutionStage", bindings) != "post",
        "the Agent-scope PII middleware runs at POST only, so it never reads the uploaded statement",
    )
    require_detection_scope(
        agent_call,
        "Both",
        bindings,
        "the user asked for both the typed text and the uploaded statement",
    )

    print("OK: PII middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
