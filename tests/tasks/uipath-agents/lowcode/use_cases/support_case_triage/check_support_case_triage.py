#!/usr/bin/env python3
"""Support case triage — knowledge-grounded decision agent check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. An index context on "UiPathAgentsProductKnowledge" in
     "Shared/uipath-agents" with a valid lowercase retrievalMode.
  3. bindings_v2.json carries the index binding, and the solution provisions
     the index manifest under resources/solution_folder/index/.
  4. Inputs, checked structurally (names are the agent's choice): at least
     three inputs (subject, description, tier), one of which carries the tier
     values enterprise/standard as its enum or in its description; every
     input is templated into the messages with contentTokens. Which input is
     the subject or the description is left to the LLM judge.
  5. Output contract: resolutionType enum (5 values), suggestedReply,
     docReferences (array), escalateToEngineering (boolean), confidence.
  Brownfield: the agent must be built inside the existing (fixture) project.
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    _norm,
    _resolve,
    enum_values,
    assert_existing_project,
    assert_autonomous,
    assert_enum,
    assert_has_fields,
    assert_index_context,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    fail,
    is_index_context,
    load,
    require_resource,
)


def _covers(node: dict, expected) -> bool:
    """Structural role signal: enum (or description) spells out every expected value."""
    got = {_norm(v) for v in enum_values(node)}
    if got:
        return all(_norm(v) in got for v in expected)
    desc = str(node.get("description") or "")
    return all(re.search(rf"(?<![A-Za-z0-9_]){re.escape(v)}(?![A-Za-z0-9_])", desc) for v in expected)


def _inputs(in_schema: dict) -> dict:
    return {k: v for k, v in (in_schema.get("properties") or {}).items() if isinstance(v, dict)}


SOLUTION_DIR = Path(os.getcwd()) / "CaseTriageSol"
AGENT_DIR = SOLUTION_DIR / "AgentsCaseTriageAgent"
FIXTURE_AGENT_DIR = Path(__file__).resolve().parent / "_fixtures" / "CaseTriageSol" / "AgentsCaseTriageAgent"
INDEX_NAME = "UiPathAgentsProductKnowledge"
FOLDER_PATH = "Shared/uipath-agents"


def check_index_binding_and_manifest() -> None:
    bindings = load(AGENT_DIR / "bindings_v2.json")
    if not any(
        isinstance(r, dict) and r.get("resource") == "index" and r.get("key") == INDEX_NAME
        for r in bindings.get("resources") or []
    ):
        fail(f"bindings_v2.json has no index binding keyed {INDEX_NAME!r}")
    manifest = SOLUTION_DIR / "resources" / "solution_folder" / "index" / f"{INDEX_NAME}.json"
    if not manifest.is_file():
        fail(f"solution does not provision the index ({manifest.relative_to(SOLUTION_DIR)} missing)")
    print(f"OK: index binding and solution manifest present for {INDEX_NAME!r}")


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {
            "resolutionType": [],
            "suggestedReply": ["reply"],
            "docReferences": ["references", "sources"],
            "escalateToEngineering": ["escalate"],
            "confidence": ["confidenceScore"],
        },
    )
    assert_enum(
        f["resolutionType"],
        "resolutionType",
        ["how_to", "known_limitation", "configuration_issue", "probable_defect", "needs_more_info"],
    )
    if f["docReferences"].get("type") != "array":
        fail(f"docReferences must be an array, got {f['docReferences']!r}")
    if f["escalateToEngineering"].get("type") != "boolean":
        fail(f"escalateToEngineering must be a boolean, got {f['escalateToEngineering']!r}")
    print("OK: docReferences is an array and escalateToEngineering is a boolean")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_existing_project(AGENT_DIR, FIXTURE_AGENT_DIR)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    ins = _inputs(in_schema)
    if len(ins) < 3:
        fail(f"inputSchema must declare the case subject, description and tier (>=3 inputs), found {sorted(ins)}")
    tiers = [k for k, v in ins.items() if _covers(_resolve(in_schema, v), ["enterprise", "standard"])]
    if not tiers:
        fail(f"one input must be the tier, with enterprise/standard as its enum or listed in its description; found {sorted(ins)}")
    print(f"OK: inputs {sorted(ins)}; tier input is {tiers[0]!r}")
    inputs = list(ins)
    assert_inputs_referenced(agent, inputs)
    _, ctx = require_resource(AGENT_DIR, is_index_context(INDEX_NAME), f"index context on {INDEX_NAME!r}")
    assert_index_context(ctx, FOLDER_PATH)
    check_index_binding_and_manifest()
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
