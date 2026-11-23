#!/usr/bin/env python3
"""Flow Integration Pattern 2 (Published coded agent) shape check.

Asserts:
  1. A `.flow` file exists somewhere under a `triage-flow` project, and the
     agent is NOT registered in that solution (Pattern 1): no `.uipx` lists a
     non-flow project, and any `resources/solution_folder/process/agent/*.json`
     is the imported published process (`uip solution resources refresh`),
     not a project-backed manifest. See `assert_not_in_solution_sibling`.
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


def _agent_node_keys(doc: dict) -> set[str]:
    prefix = "uipath.core.agent."
    return {
        # GUIDs are case-insensitive; the flow node and the imported manifest
        # spell the same key in different cases.
        str(dfn.get("nodeType"))[len(prefix):].lower()
        for dfn in doc.get("definitions", [])
        if isinstance(dfn, dict) and str(dfn.get("nodeType", "")).startswith(prefix)
    }


def _flow_solution_root(flow_path: Path) -> Path:
    """Nearest ancestor of the flow file that holds a `.uipx`, else CWD.

    Scopes the Pattern 1 scan to the flow's own solution: a separate solution
    wrapping the agent (a legitimate way to publish it) is not graded here.
    """
    for parent in flow_path.parents:
        if any(parent.glob("*.uipx")):
            return parent
        if parent == CWD:
            break
    return CWD


def assert_not_in_solution_sibling(doc: dict, flow_path: Path) -> None:
    """The agent is not registered as an in-solution project (Pattern 1).

    A file under `resources/solution_folder/process/agent/` is NOT by itself a
    Pattern 1 signal. `uip solution resources refresh` (recommended by the
    `flow init` NextSteps) imports the published tenant process there too.
    The two shapes differ:

    * Pattern 1 (project-backed): the solution's `.uipx` lists an Agent project,
      and the manifest carries `resource.projectKey` = that project's `Id`;
      `spec.package` is only `{key: <local GUID>}`.
    * Pattern 2 import: no `projectKey`, `spec.package` names the tenant-feed
      package (`{name, key: "<name>:<version>"}`), and `resource.key` equals the
      flow node's `uipath.core.agent.<GUID>`.
    """
    root = _flow_solution_root(flow_path)
    for uipx in root.rglob("*.uipx"):
        if ".venv" in uipx.parts or "node_modules" in uipx.parts:
            continue
        try:
            projects = json.loads(uipx.read_text(encoding="utf-8")).get("Projects") or []
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            fail(f"{uipx.relative_to(CWD)} is not a valid solution manifest")
        others = [
            p for p in projects
            if isinstance(p, dict) and str(p.get("Type", "")).lower() != "flow"
        ]
        if others:
            fail(
                f"{uipx.relative_to(CWD)} registers non-flow project(s) "
                + ", ".join(f"{p.get('Type')}:{p.get('ProjectRelativePath')}" for p in others)
                + " — the agent is an in-solution sibling of the flow (Pattern 1), "
                "not a published resource (Pattern 2)."
            )

    node_keys = _agent_node_keys(doc)
    manifests = list(root.rglob("resources/solution_folder/process/agent/*.json"))
    for path in manifests:
        rel = path.relative_to(CWD)
        try:
            resource = json.loads(path.read_text(encoding="utf-8")).get("resource") or {}
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            fail(f"{rel} is not a valid resource manifest")
        package = (resource.get("spec") or {}).get("package") or {}
        if resource.get("projectKey"):
            fail(
                f"{rel} is project-backed (projectKey={resource.get('projectKey')!r}) — "
                "the agent is registered in the solution (Pattern 1), not consumed as a "
                "published resource (Pattern 2)."
            )
        if not package.get("name"):
            fail(
                f"{rel} has no tenant-feed `spec.package.name` (spec.package={package!r}) — "
                "it is not an imported published process, so it indicates Pattern 1."
            )
        if str(resource.get("key") or "").lower() not in node_keys:
            fail(
                f"{rel} key {resource.get('key')!r} matches no flow agent node "
                f"({sorted(node_keys)!r}) — an agent manifest the flow does not consume."
            )
        print(
            f"OK: {rel} is the imported published process "
            f"(package {package.get('key')!r}, key matches the flow node) — expected for Pattern 2"
        )
    print("OK: agent is not registered as an in-solution project (Pattern 2)")


def main() -> None:
    flow_path = discover_flow_file()
    print(f"OK: discovered flow file {flow_path.relative_to(CWD)}")
    doc = assert_pattern_2_not_pattern_1(flow_path)
    assert_not_in_solution_sibling(doc, flow_path)

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
