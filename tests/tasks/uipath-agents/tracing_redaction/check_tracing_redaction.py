#!/usr/bin/env python3
"""@traced redaction check.

Walks `main.py` with the AST and asserts that the `main` function
carries a `@traced(...)` decorator whose keyword arguments include
ALL THREE of `name`, `input_processor`, and `output_processor`. This
is the only configuration that simultaneously labels the span and
redacts both directions.

The check explicitly rejects `hide_input=True` / `hide_output=True`
on the same call site — the prompt asks for processors specifically,
because the skill recommends processors over `hide_*` flags (you keep
partial visibility into non-sensitive fields).
"""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("credential-validator")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _decorator_call(deco: ast.expr) -> ast.Call | None:
    """Return the Call node if the decorator looks like `@traced(...)`."""
    if not isinstance(deco, ast.Call):
        return None
    func = deco.func
    if isinstance(func, ast.Name) and func.id == "traced":
        return deco
    if isinstance(func, ast.Attribute) and func.attr == "traced":
        return deco
    return None


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    main_py = ROOT / "main.py"
    text = _read_text(main_py)
    if "from uipath.tracing import traced" not in text:
        sys.exit("FAIL: main.py must import `traced` via `from uipath.tracing import traced`")
    print("OK: main.py imports `traced` from uipath.tracing")
    tree = ast.parse(text, filename=str(main_py))
    main_func: ast.AsyncFunctionDef | ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)) and node.name == "main":
            main_func = node
            break
    if main_func is None:
        sys.exit("FAIL: no `main` function found in main.py")
    decorated_calls: list[ast.Call] = []
    for deco in main_func.decorator_list:
        call = _decorator_call(deco)
        if call is not None:
            decorated_calls.append(call)
    if not decorated_calls:
        sys.exit(
            "FAIL: `main` is not decorated with `@traced(...)` (must be the "
            "*call form* — `@traced` without parentheses cannot pass kwargs)."
        )
    if len(decorated_calls) > 1:
        sys.exit(f"FAIL: `main` has {len(decorated_calls)} `@traced(...)` decorators; expected 1")
    call = decorated_calls[0]
    kwargs = {kw.arg: kw for kw in call.keywords if kw.arg is not None}
    for required in ("name", "input_processor", "output_processor"):
        if required not in kwargs:
            sys.exit(
                f"FAIL: `@traced(...)` on `main` is missing required kwarg "
                f"`{required}=`. Got kwargs: {sorted(kwargs)}"
            )
    print("OK: `@traced(...)` on `main` carries name + input_processor + output_processor")
    for forbidden in ("hide_input", "hide_output"):
        if forbidden in kwargs:
            kw = kwargs[forbidden]
            value = kw.value
            if isinstance(value, ast.Constant) and value.value is True:
                sys.exit(
                    f"FAIL: `@traced(...)` sets `{forbidden}=True` alongside "
                    "input/output processors. The skill recommends processors "
                    "over `hide_*` so partial visibility is preserved — pick one."
                )
    print("OK: no conflicting `hide_input=True` / `hide_output=True` on the same decorator")


if __name__ == "__main__":
    main()
