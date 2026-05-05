#!/usr/bin/env python3
"""Process-invocation coded-agent shape check.

Asserts:
  1. ``main.py`` imports ``interrupt`` from ``langgraph.types`` and
     ``InvokeProcess`` from ``uipath.platform.common``.
  2. A graph node calls ``interrupt(InvokeProcess(...))`` whose
     ``name=`` and ``process_folder_path=`` resolve (through any
     module-level constant the agent extracted) to ``DataScraper``
     and ``Workflows``.
  3. ``bindings.json`` declares the ``process`` resource for
     DataScraper / Workflows with ``ActivityName=invoke_async``.
  4. No module-level UiPath* construction.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("data-orchestrator")

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
    consts: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value.value
    return consts


def _resolve(value: ast.expr, consts: dict[str, object]) -> object | None:
    if isinstance(value, ast.Constant):
        return value.value
    if isinstance(value, ast.Name) and value.id in consts:
        return consts[value.id]
    return None


def _kwarg(call: ast.Call, name: str) -> ast.expr | None:
    for kw in call.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _find_invoke_process_call(tree: ast.Module) -> ast.Call | None:
    """Return the inner ``InvokeProcess(...)`` call wrapped by ``interrupt(...)``."""
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
        if isinstance(inner_func, ast.Name) and inner_func.id == "InvokeProcess":
            return inner
    return None


def check_invocation(text: str, tree: ast.Module) -> None:
    if not re.search(r"from\s+langgraph\.types\s+import\s+[^\n]*\binterrupt\b", text):
        sys.exit("FAIL: missing `from langgraph.types import interrupt`")
    if not re.search(
        r"from\s+uipath\.platform\.common\s+import\s+[^\n]*\bInvokeProcess\b",
        text,
    ):
        sys.exit("FAIL: missing `from uipath.platform.common import InvokeProcess`")

    call = _find_invoke_process_call(tree)
    if call is None:
        sys.exit("FAIL: no `interrupt(InvokeProcess(...))` call site found")

    consts = _module_constants(tree)
    expected = {"name": "DataScraper", "process_folder_path": "Workflows"}
    for kw, want in expected.items():
        node = _kwarg(call, kw)
        if node is None:
            sys.exit(f"FAIL: `InvokeProcess(...)` is missing `{kw}=`")
        got = _resolve(node, consts)
        if got != want:
            sys.exit(
                f"FAIL: `InvokeProcess({kw}=...)` resolves to {got!r}, expected {want!r}."
            )
    print(
        'OK: graph node calls `interrupt(InvokeProcess(name="DataScraper", '
        'process_folder_path="Workflows", ...))`'
    )


def check_process_binding() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="process", key="DataScraper.Workflows")
    assert_value_field(entry, field="name", expected="DataScraper")
    assert_value_field(entry, field="folderPath", expected="Workflows")
    assert_metadata_field(entry, field="ActivityName", expected="invoke_async")
    print("OK: bindings.json declares the DataScraper/Workflows `process` resource")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)
    tree = ast.parse(text, filename=str(module))
    check_invocation(text, tree)
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")
    check_process_binding()


if __name__ == "__main__":
    main()
