#!/usr/bin/env python3
"""Check that a user prompt attacks decorator guardrail was correctly added to graph.py.

Validates:
- guardrail and UserPromptAttacksValidator imported from uipath_langchain.guardrails
- a @guardrail(validator=UserPromptAttacksValidator(...)) decorates the LLM factory
  (a function, not a @tool, that returns a chat model and is called)
- that decorator runs at GuardrailExecutionStage.PRE (user prompt attacks is PRE-only)
  and blocks (action=BlockAction(...))
- No middleware spread pattern (*UiPathUserPromptAttacksMiddleware) — must be decorator style
- The Input model declares an Attachment field and render_attachments_block puts it
  into the user message (the uploaded document)
- the decorator sets detection_scope to Both
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from _shared.guardrails.coded_file_guardrail_assertions import (
    imported_from,
    module_constants,
    require_attachment_input,
    require_detection_scope,
    require_rendered_attachments,
)
from _shared.guardrails.guardrail_middleware import call_kwarg, call_name, spread_middleware_calls

GRAPH = Path("graph.py")
LANGCHAIN_GUARDRAILS = "uipath_langchain.guardrails"


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


def returns_chat_model(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    local = {
        target.id: node.value
        for node in ast.walk(fn)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    for node in ast.walk(fn):
        if isinstance(node, ast.Return):
            value = local.get(node.value.id) if isinstance(node.value, ast.Name) else node.value
            if isinstance(value, ast.Call) and "Chat" in (call_name(value) or ""):
                return True
    return False


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")
    consts = module_constants(tree)

    for symbol in ("guardrail", "UserPromptAttacksValidator"):
        check(imported_from(tree, LANGCHAIN_GUARDRAILS, symbol), f"{symbol} is not imported from {LANGCHAIN_GUARDRAILS}")
    print(f"OK: guardrail and UserPromptAttacksValidator imported from {LANGCHAIN_GUARDRAILS}")

    guarded = [
        (fn, dec)
        for fn in ast.walk(tree)
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
        for dec in fn.decorator_list
        if isinstance(dec, ast.Call) and call_name(dec) == "guardrail"
    ]
    check(guarded, "@guardrail(...) decorator not found above any function in graph.py")
    upa = [
        (fn, dec)
        for fn, dec in guarded
        if isinstance(resolve(call_kwarg(dec, "validator"), consts), ast.Call)
        and call_name(resolve(call_kwarg(dec, "validator"), consts)) == "UserPromptAttacksValidator"
    ]
    check(upa, "no @guardrail(validator=UserPromptAttacksValidator(...)) decorating a function")
    fn, dec = upa[0]
    print(f"OK: @guardrail(validator=UserPromptAttacksValidator(...)) on {fn.name}()")

    check(
        not any(isinstance(d, (ast.Name, ast.Attribute, ast.Call)) and "tool" in ast.unparse(d) for d in fn.decorator_list if d is not dec)
        and returns_chat_model(fn)
        and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == fn.name for n in ast.walk(tree)),
        f"the user prompt attacks guardrail must decorate the LLM factory (a function that returns the chat model and is "
        f"called to build the agent's model); {fn.name}() is not one",
    )
    print(f"OK: {fn.name}() is the LLM factory")

    stage = resolve(call_kwarg(dec, "stage"), consts)
    check(
        stage is not None and ast.unparse(stage).endswith("GuardrailExecutionStage.PRE"),
        f"stage must be GuardrailExecutionStage.PRE (user prompt attacks is PRE-only), got {ast.unparse(stage) if stage is not None else 'PRE_AND_POST (default)'}",
    )
    print("OK: stage is GuardrailExecutionStage.PRE")

    action = resolve(call_kwarg(dec, "action"), consts)
    check(
        isinstance(action, ast.Call) and call_name(action) == "BlockAction",
        f"action must be BlockAction(...) — user prompt attacks should block adversarial inputs, got {ast.unparse(action) if action is not None else None}",
    )
    print("OK: action is BlockAction")

    check(
        not any(call_name(c) == "UiPathUserPromptAttacksMiddleware" for c in spread_middleware_calls(tree)),
        "Middleware spread *UiPathUserPromptAttacksMiddleware found — task requires decorator style",
    )
    print("OK: no middleware spread (decorator style confirmed)")

    require_attachment_input(tree)
    require_rendered_attachments(tree)
    require_detection_scope(
        dec,
        "Both",
        consts,
        "the user asked for both the typed text and the uploaded document",
    )

    print("OK: User prompt attacks decorator guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
