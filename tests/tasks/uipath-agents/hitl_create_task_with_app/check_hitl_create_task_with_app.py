#!/usr/bin/env python3
"""HITL `interrupt(CreateTask)` shape check — regular Action Center task (NOT escalation).

Asserts:
  1. `main.py` imports `interrupt` from `langgraph.types`.
  2. `main.py` imports `CreateTask` from `uipath.platform.common`.
  3. At least one `interrupt(CreateTask(...))` call site exists.
  4. The `CreateTask` call targets `app_name="RefundReview"`,
     `app_folder_path="Compliance"`.
  5. `main.py` does NOT use `CreateEscalation` (that's a different pattern
     covered by hitl_create_task — keep them disjoint).
  6. `bindings.json` declares the `app` resource for `RefundReview` /
     `Compliance`.
  7. A top-level `graph =` variable is exported.
  8. No module-level UiPath* construction (Critical Rule C4).
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.bindings_assertions import (  # noqa: E402
    load_bindings,
    find_resource,
    assert_value_field,
    assert_metadata_field,
)

ROOT = find_project_root("refund-gate")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_graph_module() -> Path:
    for candidate in ("main.py", "graph.py"):
        path = ROOT / candidate
        if path.is_file():
            return path
    fail(f"neither main.py nor graph.py found under {ROOT}")
    raise SystemExit(1)


def module_constants(tree: ast.Module) -> dict[str, object]:
    consts: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value.value
    return consts


def resolve_kwarg(value: ast.expr, consts: dict[str, object]) -> object | None:
    if isinstance(value, ast.Constant):
        return value.value
    if isinstance(value, ast.Name) and value.id in consts:
        return consts[value.id]
    return None


def find_create_task_call(tree: ast.Module) -> ast.Call | None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "interrupt"):
            continue
        if not node.args:
            continue
        inner = node.args[0]
        if (
            isinstance(inner, ast.Call)
            and isinstance(inner.func, ast.Name)
            and inner.func.id == "CreateTask"
        ):
            return inner
    return None


def main() -> None:
    if not ROOT.is_dir():
        fail(f"project directory {ROOT} does not exist")

    module = find_graph_module()
    text = module.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(module))
    except SyntaxError as exc:
        fail(f"{module} has a syntax error: {exc}")

    if not re.search(r"from\s+langgraph\.types\s+import\s+[^\n]*\binterrupt\b", text):
        fail("missing `from langgraph.types import interrupt`")
    print("OK: imports `interrupt` from langgraph.types")

    if not re.search(
        r"from\s+uipath\.platform\.common\s+import\s+[^\n]*\bCreateTask\b", text
    ):
        fail(
            "missing `from uipath.platform.common import CreateTask`. "
            "The scenario opens a new Action Center task — use `CreateTask`."
        )
    print("OK: imports CreateTask from uipath.platform.common")

    if re.search(r"\bCreateEscalation\s*\(", text):
        fail(
            "main.py invokes `CreateEscalation(...)`. The scenario is a regular "
            "compliance review, not an escalation. Use `CreateTask` only."
        )
    print("OK: no CreateEscalation usage (scenario is the regular task pattern)")

    call = find_create_task_call(tree)
    if call is None:
        fail("no `interrupt(CreateTask(...))` call site found")

    consts = module_constants(tree)
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}
    expected = {"app_name": "RefundReview", "app_folder_path": "Compliance"}
    for kw, want in expected.items():
        if kw not in kwargs:
            fail(f"`CreateTask(...)` is missing `{kw}=`")
        got = resolve_kwarg(kwargs[kw], consts)
        if got != want:
            fail(f"`CreateTask({kw}=...)` resolves to {got!r}, expected {want!r}")
    print(
        'OK: CreateTask targets app_name="RefundReview" / app_folder_path="Compliance"'
    )

    if not re.search(r"^\s*graph\s*=\s*", text, re.M):
        fail("main.py does not export a top-level `graph =` variable")
    print("OK: top-level `graph` variable exported")

    violations = find_module_level_llm_clients(module)
    if violations:
        fail("module-level UiPath* construction (C4): " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")

    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="app", key="RefundReview.Compliance")
    assert_value_field(entry, field="name", expected="RefundReview")
    assert_value_field(entry, field="folderPath", expected="Compliance")
    assert_metadata_field(entry, field="ActivityName", expected="create_async")
    assert_metadata_field(entry, field="DisplayLabel", expected="RefundReview")
    print("OK: bindings.json declares the RefundReview/Compliance `app` resource")


if __name__ == "__main__":
    main()
