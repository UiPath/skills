#!/usr/bin/env python3
"""HITL `interrupt(WaitTask)` shape check.

This is the "wait on a task that already exists" pattern, distinct from
`CreateTask` / `CreateEscalation` (which open a new task). Asserts:

  1. `main.py` imports `interrupt` from `langgraph.types`.
  2. `main.py` imports `WaitTask` from `uipath.platform.common`.
  3. At least one `interrupt(WaitTask(...))` call exists.
  4. `main.py` does NOT use `CreateTask` / `CreateEscalation` — the
     scenario is monitoring an existing task, not creating one.
  5. A top-level `graph =` variable is exported (LangGraph entrypoint).
  6. No module-level UiPath* client construction (Critical Rule C4).
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

ROOT = find_project_root("purchase-gate")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_graph_module() -> Path:
    for candidate in ("main.py", "graph.py"):
        path = ROOT / candidate
        if path.is_file():
            return path
    fail(f"neither main.py nor graph.py found under {ROOT}")
    raise SystemExit(1)  # unreachable, for type checkers


def has_interrupt_wait_task(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "interrupt"):
            continue
        if not node.args:
            continue
        inner = node.args[0]
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "WaitTask":
            return True
    return False


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

    if not re.search(r"from\s+uipath\.platform\.common\s+import\s+[^\n]*\bWaitTask\b", text):
        fail(
            "missing `from uipath.platform.common import WaitTask`. "
            "The scenario is `WaitTask` (wait on an existing Action Center task), "
            "not `CreateTask` (which opens a new one)."
        )
    print("OK: imports WaitTask from uipath.platform.common")

    if not has_interrupt_wait_task(tree):
        fail(
            "no `interrupt(WaitTask(...))` call site found. "
            "The agent must pause on the existing task via `interrupt(WaitTask(action=...))`."
        )
    print("OK: graph node calls interrupt(WaitTask(...))")

    if re.search(r"\bCreateTask\s*\(", text) or re.search(r"\bCreateEscalation\s*\(", text):
        fail(
            "main.py invokes `CreateTask(...)` or `CreateEscalation(...)`. "
            "Those open a NEW Action Center task — the scenario is monitoring an "
            "ALREADY-CREATED task via `WaitTask`. Use `WaitTask` only."
        )
    print("OK: no CreateTask / CreateEscalation usage (scenario is monitor-existing-task)")

    if not re.search(r"^\s*graph\s*=\s*", text, re.M):
        fail("main.py does not export a top-level `graph =` variable")
    print("OK: top-level `graph` variable exported")

    violations = find_module_level_llm_clients(module)
    if violations:
        fail("module-level UiPath* construction (C4): " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")

    print("OK: WaitTask HITL shape verified")


if __name__ == "__main__":
    main()
