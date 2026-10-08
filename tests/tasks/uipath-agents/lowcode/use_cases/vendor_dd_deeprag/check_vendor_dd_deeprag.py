#!/usr/bin/env python3
"""Vendor due diligence — DeepRAG / JIT grounding over runtime documents check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. `vendorDocuments` is a list of job-attachments (array whose items are the
     canonical JobAttachment definition); `questions` is an array; both are
     templated into the messages.
  3. The run's documents are grounded just-in-time: an enabled built-in
     `deep-rag` tool, or a context with contextType "attachments". A
     pre-built index context does not satisfy the prompt ("we don't keep
     these documents in any index").
  4. Output contract: `answers` array whose items carry question, answer,
     status enum {answered, partially_answered, not_found}, sources (array).
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
    assert_unique_resource_ids,
    attachment_fields,
    fail,
    find_resources,
    load,
    require_resource,
)

AGENT_DIR = Path(os.getcwd()) / "VendorRiskSol" / "VendorDueDiligenceAgent"


def is_jit_grounding(d: dict) -> bool:
    if d.get("$resourceType") == "tool" and d.get("type") == "internal":
        return (d.get("properties") or {}).get("toolType") == "deep-rag"
    return d.get("$resourceType") == "context" and d.get("contextType") == "attachments"


def check_inputs(in_schema: dict) -> None:
    props = in_schema.get("properties") or {}
    docs = props.get("vendorDocuments")
    if not isinstance(docs, dict) or docs.get("type") != "array":
        fail(f"vendorDocuments must be an array of files, got {docs!r}")
    if "vendorDocuments" not in attachment_fields(in_schema):
        fail("vendorDocuments items must be job-attachments")
    if (props.get("questions") or {}).get("type") != "array":
        fail(f"questions must be an array, got {props.get('questions')!r}")
    print("OK: vendorDocuments is a list of job-attachments and questions is an array")


def check_grounding() -> None:
    _, res = require_resource(AGENT_DIR, is_jit_grounding, "DeepRAG tool or attachments context")
    kind = (res.get("properties") or {}).get("toolType") or res.get("contextType")
    indexes = find_resources(
        AGENT_DIR, lambda d: d.get("$resourceType") == "context" and d.get("contextType") == "index"
    )
    if indexes:
        fail(f"documents are run-only — a pre-built index context should not be used, found {[p.parent.name for p, _ in indexes]}")
    print(f"OK: run documents are grounded just-in-time via {kind!r}")


def check_outputs(out_schema: dict) -> None:
    answers = assert_has_fields(out_schema, "outputSchema", {"answers": []})["answers"]
    if answers.get("type") != "array":
        fail(f"answers must be an array, got {answers!r}")
    item_schema = {"type": "object", "properties": {"item": answers}, "definitions": out_schema.get("definitions") or {}}
    f = assert_has_fields(
        item_schema,
        "answers[] item",
        {"question": [], "answer": [], "status": ["answerStatus"], "sources": ["citations"]},
    )
    assert_enum(f["status"], "status", ["answered", "partially_answered", "not_found"])
    if f["sources"].get("type") != "array":
        fail(f"sources must be an array, got {f['sources']!r}")
    print("OK: answers[] items carry question, answer, status and sources")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    check_inputs(in_schema)
    assert_inputs_referenced(agent, ["vendorDocuments", "questions"])
    check_grounding()
    assert_unique_resource_ids(AGENT_DIR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
