#!/usr/bin/env python3
"""Coded BatchTransform graph shape check.

Asserts that the agent scaffolded a Python coded agent that:

  1. Has a graph module (main.py or graph.py) under the project root.
  2. Imports `CreateBatchTransform` and `CreateEphemeralIndex` from
     `uipath.platform.common`.
  3. Imports `BatchTransformOutputColumn` and `EphemeralIndexUsage`
     from `uipath.platform.context_grounding`.
  4. Imports `durable_interrupt` from
     `uipath_langchain._utils.durable_interrupt`.
  5. References `CreateBatchTransform(...)` somewhere (the durable
     interrupt body).
  6. Does NOT instantiate `UiPath()` at module top level.

The project root is whichever of `<cwd>/pyproject.toml` or
`<cwd>/batch-transform-agent/pyproject.toml` exists.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

DEFAULT_SUBDIR = "batch-transform-agent"


def find_project_root() -> Path:
    cwd = Path(os.getcwd())
    if (cwd / "pyproject.toml").is_file():
        return cwd
    nested = cwd / DEFAULT_SUBDIR
    if (nested / "pyproject.toml").is_file():
        return nested
    sys.exit(f"FAIL: pyproject.toml not found in {cwd} or {nested}")


def find_graph_module(root: Path) -> Path:
    for candidate in ("main.py", "graph.py"):
        path = root / candidate
        if path.is_file():
            return path
    sys.exit(f"FAIL: neither main.py nor graph.py found under {root}")


def assert_import(text: str, module: str, symbols: list[str]) -> None:
    pat = rf"from\s+{re.escape(module)}\s+import\s+[^\n]*"
    matches = re.findall(pat, text)
    if not matches:
        sys.exit(f"FAIL: graph module never imports from {module}")
    for sym in symbols:
        if not any(re.search(rf"\b{re.escape(sym)}\b", m) for m in matches):
            sys.exit(f"FAIL: graph module does not import {sym} from {module}")


def assert_no_module_level_uipath(text: str) -> None:
    for m in re.finditer(r"^(\s*)([A-Za-z_][\w]*\s*=\s*UiPath\s*\()", text, re.MULTILINE):
        if m.group(1) == "":
            sys.exit("FAIL: UiPath() instantiated at module top level (must be lazy, inside node bodies)")


def main() -> None:
    root = find_project_root()
    module = find_graph_module(root)
    text = module.read_text(encoding="utf-8")

    assert_import(text, "uipath.platform.common", ["CreateBatchTransform", "CreateEphemeralIndex"])
    assert_import(text, "uipath.platform.context_grounding", ["BatchTransformOutputColumn", "EphemeralIndexUsage"])
    assert_import(text, "uipath_langchain._utils.durable_interrupt", ["durable_interrupt"])

    if not re.search(r"\bCreateBatchTransform\s*\(", text):
        sys.exit("FAIL: graph module never calls CreateBatchTransform(...)")
    if not re.search(r"\bCreateEphemeralIndex\s*\(", text):
        sys.exit("FAIL: graph module never calls CreateEphemeralIndex(...)")

    assert_no_module_level_uipath(text)
    print("PASS")


if __name__ == "__main__":
    main()
