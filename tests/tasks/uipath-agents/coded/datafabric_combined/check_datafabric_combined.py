#!/usr/bin/env python3
"""Data Fabric combined-path coded-agent shape check.

Asserts:
  1. NL-to-SQL path: imports `create_datafabric_tool` from
     `uipath_langchain.agent.tools` and `DataFabricEntityItem` from
     `uipath.platform.entities`. Entity configured with valid UUIDs.
     `base_system_prompt` parameter present.
  2. SDK direct path: imports `UiPath` from `uipath.platform`.
     Uses `sdk.entities.update_record` (sync or async).
     Wrapped in @tool decorator.
  3. No module-level UiPath/LLM construction.
  4. `bindings.json` exists with valid envelope.
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

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)


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


def check_entity_config(text: str) -> None:
    # Verify entity is configured with structurally valid UUIDs (discovered from tenant)
    id_match = re.search(r'\bid\s*=\s*["\'](' + UUID_PATTERN.pattern + r')["\']', text)
    if not id_match:
        sys.exit("FAIL: no DataFabricEntityItem id= with a valid UUID found")
    print(f"OK: entity ID configured ({id_match.group(1)[:8]}...)")

    fk_match = re.search(r'\bfolder_key\s*=\s*["\'](' + UUID_PATTERN.pattern + r')["\']', text)
    if not fk_match:
        sys.exit("FAIL: no DataFabricEntityItem folder_key= with a valid UUID found")
    print(f"OK: folder key configured ({fk_match.group(1)[:8]}...)")


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
            "the write tool must use SDK to update records"
        )
    print("OK: uses sdk.entities.update_record for writes")


def check_tool_decorator(text: str) -> None:
    if not re.search(r"@tool", text):
        sys.exit("FAIL: no @tool decorator — write tool must be a LangChain tool")
    print("OK: @tool decorator present")


# ── Shared checks ──────────────────────────────────────────────────


def check_bindings() -> None:
    # Entity bindings are not yet supported in bindings.schema.json.
    # Verify the envelope is valid.
    load_bindings(ROOT / "bindings.json")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)

    # NL-to-SQL path
    check_nl_tool_factory(text)
    check_entity_item_import(text)
    check_entity_config(text)
    check_prompt_forwarding(text)

    # SDK direct path
    check_sdk_import(text)
    check_update_record(text)
    check_tool_decorator(text)

    # Shared invariants
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath/LLM construction (lazy init)")
    check_bindings()


if __name__ == "__main__":
    main()
