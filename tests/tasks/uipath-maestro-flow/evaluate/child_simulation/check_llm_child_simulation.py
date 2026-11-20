#!/usr/bin/env python3
"""Prove the Llm child simulation is satisfiable on the flow the agent built.

  1. A compiled .flow under ChildSimEval/ has node agent_1 with the tools
     Web_Search and Send_Email wired on its `tool` port.
  2. Each tool's resources/<id>/resource.json under the agent's source folder
     carries a non-empty outputSchema.
  3. Replaying the Llm add for Send_Email exits 0, and so does the remove that
     restores the final state.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("ChildSimEval")
PARENT_ID = "agent_1"
TOOLS = ("Web_Search", "Send_Email")
CHILD = "Send_Email"
EVAL_SET = "Agent Tools"
DATA_POINT = "search-test"
TOOL_PORT = "tool"
CLI_TIMEOUT_SECONDS = 120


def _load(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _find_flow() -> tuple[Path, dict]:
    for path in sorted(ROOT.rglob("*.flow")):
        flow = _load(path)
        if not flow:
            continue
        if any(n.get("id") == PARENT_ID for n in flow.get("nodes", []) if isinstance(n, dict)):
            return path, flow
    sys.exit(f"FAIL: no .flow under {ROOT} has a node with id {PARENT_ID}")


def _wired_sources(flow: dict) -> set[str]:
    nodes = {n.get("id"): n for n in flow.get("nodes", []) if isinstance(n, dict)}
    sources: set[str] = set()
    for edge in flow.get("edges", []):
        if not isinstance(edge, dict):
            continue
        if edge.get("sourceNodeId") != PARENT_ID or edge.get("sourcePort") != TOOL_PORT:
            continue
        node = nodes.get(edge.get("targetNodeId")) or {}
        source = (node.get("inputs") or {}).get("source")
        if isinstance(source, str):
            sources.add(source)
    return sources


def _check_resources(flow_dir: Path, flow: dict) -> None:
    agent = next(n for n in flow["nodes"] if n.get("id") == PARENT_ID)
    source = (agent.get("inputs") or {}).get("source")
    if not isinstance(source, str) or not source:
        sys.exit(f"FAIL: node {PARENT_ID} has no inputs.source")

    wired = _wired_sources(flow)
    schemas: dict[str, object] = {}
    for path in (flow_dir / source / "resources").glob("*/resource.json"):
        resource = _load(path) or {}
        if resource.get("id") in wired:
            schemas[str(resource.get("name"))] = resource.get("outputSchema")
    for tool in TOOLS:
        schema = schemas.get(tool)
        props = schema.get("properties") if isinstance(schema, dict) else None
        if not props:
            sys.exit(
                f"FAIL: tool {tool} wired to {PARENT_ID} has no resource.json with a non-empty "
                f"outputSchema. Wired tools: {sorted(schemas)}; got: {schema!r}"
            )
    print(f"OK: {PARENT_ID} wires {TOOLS} with non-empty output schemas")


def _eval(flow_dir: Path, *args: str) -> None:
    cmd = [
        "uip", "maestro", "flow", "eval", "simulation", *args,
        "--parent", PARENT_ID, "--set", EVAL_SET, "--data-point", DATA_POINT,
        "--path", str(flow_dir), "--output", "json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=CLI_TIMEOUT_SECONDS)
    if result.returncode != 0:
        sys.exit(f"FAIL: `{' '.join(cmd)}` exited {result.returncode}: {(result.stdout + result.stderr)[-600:]}")


def main() -> None:
    flow_path, flow = _find_flow()
    flow_dir = flow_path.parent
    _check_resources(flow_dir, flow)
    _eval(
        flow_dir, "add", CHILD, "--strategy", "Llm",
        "--simulation-instructions", "Return a success status with a message ID.",
    )
    _eval(flow_dir, "remove", CHILD)
    print(f"OK: Llm add and remove of {CHILD} on {PARENT_ID} exit 0")


if __name__ == "__main__":
    main()
