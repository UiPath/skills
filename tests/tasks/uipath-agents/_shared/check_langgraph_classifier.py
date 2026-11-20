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
  3. The graph module `langgraph.json` registers (else `main.py` /
     `graph.py`) wires a `StateGraph` to distinct Pydantic input/output
     models, exports a top-level `graph` variable, and neither it nor
     any project module it imports has module-level UiPath*
     construction (`UiPathChat`, `UiPathAzureChatOpenAI`, etc.). Model
     *names* are not asserted — `agent-patterns.md` allows any naming.
  4. `entry-points.json` input / output property names equal the
     fields of the models the StateGraph is wired to — proving `uip
     codedagent init` ran AFTER the models were final — with at least
     one input and two output properties. An output enum naming any
     of billing / technical / general names all three. No field name
     is asserted: the prompt names none.
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
from _shared.langgraph_assertions import assert_graph_module_shape, graph_io_fields  # noqa: E402
from _shared.project_root import find_project_root  # noqa: E402
from _shared.project_sources import agent_modules, find_entry_module  # noqa: E402

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


def check_graph_module(path: Path) -> None:
    modules = agent_modules(ROOT, path)
    assert_graph_module_shape(path, modules)
    violations = [v for m in modules for v in find_module_level_llm_clients(m)]
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(
        "OK: agent modules have no module-level UiPath* construction "
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


BUCKETS = frozenset({"billing", "technical", "general"})


def _properties(schema: dict) -> dict[str, dict]:
    """Top-level properties, with `$ref` / `anyOf` resolved per property."""
    def resolve(node: object) -> dict:
        for _ in range(10):
            if not isinstance(node, dict):
                return {}
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/"):
                target: object = schema
                for part in ref[2:].split("/"):
                    target = target.get(part, {}) if isinstance(target, dict) else {}
                node = target
                continue
            branches = node.get("anyOf") or node.get("oneOf") or node.get("allOf")
            typed = [b for b in branches or [] if isinstance(b, dict) and b.get("type") != "null"]
            if typed:
                node = typed[0]
                continue
            return node
        return {}

    return {k: resolve(v) for k, v in (schema.get("properties") or {}).items()}


def check_entry_points(graph_module: Path) -> None:
    """`entry-points.json` is in sync with the code, and carries the shape
    the prompt asks for. No field name is asserted — the prompt names none.

      1. Sync: the input / output property names equal the fields of the
         models `StateGraph` is wired to (`input_schema` else the state,
         `output_schema`). A mismatch means `uip codedagent init` ran
         before the models were final.
      2. Shape: the input has at least one property (the ticket) and the
         output at least two (the category and the original ticket).
      3. Buckets: if an output property is an enum naming any of the
         prompt's buckets, it names all three. A plain `str` category
         is accepted — its values cannot be checked statically.
    """
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit("FAIL: entry-points.json has no entryPoints — `uip codedagent init` did not run successfully")
    ep = entrypoints[0]
    in_props = _properties(ep.get("input") or {})
    out_props = _properties(ep.get("output") or {})

    in_model, in_fields, out_model, out_fields = graph_io_fields(
        graph_module, agent_modules(ROOT, graph_module)
    )
    for side, model, fields, props in (
        ("input", in_model, in_fields, in_props),
        ("output", out_model, out_fields, out_props),
    ):
        if fields != set(props):
            sys.exit(
                f"FAIL: entry-points.json {side} properties {sorted(props)} do not "
                f"match `{model}` fields {sorted(fields)} — `uip codedagent init` "
                f"ran before the models were final. Re-run it."
            )
    print(
        f"OK: entry-points.json matches the code: {in_model} {sorted(in_fields)} -> "
        f"{out_model} {sorted(out_fields)}"
    )

    if not in_props:
        sys.exit("FAIL: the input schema has no properties — the ticket cannot be passed in")
    if len(out_props) < 2:
        sys.exit(
            f"FAIL: the output schema has {sorted(out_props)} — the prompt asks for "
            "the chosen category AND the original ticket text"
        )
    for name, prop in out_props.items():
        values = prop.get("enum")
        if not isinstance(values, list):
            continue
        normalized = {str(v).lower() for v in values}
        if normalized & BUCKETS and not BUCKETS <= normalized:
            sys.exit(
                f"FAIL: output `{name}` enumerates {sorted(values)} — missing "
                f"bucket(s) {sorted(BUCKETS - normalized)} from the prompt"
            )
    print("OK: input carries the ticket; output carries a category and the ticket")


def check_bindings() -> None:
    load_bindings(ROOT / "bindings.json")
    print("OK: bindings.json envelope is well-formed")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    graph_module = find_entry_module(ROOT)
    check_graph_module(graph_module)
    check_runtime_config()
    check_entry_points(graph_module)
    check_bindings()


if __name__ == "__main__":
    main()
