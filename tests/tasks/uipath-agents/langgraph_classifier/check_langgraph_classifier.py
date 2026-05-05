#!/usr/bin/env python3
"""LangGraph agent project-shape check.

Asserts the lazy-LLM-init invariant (Critical Rule C4) and the
schema-sync invariant (`entry-points.json` reflects the Pydantic
Input/Output classes the agent declared).

Checks performed:

  1. `support-classifier/pyproject.toml` declares `uipath-langchain`
     as a dependency, has `[project]` with `authors`, and contains NO
     `[build-system]` section.
  2. The project has either `langgraph.json` (Pattern A — recommended)
     OR `uipath.json` with a `functions.graph` entry (Pattern B). Both
     are valid per the LangGraph integration guide.
  3. `main.py` (or `graph.py`) defines `GraphInput`/`GraphOutput`
     Pydantic models, exports a top-level `graph` variable, and has
     NO module-level UiPath* construction (`UiPathChat`,
     `UiPathAzureChatOpenAI`, etc.).
  4. `entry-points.json` has one entrypoint whose schemas mention
     `text` (input) and `category` (output) — proves `uip codedagent
     init` ran AFTER the Pydantic models were written.
  5. `bindings.json` is the v2.0 envelope (resource count is not
     asserted — the classifier itself uses no SDK resources).

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import load_bindings  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402

ROOT = find_project_root("support-classifier")


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
    if "[project]" not in text or "authors" not in text:
        sys.exit("FAIL: pyproject.toml is missing [project] or `authors`")
    if "uipath-langchain" not in text:
        sys.exit(
            "FAIL: pyproject.toml does not declare `uipath-langchain` — "
            "the LangGraph integration guide makes this dependency mandatory."
        )
    print("OK: pyproject.toml is hygienic and declares uipath-langchain")


def find_graph_module() -> Path:
    for candidate in ("main.py", "graph.py"):
        path = ROOT / candidate
        if path.is_file():
            return path
    sys.exit(
        "FAIL: neither main.py nor graph.py found under "
        f"{ROOT} — LangGraph integration guide requires one."
    )


def check_graph_module(path: Path) -> None:
    text = _read_text(path)
    for needle in ("GraphInput", "GraphOutput", "graph"):
        if needle not in text:
            sys.exit(f"FAIL: {path.name} is missing `{needle}`")
    if "StateGraph" not in text and "CompiledStateGraph" not in text:
        sys.exit(f"FAIL: {path.name} does not reference StateGraph / CompiledStateGraph")
    print(f"OK: {path.name} defines GraphInput, GraphOutput, and a graph variable")
    violations = find_module_level_llm_clients(path)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(
        f"OK: {path.name} has no module-level UiPath* construction "
        "(lazy-LLM-init invariant holds)"
    )


def check_runtime_config() -> None:
    langgraph_json = ROOT / "langgraph.json"
    uipath_json = ROOT / "uipath.json"
    if langgraph_json.is_file():
        doc = _load_json(langgraph_json)
        graphs = doc.get("graphs") or {}
        if not graphs:
            sys.exit("FAIL: langgraph.json has no `graphs` mapping")
        target = next(iter(graphs.values()))
        if not isinstance(target, str) or ":graph" not in target:
            sys.exit(
                f'FAIL: langgraph.json graphs entry should map to a `<file>:graph` '
                f'reference, got {target!r}'
            )
        print(f"OK: langgraph.json registers a graph -> {target!r}")
        return
    if uipath_json.is_file():
        doc = _load_json(uipath_json)
        functions = doc.get("functions") or {}
        graph_entry = functions.get("graph")
        if not graph_entry or ":graph" not in graph_entry:
            sys.exit(
                "FAIL: neither langgraph.json nor uipath.json `functions.graph` "
                "is present — the runtime cannot find the compiled graph."
            )
        print(f'OK: uipath.json registers functions.graph -> {graph_entry!r}')
        return
    sys.exit(
        "FAIL: project has neither langgraph.json nor uipath.json — at "
        "least one is required for `uip codedagent init` to succeed."
    )


def check_entry_points() -> None:
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit("FAIL: entry-points.json has no entryPoints — `uip codedagent init` did not run successfully")
    raw = json.dumps(entrypoints)
    for field in ("text", "category"):
        if field not in raw:
            sys.exit(
                f'FAIL: entry-points.json schemas do not mention `{field}`. '
                f'Either `uip codedagent init` ran before the Pydantic models '
                f'were written, or the models did not declare the expected '
                f'fields. Got: {raw}'
            )
    print(
        "OK: entry-points.json schemas reflect the GraphInput/GraphOutput "
        "fields (text, category)"
    )


def check_bindings() -> None:
    load_bindings(ROOT / "bindings.json")
    print("OK: bindings.json envelope is well-formed")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    graph_module = find_graph_module()
    check_graph_module(graph_module)
    check_runtime_config()
    check_entry_points()
    check_bindings()
    if not (ROOT / "run_marker.txt").is_file():
        sys.exit(f"FAIL: {ROOT}/run_marker.txt does not exist — `uip codedagent run` likely never finished")
    print("OK: run_marker.txt exists (run completed cleanly)")


if __name__ == "__main__":
    main()
