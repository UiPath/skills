#!/usr/bin/env python3
"""HITL `interrupt(WaitTask)` / `interrupt(WaitEscalation)` shape check.

This is the "wait on a task that already exists" pattern, distinct from
`CreateTask` / `CreateEscalation` (which open a new task). Both wait
classes are accepted: `WaitEscalation` subclasses `WaitTask` in the SDK
(same fields, same `action=` target); they differ only in the resume
payload (`WaitTask` -> task `data`, `WaitEscalation` -> full `Task` incl.
`action`). The prompt asks the agent to read the reviewer's decision,
which either class can serve, so the choice is not graded. Asserts:

  1. `main.py` imports `interrupt` from `langgraph.types`.
  2. `main.py` imports `WaitTask` or `WaitEscalation` from
     `uipath.platform.common`.
  3. At least one `interrupt(WaitTask(...))` or
     `interrupt(WaitEscalation(...))` call exists.
  4. `main.py` does NOT use `CreateTask` / `CreateEscalation` — the
     scenario is monitoring an existing task, not creating one.
  5. A top-level `graph =` variable is exported (LangGraph entrypoint).
  6. `langgraph.json` exists at the resolved project root and points at
     the exported graph.
  7. No module-level UiPath* client construction (Critical Rule C4).
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

_shared_root = (
    os.path.join(os.environ["SKILLS_REPO_PATH"], "tests", "tasks", "uipath-agents")
    if os.environ.get("SKILLS_REPO_PATH")
    else os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, _shared_root)
from _shared.project_root import find_project_root  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.langgraph_assertions import assert_langgraph_config  # noqa: E402

ROOT = find_project_root("purchase-gate")

# `WaitEscalation` is a subclass of `WaitTask` (uipath.platform.common);
# either is a valid "wait on an existing task" interrupt.
WAIT_CLASSES = ("WaitTask", "WaitEscalation")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_graph_module() -> Path:
    for candidate in ("main.py", "graph.py"):
        path = ROOT / candidate
        if path.is_file():
            return path
    fail(f"neither main.py nor graph.py found under {ROOT}")
    raise SystemExit(1)  # unreachable, for type checkers


def find_interrupt_wait_class(tree: ast.Module) -> str | None:
    """Return the wait class name used inside `interrupt(...)`, if any."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "interrupt"):
            continue
        if not node.args:
            continue
        inner = node.args[0]
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id in WAIT_CLASSES:
            return inner.func.id
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

    if not re.search(r"from\s+langgraph\.types\s+import\s+(?:[^\n]*\binterrupt\b|\([^)]*\binterrupt\b)", text):
        fail("missing `from langgraph.types import interrupt`")
    print("OK: imports `interrupt` from langgraph.types")

    imported = re.search(
        r"from\s+uipath\.platform\.common\s+import\s+(?:[^\n]*\b(WaitTask|WaitEscalation)\b|\([^)]*\b(WaitTask|WaitEscalation)\b)",
        text,
    )
    if not imported:
        fail(
            "missing `from uipath.platform.common import WaitTask` (or `WaitEscalation`). "
            "The scenario waits on an existing Action Center task, "
            "not `CreateTask` (which opens a new one)."
        )
    print(f"OK: imports {imported.group(1) or imported.group(2)} from uipath.platform.common")

    wait_cls = find_interrupt_wait_class(tree)
    if wait_cls is None:
        fail(
            "no `interrupt(WaitTask(...))` / `interrupt(WaitEscalation(...))` call site found. "
            "The agent must pause on the existing task via `interrupt(WaitTask(action=...))`."
        )
    print(f"OK: graph node calls interrupt({wait_cls}(...))")

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

    assert_langgraph_config(ROOT, module)

    violations = find_module_level_llm_clients(module)
    if violations:
        fail("module-level UiPath* construction (C4): " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")

    print(f"OK: {wait_cls} HITL shape verified")


if __name__ == "__main__":
    main()
