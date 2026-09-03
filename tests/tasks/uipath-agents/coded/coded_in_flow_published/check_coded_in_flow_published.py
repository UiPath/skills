#!/usr/bin/env python3
"""Flow Integration Pattern 2 (Published coded agent) shape check.

Asserts:
  1. A `.flow` file exists somewhere under a `triage-flow` project that
     is NOT colocated with the coded agent (no
     `resources/solution_folder/process/agent/<name>.json` sibling — that
     would indicate Pattern 1, not Pattern 2).
  2. The flow file contains at least one node of type
     `uipath.core.agent.<resourceKey>`.
  3. The agent node's `definitions[]` entry carries the Pattern 2 marker:
     either `model.section == "Published"` (legacy registry output) or —
     per current registry output, which omits `model.section` entirely —
     `category == "agent.published"`. Matches `flow-integration.md`'s
     Pattern Comparison table (`"Published"` or absent).
  4. The flow file does NOT contain `"In this solution"` for that node
     (would indicate Pattern 1).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

CWD = Path(os.getcwd())
FLOW_PROJECT_HINT = "triage-flow"
AGENT_PROJECT_HINT = "tone-classifier"


def fail(msg: str) -> None:
    sys.exit(f"FAIL: {msg}")


def discover_flow_file() -> Path:
    candidates = list(CWD.rglob("*.flow"))
    if not candidates:
        fail("no .flow file found anywhere under the working tree")
    triage = [p for p in candidates if FLOW_PROJECT_HINT in str(p)]
    if triage:
        return triage[0]
    return candidates[0]


def assert_pattern_2_not_pattern_1(flow_path: Path) -> dict:
    text = flow_path.read_text(encoding="utf-8")
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        fail(f"{flow_path} is not valid JSON: {exc}")

    agent_nodes = re.findall(r'"uipath\.core\.agent\.[0-9a-fA-F-]{8,}"', text)
    if not agent_nodes:
        fail(
            f"{flow_path} contains no `uipath.core.agent.<resourceKey>` node — "
            "the flow must reference the published agent"
        )
    print(f"OK: flow references a uipath.core.agent.<key> node ({len(agent_nodes)} occurrence(s))")

    if '"In this solution"' in text:
        fail(
            f"{flow_path} references the agent with `section: \"In this solution\"` — "
            "that is Pattern 1 (in-solution). This test verifies Pattern 2 (Published). "
            "The agent must be referenced as a Published resource."
        )

    agent_defs = [
        dfn
        for dfn in doc.get("definitions", [])
        if isinstance(dfn, dict)
        and str(dfn.get("nodeType", "")).startswith("uipath.core.agent.")
    ]
    if not agent_defs:
        fail(
            f"{flow_path} has no `definitions[]` entry for a "
            "`uipath.core.agent.<resourceKey>` node — the definition must be "
            "copied verbatim from `uip maestro flow registry get`"
        )
    for dfn in agent_defs:
        node_type = dfn.get("nodeType")
        section = (dfn.get("model") or {}).get("section")
        category = dfn.get("category")
        # Pattern 2 marker: legacy registry output set model.section to
        # "Published"; current registry output omits model.section and sets
        # category to "agent.published" instead. Accept either.
        if section == "Published" or (section is None and category == "agent.published"):
            continue
        fail(
            f"{flow_path} definition for `{node_type}` is not Pattern 2 "
            f"(Published): model.section={section!r}, category={category!r}. "
            "Expected model.section == 'Published' or (model.section absent "
            "and category == 'agent.published')."
        )
    print(
        "OK: agent definition carries the Published marker "
        "(`model.section: \"Published\"` or `category: \"agent.published\"`) (Pattern 2)"
    )

    return doc


def assert_not_in_solution_sibling() -> None:
    # Pattern 1 places the resource manifest at
    # `<Solution>/resources/solution_folder/process/agent/<name>.json`.
    # Pattern 2 should NOT have one — the agent is a tenant-level resource,
    # not a solution-local one.
    matches = list(CWD.rglob("resources/solution_folder/process/agent/*.json"))
    if matches:
        fail(
            "found in-solution resource manifest(s) at "
            + ", ".join(str(p.relative_to(CWD)) for p in matches)
            + " — these indicate Pattern 1 (in-solution), not Pattern 2 (published). "
            "The coded agent must NOT be registered as a sibling of the flow."
        )
    print("OK: no in-solution resource manifest exists (correctly publishes as Pattern 2)")


def main() -> None:
    flow_path = discover_flow_file()
    print(f"OK: discovered flow file {flow_path.relative_to(CWD)}")
    assert_pattern_2_not_pattern_1(flow_path)
    assert_not_in_solution_sibling()

    agent_marker = next(CWD.rglob(f"{AGENT_PROJECT_HINT}/langgraph.json"), None)
    if agent_marker is None:
        fail(
            f"coded agent project `{AGENT_PROJECT_HINT}` is missing its langgraph.json "
            "— the agent must be a LangGraph project before it can be deployed and referenced"
        )
    print(f"OK: coded agent LangGraph marker present at {agent_marker.relative_to(CWD)}")

    print("OK: Pattern 2 (Published coded agent) wiring verified")


if __name__ == "__main__":
    main()
