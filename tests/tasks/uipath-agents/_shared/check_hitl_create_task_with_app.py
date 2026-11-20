#!/usr/bin/env python3
"""HITL `interrupt(CreateTask)` shape check — regular Action Center task (NOT escalation).

Asserts:
  1. An agent module imports `interrupt` from `langgraph.types`.
  2. An agent module imports `CreateTask` from `uipath.platform.common`.
  3. At least one `interrupt(CreateTask(...))` call site exists.
  4. The `CreateTask` call targets `app_name="RefundReviewApp"`,
     `app_folder_path="Shared/uipath-agents/RefundReviewSol"` (where the app
     is deployed on the codereval tenant).
  5. No agent module uses `CreateEscalation` (that's a different pattern
     covered by hitl_create_task — keep them disjoint).
  6. `bindings.json` declares the `app` resource for `RefundReviewApp` /
     `Shared/uipath-agents/RefundReviewSol`.
  7. A top-level `graph =` variable is exported.
  8. `langgraph.json` exists at the resolved project root and points at
     the exported graph.
  9. No module-level UiPath* construction (Critical Rule C4).

Agent modules are the entry module `langgraph.json` registers plus every
project module it imports (see `project_sources.py`).
"""

from __future__ import annotations

import ast
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.langgraph_assertions import assert_langgraph_config  # noqa: E402
from _shared.project_sources import agent_modules, find_entry_module, parse_modules, read_sources  # noqa: E402
from _shared.bindings_assertions import (  # noqa: E402
    load_bindings,
    find_resource,
    assert_value_field,
    assert_metadata_field,
)

ROOT = find_project_root("refund-gate")

APP_NAME = "RefundReviewApp"
APP_FOLDER = "Shared/uipath-agents/RefundReviewSol"
# SDK-generated (`uip codedagent init`, uipath >= 2.14) and hand-authored
# (bindings-reference.md) key forms — both resolve at runtime.
APP_KEYS = (f"app.{APP_NAME}.{APP_FOLDER}", f"{APP_NAME}.{APP_FOLDER}")


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def module_constants(tree: ast.Module) -> dict[str, object]:
    consts: dict[str, object] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.target, ast.Name)
        ):
            # Annotated constant, e.g. ``APP_NAME: str = "RefundReviewApp"``.
            consts[node.target.id] = node.value.value
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
        if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == "CreateTask":
            return inner
    return None


def main() -> None:
    if not ROOT.is_dir():
        fail(f"project directory {ROOT} does not exist")

    module = find_entry_module(ROOT)
    modules = agent_modules(ROOT, module)
    parsed = parse_modules(modules)
    text = read_sources(modules)
    entry_text = module.read_text(encoding="utf-8")

    if not re.search(r"from\s+langgraph\.types\s+import\s+(?:[^\n]*\binterrupt\b|\([^)]*\binterrupt\b)", text):
        fail("missing `from langgraph.types import interrupt`")
    print("OK: imports `interrupt` from langgraph.types")

    if not re.search(r"from\s+uipath\.platform\.common\s+import\s+(?:[^\n]*\bCreateTask\b|\([^)]*\bCreateTask\b)", text):
        fail(
            "missing `from uipath.platform.common import CreateTask`. "
            "The scenario opens a new Action Center task — use `CreateTask`."
        )
    print("OK: imports CreateTask from uipath.platform.common")

    if re.search(r"\bCreateEscalation\s*\(", text):
        fail(
            "An agent module invokes `CreateEscalation(...)`. The scenario is a regular "
            "compliance review, not an escalation. Use `CreateTask` only."
        )
    print("OK: no CreateEscalation usage (scenario is the regular task pattern)")

    found = next(
        ((tree, c) for _, tree in parsed if (c := find_create_task_call(tree))),
        None,
    )
    if found is None:
        fail("no `interrupt(CreateTask(...))` call site found")
    tree, call = found

    # Constants from every agent module; the call's own module wins.
    consts: dict[str, object] = {}
    for _, other in parsed:
        consts.update(module_constants(other))
    consts.update(module_constants(tree))
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}
    expected = {"app_name": APP_NAME, "app_folder_path": APP_FOLDER}
    for kw, want in expected.items():
        if kw not in kwargs:
            fail(f"`CreateTask(...)` is missing `{kw}=`")
        got = resolve_kwarg(kwargs[kw], consts)
        if got != want:
            fail(f"`CreateTask({kw}=...)` resolves to {got!r}, expected {want!r}")
    print(f'OK: CreateTask targets app_name="{APP_NAME}" / app_folder_path="{APP_FOLDER}"')

    if not re.search(r"^\s*graph\s*=\s*", entry_text, re.M):
        fail(f"{module.name} does not export a top-level `graph =` variable")
    print("OK: top-level `graph` variable exported")

    assert_langgraph_config(ROOT, module)

    violations = [v for m in modules for v in find_module_level_llm_clients(m)]
    if violations:
        fail("module-level UiPath* construction (C4): " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")

    doc = load_bindings(ROOT / "bindings.json")
    present = {
        r.get("key")
        for r in (doc.get("resources") or [])
        if isinstance(r, dict) and r.get("resource") == "app"
    }
    key = next((k for k in APP_KEYS if k in present), APP_KEYS[0])
    entry = find_resource(doc, resource="app", key=key)
    assert_value_field(entry, field="name", expected=APP_NAME)
    assert_value_field(entry, field="folderPath", expected=APP_FOLDER)
    assert_metadata_field(entry, field="ActivityName", expected="create_async")
    assert_metadata_field(entry, field="DisplayLabel", expected=APP_NAME)
    print(f'OK: bindings.json declares the {APP_NAME}/{APP_FOLDER} `app` resource (key="{key}")')


if __name__ == "__main__":
    main()
