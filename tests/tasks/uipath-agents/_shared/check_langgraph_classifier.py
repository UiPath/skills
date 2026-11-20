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
  4. `entry-points.json` carries the classifier contract — a string
     input, a category output covering billing / technical / general,
     and the echoed ticket text — proving `uip codedagent init` ran
     AFTER the Pydantic models were written. Field names are not
     asserted: the prompt names none.
  5. `bindings.json` is the v2.0 envelope (resource count is not
     asserted — the classifier itself uses no SDK resources).

Exits 0 on PASS, with a `FAIL: ...` message on the first violation.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _shared.bindings_assertions import load_bindings  # noqa: E402
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402
from _shared.langgraph_assertions import assert_graph_module_shape  # noqa: E402
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
# Name hints for a plain-string category field (no enum in the schema).
_CATEGORY_NAME = re.compile(r"categor|bucket|class|label|queue|department|topic", re.I)


def _resolve(schema: object, root: dict) -> dict:
    """Follow `$ref` (into `$defs` / `definitions`) and unwrap `anyOf` /
    `oneOf` / `allOf` to the first object-or-typed branch."""
    seen = 0
    while isinstance(schema, dict) and seen < 10:
        seen += 1
        ref = schema.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            node: object = root
            for part in ref[2:].split("/"):
                node = node.get(part, {}) if isinstance(node, dict) else {}
            schema = node
            continue
        for key in ("anyOf", "oneOf", "allOf"):
            branches = schema.get(key)
            if isinstance(branches, list):
                typed = [
                    b for b in branches
                    if isinstance(b, dict) and b.get("type") != "null"
                ]
                if typed:
                    schema = typed[0]
                    break
        else:
            return schema
    return schema if isinstance(schema, dict) else {}


def _string_values(prop: dict) -> set[str] | None:
    """Enum / const values of a string property, or None when unconstrained."""
    values = prop.get("enum")
    if values is None and "const" in prop:
        values = [prop["const"]]
    if values is None:
        return None
    return {str(v).lower() for v in values}


def _is_string(prop: dict) -> bool:
    return prop.get("type") == "string" or (
        "enum" in prop and all(isinstance(v, str) for v in prop["enum"])
    )


def check_entry_points() -> None:
    """The schemas `uip codedagent init` generated carry the contract the
    prompt asks for: a ticket in, the chosen bucket plus the original
    ticket text out.

    Field names are the agent's choice — the prompt names none. Asserted:

      * input has a string property (the ticket text);
      * output has a category property: a string whose enum covers
        billing / technical / general, or — without an enum — a plain
        string whose name reads as a category (`category`, `label`, ...).
        An enum that omits a bucket fails;
      * output has a second string property (the echoed ticket text).
    """
    doc = _load_json(ROOT / "entry-points.json")
    entrypoints = doc.get("entryPoints") or []
    if not entrypoints:
        sys.exit("FAIL: entry-points.json has no entryPoints — `uip codedagent init` did not run successfully")
    ep = entrypoints[0]
    stale = (
        "Either `uip codedagent init` ran before the Pydantic models were "
        "written, or the models do not declare the expected fields."
    )

    in_schema = _resolve(ep.get("input") or {}, ep.get("input") or {})
    in_props = {
        k: _resolve(v, ep.get("input") or {})
        for k, v in (in_schema.get("properties") or {}).items()
    }
    if not any(_is_string(v) for v in in_props.values()):
        sys.exit(
            f"FAIL: entry-points.json input schema has no string property for "
            f"the ticket text. {stale} Got input: {json.dumps(ep.get('input'))}"
        )

    out_root = ep.get("output") or {}
    out_schema = _resolve(out_root, out_root)
    out_props = {
        k: _resolve(v, out_root)
        for k, v in (out_schema.get("properties") or {}).items()
    }
    category = None
    for name, prop in out_props.items():
        values = _string_values(prop)
        if values is not None and values & BUCKETS:
            missing = BUCKETS - values
            if missing:
                sys.exit(
                    f"FAIL: output property `{name}` enumerates {sorted(values)} "
                    f"but is missing bucket(s) {sorted(missing)}"
                )
            category = name
            break
    if category is None:
        category = next(
            (n for n, p in out_props.items() if _is_string(p) and _CATEGORY_NAME.search(n)),
            None,
        )
    if category is None:
        sys.exit(
            "FAIL: entry-points.json output schema has no category property — "
            "expected a string enum covering billing / technical / general, or "
            f"a string field named like `category`. {stale} "
            f"Got output: {json.dumps(out_root)}"
        )

    echoes = [n for n, p in out_props.items() if n != category and _is_string(p)]
    if not echoes:
        sys.exit(
            f"FAIL: entry-points.json output schema returns `{category}` but no "
            f"string field carrying the original ticket text. {stale} "
            f"Got output: {json.dumps(out_root)}"
        )
    print(
        f"OK: entry-points.json schemas carry the classifier contract "
        f"(input {sorted(in_props)} -> output category `{category}`, "
        f"ticket text `{echoes[0]}`)"
    )


def check_bindings() -> None:
    load_bindings(ROOT / "bindings.json")
    print("OK: bindings.json envelope is well-formed")


def main() -> None:
    if not ROOT.is_dir():
        sys.exit(f"FAIL: project directory {ROOT} does not exist")
    check_pyproject()
    check_graph_module(find_entry_module(ROOT))
    check_runtime_config()
    check_entry_points()
    check_bindings()


if __name__ == "__main__":
    main()
