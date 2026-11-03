#!/usr/bin/env python3
"""Dispute desk — multi-agent (supervisor + narrow agents) check.

The prompt names neither the solution nor the agents, so everything is located
by role. Final-state only. Validates:
  1. Exactly one solution in the sandbox, registering exactly three autonomous
     low-code agents with distinct projectIds and schemas in sync.
  2. Classifier: outputs disputeType (pricing, duplicate_charge, tax,
     service_not_received, other) and a sentiment field (positive, neutral,
     negative, angry); declares no tools.
  3. Drafter: outputs subject and body; declares no tools.
  4. Coordinator: takes the customer's message and the invoice (types are
     the agent's choice), both templated; returns disputeType, sentiment,
     proposedResolution, replySubject, replyBody; declares one
     solution-internal agent tool per child (type=agent, location=solution,
     processName=<child project>, folderPath=solution_folder) whose schemas
     are shape-equivalent to the child's own (descriptions ignored).
The coordinator's agent.json is copied to .grading/coordinator-agent.json so
the task's llm_judge (which runs after this criterion and needs a fixed path)
can read it.

`--validate` instead runs read-only `uip agent validate` on all three agents.
"""

import os
import shutil
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
    assert_unique_resource_ids,
    assert_valid_project,
    fail,
    find_property,
    load,
    require_input,
    resources,
    strip_schema,
    walk_properties,
)

ROOT = Path(os.getcwd())
GRADING_COPY = ROOT / ".grading" / "coordinator-agent.json"
DISPUTE_TYPES = ["pricing", "duplicate_charge", "tax", "service_not_received", "other"]
SENTIMENTS = ["positive", "neutral", "negative", "angry"]


def find_solution() -> Path:
    uipx = [p for p in ROOT.glob("*/*.uipx")] + [p for p in ROOT.glob("*.uipx")]
    if len(uipx) != 1:
        fail(f"expected exactly one solution (.uipx) in the workspace, found {[str(p.relative_to(ROOT)) for p in uipx]}")
    return uipx[0]


def agent_dirs(uipx: Path) -> list[Path]:
    sol = uipx.parent
    dirs = []
    for proj in load(uipx).get("Projects") or []:
        d = (sol / proj.get("ProjectRelativePath", "")).parent
        a = d / "agent.json"
        if a.is_file() and load(a).get("type") == "lowCode":
            dirs.append(d)
    if len(dirs) != 3:
        fail(f"expected three low-code agents registered in {uipx.name}, found {[d.name for d in dirs]}")
    print(f"OK: {uipx.name} registers three agents: {[d.name for d in dirs]}")
    return dirs


def tools(d: Path) -> list[dict]:
    return [r for _, r in resources(d) if r.get("$resourceType") == "tool"]


def outputs(d: Path) -> dict:
    return walk_properties(load(d / "agent.json").get("outputSchema") or {})


def identify(dirs: list[Path]) -> tuple[Path, Path, Path]:
    coordinator = [d for d in dirs if sum(1 for t in tools(d) if t.get("type") == "agent") >= 2]
    if len(coordinator) != 1:
        fail(f"expected exactly one coordinator agent with two agent tools, found {[d.name for d in coordinator]}")
    coord = coordinator[0]
    rest = [d for d in dirs if d != coord]
    classifier = [d for d in rest if find_property(outputs(d), "disputeType")]
    drafter = [d for d in rest if find_property(outputs(d), "subject") and find_property(outputs(d), "body")]
    if len(classifier) != 1 or len(drafter) != 1 or classifier == drafter:
        fail(f"could not tell classifier from drafter among {[d.name for d in rest]}")
    print(f"OK: coordinator={coord.name}, classifier={classifier[0].name}, drafter={drafter[0].name}")
    return coord, classifier[0], drafter[0]


def check_children(classifier: Path, drafter: Path) -> None:
    cls_out = load(classifier / "agent.json").get("outputSchema") or {}
    f = assert_has_fields(cls_out, f"{classifier.name}.outputSchema", {"disputeType": [], "sentiment": ["customerSentiment"]})
    assert_enum(f["disputeType"], "disputeType", DISPUTE_TYPES)
    assert_enum(f["sentiment"], "sentiment", SENTIMENTS)
    for child in (classifier, drafter):
        if tools(child):
            fail(f"{child.name} is a narrow single-purpose agent and should not declare tools")
    print("OK: classifier and drafter are tool-free with their own contracts")


def check_coordinator(coord: Path, children: list[Path]) -> None:
    agent = load(coord / "agent.json")
    in_schema, out_schema = assert_schema_sync(agent, load(coord / "entry-points.json"))
    # The prompt says only "the customer's message and invoice" — types are the agent's choice.
    msg = require_input(in_schema, "customer message", "customerMessage", "message", "customerMessageText", "disputeMessage")
    inv = require_input(in_schema, "invoice", "invoice", "invoiceDetails", "invoiceData")
    assert_inputs_referenced(agent, [msg, inv])
    assert_has_fields(
        out_schema,
        f"{coord.name}.outputSchema",
        {"disputeType": [], "sentiment": [], "proposedResolution": ["resolution"], "replySubject": [], "replyBody": []},
    )
    assert_unique_resource_ids(coord)
    by_name = {(t.get("properties") or {}).get("processName"): t for t in tools(coord) if t.get("type") == "agent"}
    for child in children:
        tool = by_name.get(child.name)
        if tool is None:
            fail(f"{coord.name} has no agent tool with processName={child.name!r}; found {sorted(k for k in by_name if k)}")
        if tool.get("location") != "solution":
            fail(f"tool {child.name} must be solution-internal (location='solution'), got {tool.get('location')!r}")
        if (tool.get("properties") or {}).get("folderPath") != "solution_folder":
            fail(f"tool {child.name} properties.folderPath must be 'solution_folder'")
        child_agent = load(child / "agent.json")
        for label in ("inputSchema", "outputSchema"):
            if strip_schema(tool.get(label)) != strip_schema(child_agent.get(label)):
                fail(f"tool {child.name}.{label} does not match {child.name}/agent.json {label} (descriptions ignored)")
        print(f"OK: coordinator calls {child.name} as a solution agent tool with matching schemas")


def main() -> None:
    dirs = agent_dirs(find_solution())
    if "--validate" in sys.argv:
        for d in dirs:
            assert_valid_project(d)
        return
    ids = []
    for d in dirs:
        a = load(d / "agent.json")
        ids.append(assert_project_id(a))
        assert_autonomous(a)
        assert_schema_sync(a, load(d / "entry-points.json"))
    if len(set(ids)) != len(ids):
        fail(f"agents share a projectId (Anti-pattern 8): {ids}")
    coord, classifier, drafter = identify(dirs)
    GRADING_COPY.parent.mkdir(exist_ok=True)
    shutil.copyfile(coord / "agent.json", GRADING_COPY)
    check_children(classifier, drafter)
    check_coordinator(coord, [classifier, drafter])


if __name__ == "__main__":
    main()
