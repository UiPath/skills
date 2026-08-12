#!/usr/bin/env python3
"""Check that a BYOG decorator guardrail was correctly added to graph.py.

Validates:
- graph.py still parses as Python
- A @guardrail(validator=ByoValidator(...), action=BlockAction(...)) decorator
- ByoValidator is pinned to the tenant's configuration by validator name
  ("byog-smoke-agent-pin") — the point of the test. The name is the first
  positional parameter, but accept the keyword form too since the SDK signature
  is positional-or-keyword.
- The decorated target is a real factory in the fixture (create_support_agent or
  create_llm). Decorating a plain helper silently no-ops at runtime (Rules 4/5).
- ByoValidator is imported from uipath_langchain.guardrails, not
  uipath.platform.guardrails. Both re-export the same class — ByoValidator is
  genuinely a core class — but only the adapter import registers the LangChain
  adapter, so the platform import type-checks and then silently no-ops (Rule 8).

Local AST helpers mirror check_deterministic.py; _shared only exports the
middleware-spread helpers.
"""

import ast
import sys
from pathlib import Path

GRAPH = Path("graph.py")

VALIDATOR = "ByoValidator"
VALIDATOR_NAME = "byog-smoke-agent-pin"
# Factories the fixture actually defines; decorating anything else won't wrap.
VALID_TARGETS = {"create_support_agent", "create_llm"}


def read() -> str:
    if not GRAPH.is_file():
        sys.exit(f"FAIL: {GRAPH} not found in {Path.cwd()}")
    return GRAPH.read_text()


def check(condition: bool, msg: str) -> None:
    if not condition:
        sys.exit(f"FAIL: {msg}")


def call_name(call: ast.Call) -> str | None:
    fn = call.func
    if isinstance(fn, ast.Attribute):
        return fn.attr
    if isinstance(fn, ast.Name):
        return fn.id
    return None


def keyword(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def positional_or_keyword(call: ast.Call, index: int, name: str) -> ast.expr | None:
    """A parameter passed either positionally at *index* or by keyword *name*."""
    if len(call.args) > index:
        return call.args[index]
    return keyword(call, name)


def is_call(node: ast.expr | None, name: str) -> bool:
    return isinstance(node, ast.Call) and call_name(node) == name


def const_str(node: ast.expr | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def resolve_validator(node: ast.expr | None, assigns: dict) -> ast.Call | None:
    """The ByoValidator call, inline or via a one-level variable assignment."""
    if is_call(node, VALIDATOR):
        assert isinstance(node, ast.Call)
        return node
    if isinstance(node, ast.Name):
        target = assigns.get(node.id)
        if is_call(target, VALIDATOR):
            return target
    return None


def imported_from(tree: ast.AST, symbol: str) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                if alias.name == symbol:
                    return node.module
    return None


def main() -> None:
    src = read()
    try:
        tree = ast.parse(src, filename=str(GRAPH))
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph.py no longer parses as Python: {exc}")

    assigns: dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigns[target.id] = node.value

    # --- find @guardrail decorators wrapping a ByoValidator ---
    found: list[tuple[str, ast.Call, ast.Call]] = []  # (target fn, decorator, validator)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call) or call_name(dec) != "guardrail":
                continue
            validator = resolve_validator(keyword(dec, "validator"), assigns)
            if validator is not None:
                found.append((node.name, dec, validator))

    if not found:
        any_guardrail = any(
            isinstance(n, ast.Call) and call_name(n) == "guardrail"
            for n in ast.walk(tree)
        )
        check(
            False,
            f"no @guardrail(validator={VALIDATOR}(...)) decorator found"
            + (
                " — a @guardrail decorator exists but its validator is not "
                f"{VALIDATOR}; the built-in validator was likely used instead"
                if any_guardrail
                else f" ({VALIDATOR} is never wired)"
            ),
        )
    print(f"OK: @guardrail with {VALIDATOR} found")

    # --- pinned to the seeded BYOG configuration (the point of the test) ---
    pinned = [
        (fn, dec, v)
        for (fn, dec, v) in found
        if const_str(positional_or_keyword(v, 0, "validator_name")) == VALIDATOR_NAME
    ]
    if not pinned:
        seen = [
            const_str(positional_or_keyword(v, 0, "validator_name"))
            for (_, _, v) in found
        ]
        check(
            False,
            f"no {VALIDATOR} pinned to the tenant's BYOG configuration. Expected "
            f'validator name "{VALIDATOR_NAME}", got: {seen}',
        )
    target_fn, decorator, _ = pinned[0]
    print(f'OK: pinned to the BYOG configuration ("{VALIDATOR_NAME}")')

    # --- block action ---
    check(
        is_call(keyword(decorator, "action"), "BlockAction"),
        "action=BlockAction(...) not found on the @guardrail decorator — the user "
        "asked to block on violations",
    )
    print("OK: action=BlockAction(...)")

    # --- decorating something that actually gets wrapped ---
    check(
        target_fn in VALID_TARGETS,
        f"@guardrail is on {target_fn!r}, which is not a factory the runtime wraps. "
        f"Decorate one of {sorted(VALID_TARGETS)} — an agent/LLM factory — or the "
        "guardrail silently no-ops",
    )
    print(f"OK: decorates {target_fn}() (a real factory)")

    # --- adapter import (Rule 8) ---
    module = imported_from(tree, VALIDATOR)
    check(module is not None, f"{VALIDATOR} is used but never imported")
    check(
        module == "uipath_langchain.guardrails",
        f"{VALIDATOR} imported from {module!r} — it is a core class, so that import "
        "type-checks, but a LangChain agent must import from "
        "'uipath_langchain.guardrails' so the adapter registers; otherwise the "
        "guardrail silently no-ops",
    )
    print("OK: imported from uipath_langchain.guardrails")

    print("OK: BYOG decorator guardrail correctly added to graph.py")


if __name__ == "__main__":
    main()
