#!/usr/bin/env python3
"""Invoice vs PO validation — document extraction and validation agent check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync with entry-points.json.
  2. `invoiceFile` is a job-attachment input (canonical definitions block with
     x-uipath-resource-kind: JobAttachment); `purchaseOrder` is an object.
  3. A file-reading built-in tool (analyze-attachments / load-attachments /
     deep-rag) is enabled — the only way a low-code agent reads file contents.
  4. Both inputs reach the LLM via templated messages with contentTokens.
  5. Output contract: extractedInvoice, validationIssues (array), status enum
     {approved, needs_review, rejected}, confidence (number).
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
    is_file_reading_tool,
    load,
    require_resource,
)

AGENT_DIR = Path(os.getcwd()) / "InvoiceValidationSol" / "InvoiceValidationAgent"


def check_inputs(in_schema: dict) -> None:
    files = attachment_fields(in_schema)
    if "invoiceFile" not in files:
        fail(f"invoiceFile must be a job-attachment input; job-attachment inputs found: {files}")
    po = (in_schema.get("properties") or {}).get("purchaseOrder")
    if not isinstance(po, dict) or po.get("type") != "object":
        fail(f"purchaseOrder must be an object input, got {po!r}")
    print("OK: invoiceFile is a job-attachment and purchaseOrder is an object")


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
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    check_inputs(in_schema)
    require_resource(AGENT_DIR, is_file_reading_tool, "file-reading built-in tool")
    assert_unique_resource_ids(AGENT_DIR)
    assert_inputs_referenced(agent, ["invoiceFile", "purchaseOrder"])
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
