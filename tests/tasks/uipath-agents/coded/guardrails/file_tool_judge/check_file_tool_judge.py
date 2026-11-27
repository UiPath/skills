#!/usr/bin/env python3
"""Check that an LLM-as-judge guardrail on review_contract reads the uploaded file.

Accepts either flavor:
- decorator: a guardrail(validator=LLMAsJudgeValidator(...), ...) decorating
  review_contract, or applied as guardrail(...)(review_contract)
- middleware: *UiPathLLMAsJudgeMiddleware(scopes=[GuardrailScope.TOOL, ...],
  tools=[review_contract], ...)

Validates on that guardrail:
- guardrail / UiPathLLMAsJudgeMiddleware comes from uipath_langchain.guardrails
  (the skill's import rule; the middleware must also be wired into create_agent)
- detection_scope is Files (the file contents, not the tool's text arguments)
- BlockAction carrying the requested block message as its detail
- the stage includes PRE (PRE or PRE_AND_POST; POST alone runs after the tool read the file)
- guardrail_text states the 12-month non-compete rule and a real model id is passed to the judge
- the fixture's Attachment input is still rendered into the user message

Arguments are read by keyword or SDK position, names resolve in the scope where the
guardrail is built, and an enum may be a member, an alias of the enum or its value.
"""

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from _shared.guardrails.coded_file_guardrail_assertions import (
    Bindings,
    call_arg,
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
TOOL = "review_contract"
LANGCHAIN_GUARDRAILS = "uipath_langchain.guardrails"
BLOCK_MESSAGE = "Non-compete exceeds 12 months"
STAGES_WITH_PRE = ("pre", "pre&post")


def check(condition: object, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def names_tool(node: ast.expr | None) -> bool:
    return node is not None and any(isinstance(n, ast.Name) and n.id == TOOL for n in ast.walk(node))


def decorator_guardrails(tree: ast.AST) -> list[ast.Call]:
    found: list[ast.Call] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == TOOL:
            found += [d for d in node.decorator_list if isinstance(d, ast.Call) and call_name(d) == "guardrail"]
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Call)
            and call_name(node.func) == "guardrail"
            and any(names_tool(arg) for arg in node.args)
        ):
            found.append(node.func)
    return found


def middleware_guardrails(bindings: Bindings) -> list[ast.Call]:
    return [
        c
        for c in wired_middleware_calls(bindings)
        if call_name(c) == "UiPathLLMAsJudgeMiddleware"
        and "Tool" in enum_values(call_arg(c, "scopes"), "GuardrailScope", bindings)
        and lists_tool(call_arg(c, "tools"), TOOL, bindings)
    ]


def main() -> None:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    src = GRAPH.read_text()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")
    bindings = Bindings(tree)

    decorators = [
        d
        for d in decorator_guardrails(tree)
        if isinstance(validator := bindings.resolve(call_arg(d, "validator")), ast.Call)
        and call_name(validator) == "LLMAsJudgeValidator"
    ]
    middleware = middleware_guardrails(bindings)
    check(
        decorators or middleware,
        f"no LLM-as-judge guardrail targets {TOOL}: expected @guardrail(validator=LLMAsJudgeValidator(...)) on it, "
        f"or *UiPathLLMAsJudgeMiddleware(scopes=[GuardrailScope.TOOL], tools=[{TOOL}], ...)",
    )
    guard = decorators[0] if decorators else middleware[0]
    flavor = "decorator" if decorators else "middleware"
    print(f"OK: LLM-as-judge guardrail on {TOOL} ({flavor})")

    symbol = "guardrail" if decorators else "UiPathLLMAsJudgeMiddleware"
    check(
        imported_from(tree, LANGCHAIN_GUARDRAILS, symbol),
        f"{symbol} must be imported from {LANGCHAIN_GUARDRAILS} (from uipath.platform.guardrails it guards a "
        "LangChain tool only if the LangChain adapter happens to be imported elsewhere)",
    )
    print(f"OK: {symbol} imported from {LANGCHAIN_GUARDRAILS}")

    require_detection_scope(guard, "Files", bindings, "the judge must read the file contents, not the tool's text arguments")

    action = bindings.resolve(call_arg(guard, "action"))
    check(isinstance(action, ast.Call) and call_name(action) == "BlockAction", f"action must be BlockAction(...), got {ast.unparse(action) if action else None}")
    detail = bindings.resolve(call_arg(action, "detail"))
    detail_text = ast.unparse(detail) if detail is not None else ""
    check(BLOCK_MESSAGE.lower() in detail_text.lower(), f'BlockAction(detail=...) must carry "{BLOCK_MESSAGE}.", got {detail_text or None}')
    print("OK: action is BlockAction with the requested message")

    stage = call_arg(guard, "stage")
    stage_value = "pre&post" if stage is None else enum_value(stage, "GuardrailExecutionStage", bindings)
    stage_text = "PRE_AND_POST (default)" if stage is None else ast.unparse(bindings.resolve(stage) or stage)
    check(stage_value in STAGES_WITH_PRE, f"the guardrail must run before the tool reads the file (stage PRE), got {stage_text}")
    print(f"OK: stage includes PRE ({stage_text})")

    judge = bindings.resolve(call_arg(guard, "validator")) if decorators else guard
    rule = bindings.resolve(call_arg(judge, "guardrail_text"))
    if isinstance(rule, ast.Constant) and isinstance(rule.value, str):
        rule_text = rule.value
    else:
        rule_text = ast.unparse(rule) if isinstance(rule, (ast.JoinedStr, ast.BinOp)) else ""
    check(
        "compete" in rule_text.lower() and "12" in rule_text,
        f"guardrail_text must state the non-compete rule and its 12-month limit for the judge, got {rule_text!r}",
    )
    model = bindings.resolve(call_arg(judge, "model"))
    check(model is not None, "model= is missing on the judge")
    check(
        not (isinstance(model, ast.Constant) and (not model.value or "<" in str(model.value))),
        f"model= must be a judge model id from `uip agent guardrails llm-as-judge-models`, got {ast.unparse(model)}",
    )
    print("OK: judge has guardrail_text and model")

    require_attachment_input(tree)
    require_rendered_attachments(tree)

    print(f"OK: LLM-as-judge file guardrail on {TOOL} is correct")


if __name__ == "__main__":
    main()
