#!/usr/bin/env python3
"""Check that a PII detection middleware guardrail was correctly added to graph.py.

Validates:
- UiPathPIIDetectionMiddleware is imported from uipath_langchain.guardrails
- The middleware is spread (*) into create_agent(middleware=[...]), inline or through a variable
- One wired entry covers Agent scope (GuardrailScope.AGENT) and does not run at POST only
- One wired entry covers Tool scope (GuardrailScope.TOOL) with tools=[lookup_account_info]
- Every wired PII entry logs (action=LogAction(...)), not blocks
- The entities cover PIIDetectionEntityType.EMAIL and PIIDetectionEntityType.PHONE_NUMBER
- The Input model declares an Attachment field and render_attachments_block puts it
  into the user message (the uploaded statement)
- The Agent-scope entry sets detection_scope to Both (text and file); any other
  detection_scope is a valid value
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.coded_file_guardrail_assertions import (
    DETECTION_SCOPE_VALUES,
    detection_scope_value,
    imported_from,
    module_constants,
    require_attachment_input,
    require_detection_scope,
    require_rendered_attachments,
    wired_middleware_calls,
)
from _shared.guardrail_middleware import call_kwarg, call_name

GRAPH = Path("graph.py")
TOOL = "lookup_account_info"


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def check(condition: object, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def resolve(node: ast.expr | None, consts: dict[str, ast.expr]) -> ast.expr | None:
    seen = 0
    while isinstance(node, ast.Name) and node.id in consts and seen < 5:
        node = consts[node.id]
        seen += 1
    return node


def resolved_text(node: ast.expr | None, consts: dict[str, ast.expr]) -> str:
    node = resolve(node, consts)
    return ast.unparse(node) if node is not None else ""


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")
    consts = module_constants(tree)

    check(
        imported_from(tree, "uipath_langchain.guardrails", "UiPathPIIDetectionMiddleware"),
        "UiPathPIIDetectionMiddleware is not imported from uipath_langchain.guardrails",
    )
    print("OK: UiPathPIIDetectionMiddleware imported from uipath_langchain.guardrails")

    pii_calls = [c for c in wired_middleware_calls(tree) if call_name(c) == "UiPathPIIDetectionMiddleware"]
    check(
        pii_calls,
        "UiPathPIIDetectionMiddleware not spread with * into create_agent(middleware=[...]) "
        "(accepts inline `[*UiPathPIIDetectionMiddleware(...)]` or a variable "
        "`m = UiPathPIIDetectionMiddleware(...); middleware=[*m]`)",
    )
    print("OK: UiPathPIIDetectionMiddleware spread with * into create_agent(middleware=[...])")

    def scopes(c: ast.Call) -> str:
        return resolved_text(call_kwarg(c, "scopes") or (c.args[0] if c.args else None), consts)

    agent_calls = [c for c in pii_calls if "GuardrailScope.AGENT" in scopes(c)]
    check(agent_calls, "no wired UiPathPIIDetectionMiddleware with GuardrailScope.AGENT in scopes")
    print("OK: Agent scope configured")

    tool_calls = [c for c in pii_calls if "GuardrailScope.TOOL" in scopes(c) and TOOL in resolved_text(call_kwarg(c, "tools"), consts)]
    check(tool_calls, f"no wired UiPathPIIDetectionMiddleware with GuardrailScope.TOOL in scopes and tools=[{TOOL}]")
    print(f"OK: Tool scope configured on {TOOL}")

    for c in pii_calls:
        action = resolve(call_kwarg(c, "action"), consts)
        check(
            isinstance(action, ast.Call) and call_name(action) == "LogAction",
            f"expected a log (not block) action for PII detection, got action={ast.unparse(action) if action is not None else None}",
        )
    print("OK: LogAction used")

    entities = " ".join(resolved_text(call_kwarg(c, "entities"), consts) for c in pii_calls)
    for entity in ("EMAIL", "PHONE_NUMBER"):
        check(f"PIIDetectionEntityType.{entity}" in entities, f"PIIDetectionEntityType.{entity} is not in the middleware entities")
    print("OK: EMAIL and PHONE_NUMBER entities configured")

    require_attachment_input(tree)
    require_rendered_attachments(tree)

    for c in pii_calls:
        value = detection_scope_value(call_kwarg(c, "detection_scope"), consts)
        check(
            value is None or value in DETECTION_SCOPE_VALUES,
            f"detection_scope must be DetectionScope.TEXT/FILES/BOTH or exactly {', '.join(DETECTION_SCOPE_VALUES)}; got {value!r}",
        )
    with_scope = [c for c in agent_calls if "detection_scope" in {kw.arg for kw in c.keywords}]
    agent_call = with_scope[0] if with_scope else agent_calls[0]
    stage = resolved_text(call_kwarg(agent_call, "stage"), consts)
    check(
        not stage.endswith("GuardrailExecutionStage.POST"),
        "the Agent-scope PII middleware runs at POST only, so it never reads the uploaded statement",
    )
    require_detection_scope(
        agent_call,
        "Both",
        consts,
        "the user asked for both the typed text and the uploaded statement",
    )

    print("OK: PII middleware guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
