#!/usr/bin/env python3
"""End-to-end check for the in-solution sibling coded-agent + Flow scenario.

Asserts:

  1. The local resource file exists with a non-empty `key`, written by
     `uip solution project add`:
       resources/solution_folder/process/agent/InputProcessor.json

  2. The Flow file `GreeterSol/GreeterFlow/GreeterFlow.flow` contains
     exactly one `uipath.core.agent.<resourceKey>` node instance in
     `nodes[]` whose suffix matches the resource.key.

  3. The flow's top-level `bindings[]` array has at least one entry per
     `(resourceKey, propertyAttribute)` pair tied to the agent, AND no
     duplicate `(resourceKey, propertyAttribute)` pairs (dedupe rule
     documented in `agent/impl.md`).

  4. The coded agent's `main.py` obeys the lazy-LLM-init invariant — no
     module-level construction of `UiPath()`, `UiPathChat()`, etc.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from _shared.ast_lazy_init_check import find_module_level_llm_clients  # noqa: E402

CWD = Path(os.getcwd())
SOL = CWD / "GreeterSol"
FLOW = SOL / "GreeterFlow" / "GreeterFlow.flow"
CODED_RESOURCE = SOL / "resources" / "solution_folder" / "process" / "agent" / "InputProcessor.json"
CODED_MAIN = SOL / "InputProcessor" / "main.py"

AGENT_NODE_TYPE_PREFIX = "uipath.core.agent."


def _load_json(path: Path) -> dict:
    if not path.is_file():
        sys.exit(f"FAIL: missing {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {path} is not valid JSON: {e}")


def _read_resource_key(path: Path, label: str) -> str:
    doc = _load_json(path)
    key = doc.get("key") or doc.get("resource", {}).get("key")
    if not isinstance(key, str) or not key.strip():
        sys.exit(f"FAIL: {label} resource file at {path} has no `key` (got {key!r})")
    print(f"OK: {label} resource.key = {key}")
    return key


def main() -> None:
    coded_key = _read_resource_key(CODED_RESOURCE, "coded agent")

    flow = _load_json(FLOW)
    nodes = flow.get("nodes") or []
    bindings = flow.get("bindings") or []

    agent_nodes = [n for n in nodes if isinstance(n, dict)
                   and isinstance(n.get("type"), str)
                   and n["type"].startswith(AGENT_NODE_TYPE_PREFIX)]
    if len(agent_nodes) != 1:
        sys.exit(
            f"FAIL: expected exactly one `{AGENT_NODE_TYPE_PREFIX}<key>` node "
            f"in {FLOW.name}, found {len(agent_nodes)}: "
            f"{[n.get('type') for n in agent_nodes]}"
        )
    print(f"OK: flow has {len(agent_nodes)} agent node")

    suffixes = {n["type"][len(AGENT_NODE_TYPE_PREFIX):] for n in agent_nodes}
    if coded_key not in suffixes:
        sys.exit(
            f"FAIL: no flow node with type `{AGENT_NODE_TYPE_PREFIX}{coded_key}` "
            f"(coded agent). Found suffixes: {sorted(suffixes)}"
        )
    print(f"OK: flow node binds the coded agent via type suffix {coded_key}")

    agent_bindings = [b for b in bindings
                      if isinstance(b, dict) and b.get("resourceKey") == coded_key]
    if not agent_bindings:
        sys.exit(
            f"FAIL: top-level bindings[] has no entry with "
            f"resourceKey=={coded_key!r}"
        )
    print(f"OK: bindings[] has {len(agent_bindings)} entry/entries for the coded agent")

    seen: dict[tuple[str, str], int] = {}
    for b in bindings:
        if not isinstance(b, dict):
            continue
        rk = b.get("resourceKey")
        attr = b.get("propertyAttribute")
        if rk is None or attr is None:
            continue
        seen[(rk, attr)] = seen.get((rk, attr), 0) + 1
    duplicates = {k: c for k, c in seen.items() if c > 1}
    if duplicates:
        sys.exit(
            "FAIL: bindings[] has duplicate (resourceKey, propertyAttribute) "
            f"entries: {duplicates}. Each pair must appear exactly once — "
            "node instances referencing the same agent must reuse the same "
            "bindings[].id."
        )
    print(f"OK: bindings[] has no duplicate (resourceKey, propertyAttribute) pairs ({len(seen)} unique)")

    violations = find_module_level_llm_clients(CODED_MAIN)
    if violations:
        sys.exit("FAIL: " + " | ".join(violations))
    print(f"OK: {CODED_MAIN.name} obeys lazy-LLM-init invariant")


if __name__ == "__main__":
    main()
