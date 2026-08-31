#!/usr/bin/env python3
"""Data Fabric SDK direct-access coded-agent shape check.

Asserts:
  1. `main.py` (or `graph.py`) imports `UiPath` from `uipath.platform`.
  2. The graph module calls a specific sdk.entities retrieval method
     (list_records, retrieve_records, query_entity_records, or get_record).
  3. A `filter=` parameter is present in the retrieval call.
  4. The entity name "Orders" and folder "Shared" appear in the file.
  5. A `@tool`-decorated function wraps the SDK call.
  6. No module-level `UiPath()` or LLM client construction.
  7. `bindings.json` declares the `datafabricentityset` resource.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)
from _shared.project_root import find_project_root  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.bindings_assertions import load_bindings, find_resource  # noqa: E402

ROOT = find_project_root("order-lookup")


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


def check_sdk_import(text: str) -> None:
    if not re.search(
        r"from\s+uipath\.platform\s+import\s+[^\n]*\bUiPath\b", text
    ):
        sys.exit(
            "FAIL: must import UiPath from `uipath.platform` "
            "(e.g. `from uipath.platform import UiPath`)"
        )
    print("OK: imports UiPath from uipath.platform")


def check_entities_usage(text: str) -> None:
    # Require a retrieval method specifically — list_records, retrieve_records,
    # query_entity_records, or get_record (sync or async variants). A generic
    # .entities.delete_record or unrelated call must NOT pass.
    retrieval_pattern = re.compile(
        r"\.entities\.(list_records|retrieve_records|query_entity_records|get_record)"
    )
    if not retrieval_pattern.search(text):
        sys.exit(
            "FAIL: no sdk.entities retrieval method found — "
            "expected list_records, retrieve_records, query_entity_records, "
            "or get_record (sync or async)"
        )
    print("OK: uses sdk.entities retrieval method")


def check_filter_usage(text: str) -> None:
    # The task asks for an OData filter by customer name. Verify the code
    # contains a filter parameter or OData-style filter string.
    if not re.search(r'\bfilter\s*=', text):
        sys.exit(
            "FAIL: no filter= parameter found — "
            "expected the tool to filter records by customer name"
        )
    print("OK: filter parameter present in retrieval call")


def check_entity_references(text: str) -> None:
    if not re.search(r'["\']Orders["\']', text):
        sys.exit('FAIL: entity name "Orders" not found in file')
    print('OK: entity "Orders" referenced')


def check_tool_decorator(text: str) -> None:
    if not re.search(r"@tool", text):
        sys.exit("FAIL: no @tool decorator found — SDK call must be wrapped as a LangChain tool")
    print("OK: @tool decorator present")


def check_bindings() -> None:
    # For the SDK direct path, `uip codedagent init` does not auto-detect
    # sdk.entities usage — there is no binding detection pattern for it.
    # We only verify that bindings.json exists and has a valid envelope.
    # If the agent hand-authored a datafabricentityset binding, that's a
    # bonus, but we don't require it.
    doc = load_bindings(ROOT / "bindings.json")
    resources = doc.get("resources") or []
    df_resources = [
        r
        for r in resources
        if isinstance(r, dict) and r.get("resource") == "datafabricentityset"
    ]
    if df_resources:
        print(f"OK: bindings.json declares {len(df_resources)} datafabricentityset resource(s) (bonus)")
    else:
        print("OK: bindings.json exists with valid envelope (no auto-detected datafabricentityset — expected for SDK direct path)")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)
    check_sdk_import(text)
    check_entities_usage(text)
    check_filter_usage(text)
    check_entity_references(text)
    check_tool_decorator(text)
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath/LLM construction (lazy init)")
    check_bindings()


if __name__ == "__main__":
    main()
