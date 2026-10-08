#!/usr/bin/env python3
"""Dispute desk — multi-agent (supervisor + narrow agents) check.

Final-state only. Validates:
  1. Three autonomous agents, registered in the solution, with distinct
     projectIds and schemas in sync with their entry-points.json.
  2. DisputeClassifierAgent outputs disputeType / sentiment enums;
     ReplyDrafterAgent outputs subject / body; neither declares tools.
  3. DisputeCoordinatorAgent takes customerMessage (string) + invoice
     (object), both templated, and returns disputeType, sentiment,
     proposedResolution, replySubject, replyBody.
  4. The coordinator declares one solution-internal agent tool per child
     (type=agent, location=solution, processName=<child>,
     folderPath=solution_folder) whose input/output schemas are
     shape-equivalent to the child's own schemas (descriptions ignored).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_autonomous,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    assert_solution_registers,
    assert_unique_resource_ids,
    fail,
    load,
    resources,
)

SOLUTION_DIR = Path(os.getcwd()) / "DisputeDeskSol"
CLASSIFIER = "DisputeClassifierAgent"
DRAFTER = "ReplyDrafterAgent"
COORDINATOR = "DisputeCoordinatorAgent"


def load_agent(name: str) -> tuple[dict, dict, dict]:
    agent_dir = SOLUTION_DIR / name
    agent = load(agent_dir / "agent.json")
    entry = load(agent_dir / "entry-points.json")
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    return agent, in_schema, out_schema


def strip_descriptions(node):
    if isinstance(node, dict):
        return {k: strip_descriptions(v) for k, v in node.items() if k not in ("description", "title")}
    if isinstance(node, list):
        return [strip_descriptions(i) for i in node]
    return node


def check_children(agents: dict) -> None:
    _, _, cls_out = agents[CLASSIFIER]
    f = assert_has_fields(cls_out, f"{CLASSIFIER}.outputSchema", {"disputeType": [], "sentiment": []})
    assert_enum(f["disputeType"], "disputeType", ["pricing", "duplicate_charge", "tax", "service_not_received", "other"])
    assert_enum(f["sentiment"], "sentiment", ["positive", "neutral", "negative", "angry"])
    _, _, dr_out = agents[DRAFTER]
    assert_has_fields(dr_out, f"{DRAFTER}.outputSchema", {"subject": [], "body": []})
    for child in (CLASSIFIER, DRAFTER):
        tools = [p.parent.name for p, d in resources(SOLUTION_DIR / child) if d.get("$resourceType") == "tool"]
        if tools:
            fail(f"{child} is a narrow single-purpose agent and should not declare tools, found {tools}")
    print("OK: child agents are tool-free with their own contracts")


def check_coordinator(agents: dict) -> None:
    agent, in_schema, out_schema = agents[COORDINATOR]
    props = in_schema.get("properties") or {}
    if (props.get("customerMessage") or {}).get("type") != "string":
        fail("coordinator input customerMessage must be a string")
    if (props.get("invoice") or {}).get("type") != "object":
        fail("coordinator input invoice must be an object")
    assert_inputs_referenced(agent, ["customerMessage", "invoice"])
    assert_has_fields(
        out_schema,
        f"{COORDINATOR}.outputSchema",
        {
            "disputeType": [],
            "sentiment": [],
            "proposedResolution": ["resolution"],
            "replySubject": [],
            "replyBody": [],
        },
    )

    coord_dir = SOLUTION_DIR / COORDINATOR
    assert_unique_resource_ids(coord_dir)
    agent_tools = {
        (d.get("properties") or {}).get("processName"): d
        for _, d in resources(coord_dir)
        if d.get("$resourceType") == "tool" and d.get("type") == "agent"
    }
    for child in (CLASSIFIER, DRAFTER):
        tool = agent_tools.get(child)
        if tool is None:
            fail(f"{COORDINATOR} has no agent tool with processName={child!r}; found {sorted(k for k in agent_tools if k)}")
        if tool.get("location") != "solution":
            fail(f"tool {child} must be solution-internal (location='solution'), got {tool.get('location')!r}")
        if (tool.get("properties") or {}).get("folderPath") != "solution_folder":
            fail(f"tool {child} properties.folderPath must be 'solution_folder'")
        if not tool.get("isEnabled", True):
            fail(f"tool {child} is disabled")
        _, child_in, child_out = agents[child]
        for label, mine, theirs in (("inputSchema", tool.get("inputSchema"), child_in), ("outputSchema", tool.get("outputSchema"), child_out)):
            if strip_descriptions(mine) != strip_descriptions(theirs):
                fail(f"tool {child}.{label} does not match {child}/agent.json {label} (descriptions ignored)")
        print(f"OK: coordinator calls {child} as a solution agent tool with matching schemas")


def main() -> None:
    assert_solution_registers(SOLUTION_DIR, [CLASSIFIER, DRAFTER, COORDINATOR])
    agents = {name: load_agent(name) for name in (CLASSIFIER, DRAFTER, COORDINATOR)}
    ids = [assert_project_id(a[0]) for a in agents.values()]
    if len(set(ids)) != len(ids):
        fail(f"agents share a projectId (Anti-pattern 8): {ids}")
    print("OK: three distinct projectIds")
    check_children(agents)
    check_coordinator(agents)


if __name__ == "__main__":
    main()
