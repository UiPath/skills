#!/usr/bin/env python3
"""Anti-pattern check — OpenAI Agents framework has no HITL.

The skill documents that OpenAI Agents has no first-class HITL support;
`interrupt(...)` is a LangGraph primitive. After the fix, asserts:

  1. `main.py` no longer calls `interrupt(...)`.
  2. `main.py` no longer imports from `langgraph.types` (that pulls in
     the wrong framework's HITL primitive).
  3. `main.py` still exports a `main` factory that returns an `Agent`
     (OpenAI Agents shape preserved).
  4. `openai_agents.json` still points at `./main.py:main`.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("triage-broken")
MAIN = ROOT / "main.py"
FRAMEWORK_JSON = ROOT / "openai_agents.json"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def _has_interrupt_call(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "interrupt":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "interrupt":
                return True
    return False


def main() -> None:
    if not MAIN.is_file():
        fail(f"missing {MAIN}")
    text = MAIN.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(MAIN))
    except SyntaxError as exc:
        fail(f"{MAIN} has a syntax error: {exc}")

    if _has_interrupt_call(tree):
        fail(
            "main.py still calls `interrupt(...)`. "
            "OpenAI Agents has no first-class HITL — `interrupt` is a LangGraph "
            "primitive and does not work here. Remove the interrupt call (or, if "
            "HITL is essential, migrate the project to LangGraph)."
        )
    print("OK: main.py no longer contains an `interrupt(...)` call")

    if re.search(r"from\s+langgraph\.types\s+import", text):
        fail(
            "main.py still imports from `langgraph.types`. "
            "That pulls in LangGraph primitives into an OpenAI Agents project. "
            "Drop the import."
        )
    if re.search(r"^\s*import\s+langgraph\b", text, re.M):
        fail("main.py still imports `langgraph`. Drop it — wrong framework.")
    print("OK: main.py no longer imports from langgraph")

    if not re.search(r"^\s*def\s+main\s*\(", text, re.M):
        fail(
            "main.py no longer defines a top-level `main` factory. "
            "OpenAI Agents requires `def main() -> Agent` so `uip codedagent init` "
            "can discover the entrypoint via `openai_agents.json`."
        )
    print("OK: top-level `main` factory function preserved")

    if "Agent[" not in text and re.search(r"\bAgent\s*\(", text) is None:
        fail(
            "main.py no longer constructs an `Agent(...)` — the OpenAI Agents "
            "primitive must remain. Replacing it with something else would break "
            "the framework shape."
        )
    print("OK: `Agent` construction preserved")

    if not FRAMEWORK_JSON.is_file():
        fail(f"missing {FRAMEWORK_JSON} — framework marker must be preserved")
    try:
        payload = json.loads(FRAMEWORK_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"openai_agents.json is not valid JSON: {exc}")
    target = (payload.get("agents") or {}).get("agent")
    # Accept either "./main.py:main" or "main.py:main" — both forms are
    # equivalent at runtime.
    if target not in ("./main.py:main", "main.py:main"):
        fail(
            f"openai_agents.json `agents.agent` is {target!r}; "
            "must point at `main.py:main` (the entrypoint that returns the Agent factory)"
        )
    print(f"OK: openai_agents.json still points at {target!r}")


if __name__ == "__main__":
    main()
