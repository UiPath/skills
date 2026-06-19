#!/usr/bin/env python3
"""LlamaIndex Workflow + UiPath Context Grounding RAG check.

Asserts:
  1. `hr-helper/llama_index.json` exists and points at a workflow inside
     `main.py` (LlamaIndex framework was correctly selected).
  2. `main.py` imports `Workflow` and `step` from `llama_index.core.workflow`
     and decorates at least one method with `@step`.
  3. `main.py` imports `ContextGroundingQueryEngine` from
     `uipath_llamaindex.query_engines` — the UiPath RAG primitive.
  4. The query engine is instantiated with `index_name="hr-policy"`
     (the index the user named in the prompt).
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


def find_call(tree: ast.Module, func_name: str) -> ast.Call | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func_name:
            return node
    return None


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
    if not any("./main.py" in str(v) for v in workflows.values()):
        fail(f"llama_index.json workflows do not point at ./main.py: {workflows}")
    print("OK: llama_index.json points at a workflow in main.py")

    if not MAIN.is_file():
        fail(f"missing {MAIN}")
    text = MAIN.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(MAIN))
    except SyntaxError as exc:
        fail(f"main.py has a syntax error: {exc}")

    if not re.search(r"from\s+llama_index\.core\.workflow\s+import\s+[^\n]*\bWorkflow\b", text):
        fail("main.py does not import `Workflow` from `llama_index.core.workflow`")
    if not re.search(r"from\s+llama_index\.core\.workflow\s+import\s+[^\n]*\bstep\b", text):
        fail("main.py does not import `step` from `llama_index.core.workflow`")
    if not re.search(r"@step\b", text):
        fail("main.py has no `@step` decorator — the workflow nodes must be marked with @step")
    print("OK: LlamaIndex Workflow shape (Workflow import + @step decorator) present")

    if not re.search(r"from\s+uipath_llamaindex\.query_engines\s+import\s+[^\n]*\bContextGroundingQueryEngine\b", text):
        fail(
            "main.py does not import `ContextGroundingQueryEngine` from "
            "`uipath_llamaindex.query_engines`. That is the UiPath RAG primitive "
            "for LlamaIndex — use it to ground answers in the index."
        )
    print("OK: imports ContextGroundingQueryEngine from uipath_llamaindex.query_engines")

    call = find_call(tree, "ContextGroundingQueryEngine")
    if call is None:
        fail("no `ContextGroundingQueryEngine(...)` call site found")
    kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg is not None}
    name_node = kwargs.get("index_name")
    if name_node is None or not (isinstance(name_node, ast.Constant) and name_node.value == "hr-policy"):
        got = getattr(name_node, "value", name_node)
        fail(
            f"`ContextGroundingQueryEngine(index_name=...)` resolves to {got!r}, "
            "expected 'hr-policy' (the index the user named in the prompt)"
        )
    print('OK: ContextGroundingQueryEngine bound to index_name="hr-policy"')

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
