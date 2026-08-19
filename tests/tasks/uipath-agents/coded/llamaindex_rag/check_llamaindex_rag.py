#!/usr/bin/env python3
"""LlamaIndex Workflow + UiPath Context Grounding RAG check.

Asserts:
  1. `hr-helper/llama_index.json` exists and points at a workflow inside
     `main.py` (LlamaIndex framework was correctly selected).
  2. `main.py` imports `Workflow` and `step` from `llama_index.core.workflow`
     and decorates at least one method with `@step`.
  3. `main.py` imports a `uipath-llamaindex` Context Grounding RAG
     primitive — `ContextGroundingQueryEngine` from
     `uipath_llamaindex.query_engines` OR `ContextGroundingRetriever`
     from `uipath_llamaindex.retrievers`. Both are documented, public
     API (the query engine wraps the retriever); raw
     `sdk.context_grounding.search()` / `search_async()` fails — the
     skill's LlamaIndex guide says to use the framework primitives.
  4. The primitive is instantiated with `index_name` resolving to
     `"hr-policy"` (the index the user named in the prompt).
  5. `pyproject.toml` includes `uipath-llamaindex` as a dependency.
  6. No module-level UiPath* client construction (Critical Rule C4 —
     LLM clients must be lazy inside a `@step` body, never class- or
     module-level).
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("hr-helper")
MAIN = ROOT / "main.py"
LLAMA_JSON = ROOT / "llama_index.json"
PYPROJECT = ROOT / "pyproject.toml"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def find_calls(tree: ast.Module, func_name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func_name
    ]


def uses_raw_sdk_search(tree: ast.Module) -> bool:
    """True on any `<...>.context_grounding.search(...)` / `.search_async(...)` call."""
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in ("search", "search_async", "unified_search", "unified_search_async")
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "context_grounding"
        ):
            return True
    return False


def module_str_constants(tree: ast.Module) -> dict[str, str]:
    """Map module-level `NAME = "literal"` assignments to their string value."""
    consts: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    consts[target.id] = node.value.value
    return consts


def resolve_str(node: ast.AST | None, consts: dict[str, str]) -> str | None:
    """Resolve a string literal or a module-level string constant reference."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name) and node.id in consts:
        return consts[node.id]
    return None


def imports_from(tree: ast.Module, module: str, name: str) -> bool:
    """True if `tree` contains `from <module> import <name>` — single- or multi-line."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            if any(alias.name == name for alias in node.names):
                return True
    return False


def main() -> None:
    if not ROOT.is_dir():
        fail(f"project directory {ROOT} does not exist")

    if not LLAMA_JSON.is_file():
        fail(f"missing {LLAMA_JSON} — LlamaIndex was not selected as the framework")
    try:
        cfg = json.loads(LLAMA_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"llama_index.json is not valid JSON: {exc}")
    workflows = cfg.get("workflows") or cfg.get("graphs") or {}
    if not workflows:
        fail("llama_index.json has no `workflows` entries")
    if not any("main.py:" in str(v) for v in workflows.values()):
        fail(f"llama_index.json workflows do not point at main.py: {workflows}")
    print("OK: llama_index.json points at a workflow in main.py")

    if not MAIN.is_file():
        fail(f"missing {MAIN}")
    text = MAIN.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(MAIN))
    except SyntaxError as exc:
        fail(f"main.py has a syntax error: {exc}")

    if not imports_from(tree, "llama_index.core.workflow", "Workflow"):
        fail("main.py does not import `Workflow` from `llama_index.core.workflow`")
    if not imports_from(tree, "llama_index.core.workflow", "step"):
        fail("main.py does not import `step` from `llama_index.core.workflow`")
    if not re.search(r"@step\b", text):
        fail("main.py has no `@step` decorator — the workflow nodes must be marked with @step")
    print("OK: LlamaIndex Workflow shape (Workflow import + @step decorator) present")

    # Either documented uipath-llamaindex RAG primitive passes. The query
    # engine wraps the retriever internally; both bind the index the same
    # way. Maps to (module, class, positional slot of `index_name`).
    primitives = [
        ("uipath_llamaindex.query_engines", "ContextGroundingQueryEngine", 1),
        ("uipath_llamaindex.retrievers", "ContextGroundingRetriever", 0),
    ]
    imported = [(cls, pos) for mod, cls, pos in primitives if imports_from(tree, mod, cls)]
    if not imported:
        if uses_raw_sdk_search(tree):
            fail(
                "main.py grounds answers with raw `sdk.context_grounding.search()` / "
                "`search_async()`. Use a `uipath-llamaindex` RAG primitive instead — "
                "`ContextGroundingQueryEngine` (uipath_llamaindex.query_engines) or "
                "`ContextGroundingRetriever` (uipath_llamaindex.retrievers) — per the "
                "skill's LlamaIndex guide § Context Grounding (RAG)."
            )
        fail(
            "main.py imports neither `ContextGroundingQueryEngine` from "
            "`uipath_llamaindex.query_engines` nor `ContextGroundingRetriever` from "
            "`uipath_llamaindex.retrievers`. Those are the UiPath RAG primitives for "
            "LlamaIndex — use one to ground answers in the index."
        )
    print("OK: imports a uipath_llamaindex Context Grounding RAG primitive "
          f"({', '.join(cls for cls, _ in imported)})")

    consts = module_str_constants(tree)
    resolved: list[tuple[str, object]] = []
    bound_cls = None
    for cls, pos in imported:
        for call in find_calls(tree, cls):
            kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}
            name_node = kwargs.get("index_name")
            if name_node is None and len(call.args) > pos:
                name_node = call.args[pos]
            got = resolve_str(name_node, consts)
            if got == "hr-policy":
                bound_cls = cls
                break
            resolved.append((cls, got or getattr(name_node, "value", name_node)))
        if bound_cls:
            break
    if bound_cls is None:
        if not resolved:
            fail(
                "no `ContextGroundingQueryEngine(...)` / `ContextGroundingRetriever(...)` "
                "call site found"
            )
        fail(
            "no RAG primitive call binds `index_name` to 'hr-policy' (the index the "
            f"user named in the prompt); found: {resolved!r}"
        )
    print(f'OK: {bound_cls} bound to index_name="hr-policy"')

    if not PYPROJECT.is_file():
        fail(f"missing {PYPROJECT}")
    pyp = PYPROJECT.read_text(encoding="utf-8")
    if "uipath-llamaindex" not in pyp:
        fail(
            "pyproject.toml does not declare `uipath-llamaindex` — required for "
            "LlamaIndex coded agents (it registers the LlamaIndex runtime factory)"
        )
    print("OK: pyproject.toml includes `uipath-llamaindex`")

    violations = find_module_level_llm_clients(MAIN)
    if violations:
        fail("module-level UiPath* construction (C4): " + " | ".join(violations))
    print("OK: no module-level UiPath* construction")

    print("OK: LlamaIndex + Context Grounding RAG wiring verified")


if __name__ == "__main__":
    main()
