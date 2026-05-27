#!/usr/bin/env python3
"""LangGraph conversational coded-agent check.

Verifies the artifacts a coded agent flagged as conversational MUST
produce, per `references/coded/capabilities/conversational-agents.md`:

  1. `chat-agent/pyproject.toml` has `[project]` + `authors` and
     NO `[build-system]` section (Critical Rule C1).
  2. `chat-agent/uipath.json` sets
     `runtimeOptions.isConversational: true` — the load-bearing flag.
  3. `chat-agent/langgraph.json` exists (LangGraph entry-point config).
  4. `chat-agent/main.py` (or the file referenced by langgraph.json)
     has no module-level UiPath*/LLM client construction
     (Critical Rule C4 — lazy init).

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("chat-agent")


def _read_text(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"FAIL: Missing {path}")
    return path.read_text(encoding="utf-8")


def _load_json(path: Path) -> dict:
    raw = _read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def check_pyproject() -> None:
    text = _read_text(ROOT / "pyproject.toml")
    if "[build-system]" in text:
        sys.exit(
            "FAIL: pyproject.toml contains a [build-system] section — "
            "Critical Rule C1 forbids it."
        )
    if "[project]" not in text:
        sys.exit("FAIL: pyproject.toml has no [project] section")
    if "authors" not in text:
        sys.exit(
            "FAIL: pyproject.toml has no `authors` entry — `uip codedagent "
            "deploy` will reject the package."
        )
    print("OK: pyproject.toml has [project], `authors`, and no [build-system]")


def check_uipath_json() -> None:
    doc = _load_json(ROOT / "uipath.json")
    runtime = doc.get("runtimeOptions") or {}
    if runtime.get("isConversational") is not True:
        sys.exit(
            "FAIL: uipath.json does not set "
            "`runtimeOptions.isConversational: true` — the load-bearing "
            "flag for chat-style agents."
        )
    print("OK: uipath.json sets runtimeOptions.isConversational = true")


def check_langgraph_json() -> None:
    path = ROOT / "langgraph.json"
    doc = _load_json(path)
    graphs = doc.get("graphs") or {}
    if not graphs:
        sys.exit(
            "FAIL: langgraph.json has no `graphs` mapping — the LangGraph "
            "entry point is missing."
        )
    print("OK: langgraph.json declares at least one graph entry point")


def check_lazy_init() -> None:
    main = ROOT / "main.py"
    candidates = [main] if main.is_file() else list(ROOT.glob("*.py"))
    if not candidates:
        sys.exit("FAIL: no Python source files found in project root")
    for py in candidates:
        violations = find_module_level_llm_clients(py)
        if violations:
            sys.exit("FAIL: " + " | ".join(violations))
    print("OK: no module-level UiPath*/LLM client construction in project sources")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_uipath_json()
    check_langgraph_json()
    check_lazy_init()


if __name__ == "__main__":
    main()
