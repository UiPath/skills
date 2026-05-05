#!/usr/bin/env python3
"""ContextGrounding-based RAG coded-agent shape check.

Asserts:
  1. `main.py` imports `ContextGroundingRetriever` from
     `uipath_langchain.retrievers` (the canonical import path the
     skill teaches across context-grounding examples and the
     LangGraph integration tools table) and references it.
  2. The retriever is constructed with `index_name="company_docs"`
     and `folder_path="Shared"`.
  3. `bindings.json` declares the `index` resource for
     company_docs / Shared with the standard binding shape.
  4. No module-level UiPath* construction — both the retriever and
     `UiPathChat` must be inside node bodies.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("policy-rag")

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


def check_imports_and_calls(text: str) -> None:
    if not re.search(r"\bContextGroundingRetriever\b", text):
        sys.exit("FAIL: main.py never references ContextGroundingRetriever")
    if not re.search(
        r"from\s+uipath_langchain\.retrievers\s+import\s+[^\n]*\bContextGroundingRetriever\b",
        text,
    ):
        sys.exit(
            "FAIL: ContextGroundingRetriever must be imported from "
            "`uipath_langchain.retrievers` — the canonical path the skill teaches."
        )
    print("OK: main.py imports ContextGroundingRetriever from uipath_langchain.retrievers")
    if not re.search(r'index_name\s*=\s*["\']company_docs["\']', text):
        sys.exit('FAIL: ContextGroundingRetriever call does not pass index_name="company_docs"')
    if not re.search(r'folder_path\s*=\s*["\']Shared["\']', text):
        sys.exit('FAIL: ContextGroundingRetriever call does not pass folder_path="Shared"')
    print('OK: retriever is constructed with index_name="company_docs" / folder_path="Shared"')


def check_index_binding() -> None:
    doc = load_bindings(ROOT / "bindings.json")
    entry = find_resource(doc, resource="index", key="company_docs.Shared")
    assert_value_field(entry, field="name", expected="company_docs")
    assert_value_field(entry, field="folderPath", expected="Shared")
    assert_metadata_field(entry, field="ActivityName", expected="retrieve_async")
    print("OK: bindings.json declares the company_docs/Shared `index` resource")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)
    check_imports_and_calls(text)
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath* construction (retriever + LLM both lazy)")
    check_index_binding()


if __name__ == "__main__":
    main()
