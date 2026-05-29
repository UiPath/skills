#!/usr/bin/env python3
"""Coded guardrail validation/fix check — SimpleCodedAgent.

Asserts the skill detected and fixed the misconfigured guardrail:
  - graph.py still parses as Python (ast.parse)
  - UserPromptAttacksValidator is still referenced in graph.py
  - No @guardrail directly above @tool def lookup_account_info uses
    UserPromptAttacksValidator (the original misuse) — LLM-scope-only validator
    on a @tool is forbidden.
  - A @guardrail decorator using UserPromptAttacksValidator now appears above a
    function definition that returns a UiPathChat(...) — i.e. the LLM factory.
"""

import ast
import sys
from pathlib import Path

GRAPH = Path("graph.py")
TARGET_TOOL = "lookup_account_info"


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def deco_name(deco: ast.expr) -> str | None:
    if isinstance(deco, ast.Call):
        target = deco.func
    else:
        target = deco
    if isinstance(target, ast.Name):
        return target.id
    if isinstance(target, ast.Attribute):
        return target.attr
    return None


def is_user_prompt_attacks_guardrail(deco: ast.expr) -> bool:
    """True iff this is `@guardrail(validator=UserPromptAttacksValidator(...), ...)`."""
    if not isinstance(deco, ast.Call):
        return False
    if deco_name(deco) != "guardrail":
        return False
    for kw in deco.keywords:
        if kw.arg == "validator" and isinstance(kw.value, ast.Call):
            if deco_name(kw.value) == "UserPromptAttacksValidator":
                return True
    return False


def returns_uipath_chat(func: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
            if deco_name(node.value) == "UiPathChat":
                return True
    return False


def main() -> None:
    src = read()

    # 1. Syntactic
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {e}")
    print("OK: graph.py parses as valid Python")

    # 2. UserPromptAttacksValidator still referenced
    if "UserPromptAttacksValidator" not in src:
        sys.exit(
            "FAIL: UserPromptAttacksValidator no longer referenced — the guardrail was "
            "removed entirely instead of being moved to the LLM factory"
        )
    print("OK: UserPromptAttacksValidator still referenced")

    # 3. Misuse must be gone: no FunctionDef named lookup_account_info with both a
    #    @tool decorator and a @guardrail(UserPromptAttacksValidator(...)) decorator.
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name != TARGET_TOOL:
            continue
        has_tool = any(deco_name(d) == "tool" for d in node.decorator_list)
        has_upa_guard = any(
            is_user_prompt_attacks_guardrail(d) for d in node.decorator_list
        )
        if has_tool and has_upa_guard:
            sys.exit(
                "FAIL: @guardrail(UserPromptAttacksValidator(...)) still decorates "
                f"@tool def {TARGET_TOOL} — user_prompt_attacks is LLM-scope only and "
                "must not decorate a @tool. Move it above the LLM factory function."
            )
    print(f"OK: no UserPromptAttacksValidator @guardrail above @tool def {TARGET_TOOL}")

    # 4. UserPromptAttacksValidator @guardrail now sits above a function that returns
    #    UiPathChat(...) — i.e. the LLM factory.
    llm_factory_decorated = False
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not any(is_user_prompt_attacks_guardrail(d) for d in node.decorator_list):
            continue
        if returns_uipath_chat(node):
            llm_factory_decorated = True
            print(
                f"OK: @guardrail(UserPromptAttacksValidator(...)) above LLM "
                f"factory `{node.name}` returning UiPathChat(...)"
            )
            break

    if not llm_factory_decorated:
        sys.exit(
            "FAIL: no function decorated with @guardrail(UserPromptAttacksValidator(...)) "
            "returns UiPathChat(...). The validator must be moved to the LLM factory."
        )

    print("OK: coded validate-and-fix check passed")


if __name__ == "__main__":
    main()
