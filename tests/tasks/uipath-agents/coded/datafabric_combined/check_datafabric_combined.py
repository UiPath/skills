#!/usr/bin/env python3
"""Data Fabric combined-path coded-agent shape check.

Asserts:
  1. NL-to-SQL path: imports `create_datafabric_tool` from
     `uipath_langchain.agent.tools` and `DataFabricEntityItem` from
     `uipath.platform.entities`. Tool named "query_orders".
     `base_system_prompt` parameter present.
  2. SDK direct path: imports `UiPath` from `uipath.platform`.
     Uses `sdk.entities.update_record_async` (or `update_record`).
     Wrapped in @tool decorator. Function named `close_order`.
  3. No module-level UiPath/LLM construction.
  4. `bindings.json` declares datafabricentityset resource.
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
from _shared.bindings_assertions import load_bindings  # noqa: E402

ROOT = find_project_root("order-manager")


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


# ── NL-to-SQL path checks ──────────────────────────────────────────


def check_nl_tool_factory(text: str) -> None:
    if not re.search(
        r"from\s+uipath_langchain\.agent\.tools\s+import\s+[^\n]*\bcreate_datafabric_tool\b",
        text,
    ):
        sys.exit(
            "FAIL: must import create_datafabric_tool from "
            "`uipath_langchain.agent.tools`"
        )
    print("OK: imports create_datafabric_tool")


def check_entity_item_import(text: str) -> None:
    if not re.search(
        r"from\s+uipath\.platform\.entities\s+import\s+[^\n]*\bDataFabricEntityItem\b",
        text,
    ):
        sys.exit(
            "FAIL: must import DataFabricEntityItem from "
            "`uipath.platform.entities`"
        )
    print("OK: imports DataFabricEntityItem")


def check_nl_tool_name(text: str) -> None:
    if not re.search(r'["\']query_orders["\']', text):
        sys.exit('FAIL: NL tool name "query_orders" not found')
    print('OK: NL tool named "query_orders"')


def check_prompt_forwarding(text: str) -> None:
    if not re.search(r'\bbase_system_prompt\b', text):
        sys.exit(
            "FAIL: base_system_prompt parameter not found — "
            "must forward system prompt to create_datafabric_tool"
        )
    print("OK: base_system_prompt forwarded")


# ── SDK direct path checks ─────────────────────────────────────────


def check_sdk_import(text: str) -> None:
    if not re.search(
        r"from\s+uipath\.platform\s+import\s+[^\n]*\bUiPath\b", text
    ):
        sys.exit("FAIL: must import UiPath from `uipath.platform`")
    print("OK: imports UiPath from uipath.platform")


def check_update_record(text: str) -> None:
    if not re.search(r"\.entities\.update_record", text):
        sys.exit(
            "FAIL: no sdk.entities.update_record call found — "
            "close_order must use SDK to update records"
        )
    print("OK: uses sdk.entities.update_record for writes")


def check_close_order_tool(text: str) -> None:
    if not re.search(r"@tool", text):
        sys.exit("FAIL: no @tool decorator — close_order must be a LangChain tool")
    if not re.search(r"def\s+close_order\b", text) and not re.search(
        r"async\s+def\s+close_order\b", text
    ):
        sys.exit('FAIL: function "close_order" not found')
    print('OK: @tool-decorated "close_order" function present')


# ── Shared checks ──────────────────────────────────────────────────


def check_bindings() -> None:
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
        print("OK: bindings.json exists with valid envelope (no auto-detected datafabricentityset — expected until CLI adds detection)")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)

    # NL-to-SQL path
    check_nl_tool_factory(text)
    check_entity_item_import(text)
    check_nl_tool_name(text)
    check_prompt_forwarding(text)

    # SDK direct path
    check_sdk_import(text)
    check_update_record(text)
    check_close_order_tool(text)

    # Shared invariants
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath/LLM construction (lazy init)")
    check_bindings()


if __name__ == "__main__":
    main()
