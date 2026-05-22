#!/usr/bin/env python3
"""HITL coded-agent shape check.

Asserts the primitives that together make
`interrupt(CreateEscalation)` work end-to-end:

  1. `main.py` imports `interrupt` from `langgraph.types`.
  2. `main.py` imports `CreateEscalation` from
     `uipath.platform.common` and references it inside `interrupt(...)`.
     The prompt is an explicit escalation — the skill prescribes
     `CreateEscalation` for that path (`CreateTask` is the general
     form for non-escalation HITL).
  3. `bindings.json` declares the `app` resource for the Action
     Center app the escalation targets — `app_name=ExpenseReview`,
     `app_folder_path=Finance`. Without this binding,
     `uipath push` would not create the virtual placeholder.

Also runs the lazy-LLM-init AST scan as a hygiene check.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("expense-approver")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import (  # noqa: E402
    load_bindings,
    find_resource,
    assert_value_field,
    assert_metadata_field,
)
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def find_graph_module() -> Path:
    for candidate in ("main.py", "graph.py"):
        path = ROOT / candidate
        if path.is_file():
            return path
    sys.exit(f"FAIL: neither main.py nor graph.py found under {ROOT}")


def _module_constants(tree: ast.Module) -> dict[str, object]:
    """Collect module-level `<Name> = <Constant>` assignments.

    Resolves the common pattern where the agent extracts string literals
    into constants (e.g. ``ACTION_CENTER_APP = "ExpenseReview"``).
    """
    consts: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value.value
    return consts


def _resolve_kwarg(value: ast.expr, consts: dict[str, object]) -> object | None:
    if isinstance(value, ast.Constant):
        return value.value
    if isinstance(value, ast.Name) and value.id in consts:
        return consts[value.id]
    return None


def _find_create_escalation_call(tree: ast.Module) -> ast.Call | None:
    """Return the inner `CreateEscalation(...)` call wrapped by `interrupt(...)`."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "interrupt"):
            continue
        if not node.args:
            continue
        inner = node.args[0]
        if not isinstance(inner, ast.Call):
            continue
        inner_func = inner.func
        if isinstance(inner_func, ast.Name) and inner_func.id == "CreateEscalation":
            return inner
    return None


def check_imports_and_calls(text: str, tree: ast.Module) -> None:
    if not re.search(r"from\s+langgraph\.types\s+import\s+[^\n]*\binterrupt\b", text):
        sys.exit("FAIL: missing `from langgraph.types import interrupt`")
    print("OK: imports `interrupt` from langgraph.types")
    if not re.search(r"from\s+uipath\.platform\.common\s+import\s+[^\n]*\bCreateEscalation\b", text):
        sys.exit(
            "FAIL: missing `from uipath.platform.common import CreateEscalation`. "
            "The prompt describes an explicit escalation — the skill prescribes "
            "`CreateEscalation` for that path."
        )
    print("OK: imports CreateEscalation from uipath.platform.common")
    call = _find_create_escalation_call(tree)
    if call is None:
        sys.exit("FAIL: no `interrupt(CreateEscalation(...))` call site found")
    print("OK: graph node calls interrupt(CreateEscalation(...))")
    consts = _module_constants(tree)
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}
    expected = {"app_name": "ExpenseReview", "app_folder_path": "Finance"}
    for kw, want in expected.items():
        if kw not in kwargs:
            sys.exit(f'FAIL: `CreateEscalation(...)` is missing `{kw}=`')
        got = _resolve_kwarg(kwargs[kw], consts)
        if got != want:
            sys.exit(
                f'FAIL: `CreateEscalation({kw}=...)` resolves to {got!r}, expected {want!r}.'
            )
    print('OK: escalation targets app_name="ExpenseReview" / app_folder_path="Finance"')


def check_app_binding() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="app", key="ExpenseReview.Finance")
    assert_value_field(entry, field="name", expected="ExpenseReview")
    assert_value_field(entry, field="folderPath", expected="Finance")
    assert_metadata_field(entry, field="ActivityName", expected="create_async")
    assert_metadata_field(entry, field="DisplayLabel", expected="ExpenseReview")
    print("OK: bindings.json declares the ExpenseReview/Finance `app` resource")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)
    tree = ast.parse(text, filename=str(module))
    check_imports_and_calls(text, tree)
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")
    check_app_binding()


if __name__ == "__main__":
    main()
