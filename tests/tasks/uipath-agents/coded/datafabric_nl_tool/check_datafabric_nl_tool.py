#!/usr/bin/env python3
"""Data Fabric NL-to-SQL tool coded-agent shape check.

Asserts:
  1. `main.py` (or `graph.py`) imports `create_datafabric_tool` from
     `uipath_langchain.agent.tools`.
  2. Imports `DataFabricEntityItem` from `uipath.platform.entities`.
  3. A `DataFabricEntityItem` is configured with a valid UUID `id` and
     `folder_key`.
  4. `base_system_prompt` is passed to `create_datafabric_tool`.
  5. No module-level UiPath/LLM construction.
  6. `bindings.json` exists with valid envelope.
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

ROOT = find_project_root("product-explorer")

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


def check_tool_factory_import(text: str) -> None:
    if not re.search(
        r"from\s+uipath_langchain\.agent\.tools\s+import\s+(?:[^\n]*\bcreate_datafabric_tool\b|\([^)]*\bcreate_datafabric_tool\b)",
        text,
    ):
        sys.exit(
            "FAIL: must import create_datafabric_tool from "
            "`uipath_langchain.agent.tools`"
        )
    print("OK: imports create_datafabric_tool from uipath_langchain.agent.tools")


def check_entity_item_import(text: str) -> None:
    if not re.search(
        r"from\s+uipath\.platform\.entities\s+import\s+(?:[^\n]*\bDataFabricEntityItem\b|\([^)]*\bDataFabricEntityItem\b)",
        text,
    ):
        sys.exit(
            "FAIL: must import DataFabricEntityItem from "
            "`uipath.platform.entities`"
        )
    print("OK: imports DataFabricEntityItem from uipath.platform.entities")


def check_entity_config(text: str) -> None:
    # The agent should have discovered an entity and configured it with
    # The agent may inline UUIDs (id="abc-...") or use constants (id=_ENTITY_ID
    # where _ENTITY_ID = "abc-..."). Check both patterns.
    uuids = UUID_PATTERN.findall(text)
    if not uuids:
        sys.exit(
            "FAIL: no valid UUID found in file — "
            "expected the agent to discover and configure an entity"
        )

    if not re.search(r'\bid\s*=', text):
        sys.exit("FAIL: no id= parameter found in DataFabricEntityItem configuration")
    print(f"OK: entity ID configured ({uuids[0][:8]}...)")

    if not re.search(r'\bfolder_key\s*=', text):
        sys.exit("FAIL: no folder_key= parameter found in DataFabricEntityItem configuration")
    print(f"OK: folder key configured")

    # Entity name should reference a non-empty string (inline or constant)
    if not re.search(r'\bname\s*=\s*["\'][^"\']+["\']', text) and not re.search(r'\bname\s*=\s*\w+', text):
        sys.exit("FAIL: no entity name= found in DataFabricEntityItem configuration")
    print("OK: entity name configured")


def check_prompt_forwarding(text: str) -> None:
    if not re.search(r'\bbase_system_prompt\b', text):
        sys.exit(
            "FAIL: base_system_prompt parameter not found — "
            "must pass system prompt to create_datafabric_tool"
        )
    print("OK: base_system_prompt forwarded to create_datafabric_tool")


def check_bindings() -> None:
    # Entity bindings are not yet supported in bindings.schema.json.
    # Verify the envelope is valid.
    load_bindings(ROOT / "bindings.json")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    module = find_graph_module()
    text = _read_text(module)
    check_tool_factory_import(text)
    check_entity_item_import(text)
    check_entity_config(text)
    check_prompt_forwarding(text)
    violations = find_module_level_llm_clients(module)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath/LLM construction (lazy init)")
    check_bindings()


if __name__ == "__main__":
    main()
