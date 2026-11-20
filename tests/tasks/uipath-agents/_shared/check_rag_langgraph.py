#!/usr/bin/env python3
"""ContextGrounding-based RAG coded-agent shape check.

Asserts:
  1. The agent modules use one of the two accepted retrieval patterns:
     - `ContextGroundingRetriever` from `uipath_langchain.retrievers`
       (preferred — LangChain-native, integrates with graph pipeline)
     - `sdk.context_grounding.search` / `search_async` (raw SDK, also valid)
  2. The index name "company_docs" and folder "Shared" appear in them.
  3. `bindings.json` declares the `index` resource for
     company_docs / Shared with the standard binding shape.
  4. No module-level UiPath* construction — retriever and LLM must be
     inside node bodies.

Agent modules are the entry module `langgraph.json` registers plus every
project module it imports (see `project_sources.py`).
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("policy-rag")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.bindings_assertions import (  # noqa: E402
    load_bindings,
    find_resource,
    assert_value_field,
    assert_metadata_field,
)
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_sources import agent_modules, find_entry_module, read_sources  # noqa: E402


def check_imports_and_calls(text: str) -> None:
    uses_retriever = bool(re.search(r"\bContextGroundingRetriever\b", text))
    uses_sdk = bool(re.search(r"context_grounding\.(search|search_async|unified_search|unified_search_async)\b", text))

    if not uses_retriever and not uses_sdk:
        sys.exit(
            "FAIL: the agent modules use neither ContextGroundingRetriever nor "
            "sdk.context_grounding.search — no context grounding retrieval found."
        )

    if uses_retriever:
        if not re.search(
            r"from\s+uipath_langchain\.retrievers\s+import\s+(?:[^\n]*\bContextGroundingRetriever\b|\([^)]*\bContextGroundingRetriever\b)",
            text,
        ):
            sys.exit(
                "FAIL: ContextGroundingRetriever must be imported from "
                "`uipath_langchain.retrievers`."
            )
        print("OK: agent uses ContextGroundingRetriever (LangChain-native pattern)")
    else:
        print("OK: agent uses sdk.context_grounding.search (raw SDK pattern)")

    if not re.search(r'["\']company_docs["\']', text):
        sys.exit('FAIL: index name "company_docs" not found in the agent modules')
    if not re.search(r'["\']Shared["\']', text):
        sys.exit('FAIL: folder path "Shared" not found in the agent modules')
    print('OK: index "company_docs" / folder "Shared" referenced')


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
    modules = agent_modules(ROOT, find_entry_module(ROOT))
    check_imports_and_calls(read_sources(modules))
    violations = [v for m in modules for v in find_module_level_llm_clients(m)]
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath* construction (retriever + LLM both lazy)")
    check_index_binding()


if __name__ == "__main__":
    main()
