#!/usr/bin/env python3
"""Invoice vs PO validation — document extraction and validation agent check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. The invoice file is a job-attachment input and the purchase order an
     object input (names are the agent's choice).
  3. A file-reading built-in tool (analyze-attachments / load-attachments /
     deep-rag) is enabled — the only way a low-code agent reads file contents.
  4. Both inputs reach the LLM via templated messages with contentTokens.
  5. Output contract: extractedInvoice, validationIssues (array), status enum
     {approved, needs_review, rejected}, confidence (number).
  Brownfield: the agent must be built inside the existing (fixture) project.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_existing_project,
    require_input,
    assert_autonomous,
    assert_enum,
    assert_has_fields,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    assert_unique_resource_ids,
    attachment_fields,
    fail,
    is_file_reading_tool,
    load,
    require_resource,
)

AGENT_DIR = Path(os.getcwd()) / "InvoiceValidationSol" / "InvoiceValidationAgent"
FIXTURE_AGENT_DIR = Path(__file__).resolve().parent / "_fixtures" / "InvoiceValidationSol" / "InvoiceValidationAgent"


def check_inputs(in_schema: dict) -> list[str]:
    files = attachment_fields(in_schema)
    if len(files) != 1:
        fail(f"expected exactly one job-attachment input for the invoice file, found {files}")
    po = require_input(in_schema, "purchase order", "purchaseOrder", "po", "purchaseOrderData", "sapPurchaseOrder", type_="object")
    print(f"OK: invoice file input {files[0]!r} is a job-attachment")
    return [files[0], po]


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {
            "extractedInvoice": ["invoice", "extractedData"],
            "validationIssues": ["issues"],
            "status": ["validationStatus"],
            "confidence": ["confidenceScore"],
        },
    )
    if f["validationIssues"].get("type") != "array":
        fail(f"validationIssues must be an array, got {f['validationIssues']!r}")
    assert_enum(f["status"], "status", ["approved", "needs_review", "rejected"])
    if f["confidence"].get("type") not in ("number", "integer"):
        fail(f"confidence must be numeric, got {f['confidence']!r}")
    print("OK: validationIssues is an array and confidence is numeric")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_existing_project(AGENT_DIR, FIXTURE_AGENT_DIR)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    inputs = check_inputs(in_schema)
    require_resource(AGENT_DIR, is_file_reading_tool, "file-reading built-in tool")
    assert_unique_resource_ids(AGENT_DIR)
    assert_inputs_referenced(agent, inputs)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
