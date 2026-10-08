#!/usr/bin/env python3
"""Support case triage — knowledge-grounded decision agent check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. An index context on "UiPathAgentsProductKnowledge" in
     "Shared/uipath-agents" with a valid lowercase retrievalMode.
  3. bindings_v2.json carries the index binding, and the solution provisions
     the index manifest under resources/solution_folder/index/.
  4. Inputs caseSubject / caseDescription / customerTier are templated into
     the messages with contentTokens.
  5. Output contract: resolutionType enum (5 values), suggestedReply,
     docReferences (array), escalateToEngineering (boolean), confidence.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
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

SOLUTION_DIR = Path(os.getcwd()) / "CaseTriageSol"
AGENT_DIR = SOLUTION_DIR / "AgentsCaseTriageAgent"
INDEX_NAME = "UiPathAgentsProductKnowledge"
FOLDER_PATH = "Shared/uipath-agents"
INPUTS = ["caseSubject", "caseDescription", "customerTier"]


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
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_has_fields(in_schema, "inputSchema", {f: [] for f in INPUTS})
    assert_inputs_referenced(agent, INPUTS)
    _, ctx = require_resource(AGENT_DIR, is_index_context(INDEX_NAME), f"index context on {INDEX_NAME!r}")
    assert_index_context(ctx, FOLDER_PATH)
    check_index_binding_and_manifest()
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
