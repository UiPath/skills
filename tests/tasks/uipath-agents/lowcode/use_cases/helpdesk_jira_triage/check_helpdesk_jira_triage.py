#!/usr/bin/env python3
"""Helpdesk Jira triage — external-system (IS) agent with memory check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync; inputs templated.
  2. An Integration Service tool on connector `uipath-atlassian-jira` whose
     activity creates an issue, bound to the "jira-coded-eval" connection and
     passing the Studio Web silent-drop rules (connection id/resourceKey,
     folder key/path, isDefault=false, iconUrl, enumValues shape).
  3. The PRODEV project is targeted — as a static tool parameter or in the
     system prompt.
  4. The solution provisions a Jira connection resource.
  5. A memorySpace feature attaches "UiPathAgentsSupportMemory" from
     "Shared/uipath-agents" with dynamic few-shot recall over `description`.
  6. Output contract: category enum (5), priority enum P1–P4, jiraIssueKey,
     summary.
"""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_autonomous,
    assert_connection_provisioned,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_integration_wiring,
    assert_project_id,
    assert_schema_sync,
    fail,
    is_integration_tool,
    load,
    require_resource,
    system_prompt,
)

SOLUTION_DIR = Path(os.getcwd()) / "HelpdeskSol"
AGENT_DIR = SOLUTION_DIR / "HelpdeskTriageAgent"
CONNECTOR = "uipath-atlassian-jira"
CONNECTION_NAME = "jira-coded-eval"
MEMORY_SPACE = "UiPathAgentsSupportMemory"
FOLDER_PATH = "Shared/uipath-agents"
INPUTS = ["requesterEmail", "title", "description"]


def is_create_issue(object_name: str) -> bool:
    lowered = object_name.lower()
    return "issue" in lowered and "create" in lowered


def check_jira_tool(agent: dict) -> None:
    _, tool = require_resource(
        AGENT_DIR, is_integration_tool(CONNECTOR, is_create_issue), "Jira create-issue IS tool"
    )
    conn = assert_integration_wiring(tool)
    if conn.get("name") != CONNECTION_NAME:
        fail(f"Jira tool must use the {CONNECTION_NAME!r} connection, got {conn.get('name')!r}")
    params = json.dumps((tool.get("properties") or {}).get("parameters") or [])
    if "PRODEV" not in params and "PRODEV" not in system_prompt(agent):
        fail("PRODEV project is neither a tool parameter value nor named in the system prompt")
    print(f"OK: Jira tool targets PRODEV via connection {CONNECTION_NAME!r}")


def check_memory() -> None:
    features = []
    for path in sorted((AGENT_DIR / "features").glob("*/feature.json")):
        data = load(path)
        if data.get("$featureType") == "memorySpace":
            features.append((path, data))
    if not features:
        fail(f"no memorySpace feature under {AGENT_DIR.name}/features")
    hits = [
        (p, d) for p, d in features
        if d.get("memorySpaceName") == MEMORY_SPACE and d.get("folderPath") == FOLDER_PATH
    ]
    if not hits:
        got = [(d.get("memorySpaceName"), d.get("folderPath")) for _, d in features]
        fail(f"no memory feature attaches {MEMORY_SPACE!r} in {FOLDER_PATH!r}; got {got}")
    path, feature = hits[0]
    if not feature.get("isEnabled"):
        fail(f"memory feature {path.parent.name} is disabled")
    few_shot = feature.get("dynamicFewShotSettings") or {}
    if few_shot.get("isEnabled") is not True:
        fail("memory feature must enable dynamic few-shot recall of past cases")
    fields = [f.get("name") for f in few_shot.get("fieldSettings") or [] if isinstance(f, dict)]
    if "description" not in fields:
        fail(f"memory recall should match on the `description` input, got fieldSettings {fields}")
    print(f"OK: memory feature {path.parent.name!r} recalls {MEMORY_SPACE!r} by description")


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {"category": [], "priority": [], "jiraIssueKey": ["issueKey"], "summary": []},
    )
    assert_enum(f["category"], "category", ["access", "hardware", "software", "network", "other"])
    assert_enum(f["priority"], "priority", ["P1", "P2", "P3", "P4"])


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_has_fields(in_schema, "inputSchema", {f: [] for f in INPUTS})
    assert_inputs_referenced(agent, INPUTS)
    check_jira_tool(agent)
    assert_connection_provisioned(SOLUTION_DIR, CONNECTOR)
    check_memory()
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
