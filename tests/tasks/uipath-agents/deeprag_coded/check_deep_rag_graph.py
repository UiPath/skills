#!/usr/bin/env python3
"""Coded DeepRAG graph shape check.

Asserts that the agent scaffolded a Python coded agent that:

  1. Has a graph module (main.py or graph.py) under the project root.
  2. Imports `CreateDeepRag` and `WaitEphemeralIndex` from
     `uipath.platform.common`.
  3. Imports `EphemeralIndexUsage` from
     `uipath.platform.context_grounding`.
  4. Imports `interrupt` from `langgraph.types`.
  5. Calls `create_ephemeral_index_async`.
  6. Passes `is_ephemeral_index=True` on `CreateDeepRag`.
  7. Does NOT instantiate `UiPath()` at module top level.

The project root is whichever of `<cwd>/pyproject.toml` or
`<cwd>/deep-rag-agent/pyproject.toml` exists.
"""

from __future__ import annotations

import ast
import os
import re
import sys
from pathlib import Path

DEFAULT_SUBDIR = "deep-rag-agent"


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


def imported_symbols(tree: ast.AST, module: str) -> set[str]:
    """Return the set of symbol names imported from `module` in `tree`.

    Robust to single-line, multi-line parenthesized, backslash-continued,
    and aliased imports — anything Python itself accepts as `from <mod>
    import ...`.
    """
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == module:
            for alias in node.names:
                found.add(alias.name)
    return found


def assert_import(tree: ast.AST, text: str, module: str, symbols: list[str]) -> None:
    found = imported_symbols(tree, module)
    if not found:
        sys.exit(f"FAIL: graph module never imports from {module}")
    for sym in symbols:
        if sym not in found:
            sys.exit(f"FAIL: graph module does not import {sym} from {module}")


def assert_no_module_level_uipath(text: str) -> None:
    for m in re.finditer(r"^(\s*)([A-Za-z_][\w]*\s*=\s*UiPath\s*\()", text, re.MULTILINE):
        if m.group(1) == "":
            sys.exit("FAIL: UiPath() instantiated at module top level (must be inside node bodies)")


def main() -> None:
    root = find_project_root()
    module = find_graph_module(root)
    text = module.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(module))
    except SyntaxError as exc:
        sys.exit(f"FAIL: graph module is not valid Python ({exc})")

    assert_import(tree, text, "uipath.platform.common", ["CreateDeepRag", "WaitEphemeralIndex"])
    assert_import(tree, text, "uipath.platform.context_grounding", ["EphemeralIndexUsage"])
    assert_import(tree, text, "langgraph.types", ["interrupt"])

    if not re.search(r"\bcreate_ephemeral_index_async\s*\(", text):
        sys.exit("FAIL: graph module never calls create_ephemeral_index_async(...)")
    if not re.search(r"\bCreateDeepRag\s*\(", text):
        sys.exit("FAIL: graph module never calls CreateDeepRag(...)")
    if not re.search(r"is_ephemeral_index\s*=\s*True", text):
        sys.exit("FAIL: CreateDeepRag must pass is_ephemeral_index=True")

    assert_no_module_level_uipath(text)
    print("PASS")


if __name__ == "__main__":
    main()
