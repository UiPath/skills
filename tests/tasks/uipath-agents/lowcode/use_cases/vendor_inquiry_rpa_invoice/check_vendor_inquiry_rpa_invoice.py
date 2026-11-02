#!/usr/bin/env python3
"""Vendor inquiry — document + RPA (file returned by an RPA tool) check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync; vendor-name and inquiry inputs
     (names are the agent's choice) templated.
  2. A solution-local RPA process tool for the "DownloadVendorInvoice"
     project already in the solution (type=process, location=solution,
     folderPath=solution_folder, UUID referenceKey) whose input/output schemas
     mirror that project's entry-points.json (descriptions ignored). In
     particular the `invoiceFile` File output must be a job-attachment —
     mapping it to a string is the attachment-passing failure under test.
  3. A file-reading built-in tool is enabled to read the returned PDF.
  4. Output contract: invoiceNumber, invoiceFound (boolean), invoiceAmount,
     dueDate, reply, needsHumanFollowUp (boolean).
  Brownfield: the agent must be built inside the existing (fixture) project.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
    assert_existing_project,
    entry_point_schemas,
    require_input,
    strip_schema,
    UUID_RE,
    assert_autonomous,
    assert_has_fields,
    assert_inputs_referenced,
    assert_project_id,
    assert_schema_sync,
    assert_unique_resource_ids,
    fail,
    is_file_reading_tool,
    load,
    require_resource,
)

SOLUTION_DIR = Path(os.getcwd()) / "VendorInquirySol"
AGENT_DIR = SOLUTION_DIR / "VendorInquiryAgent"
FIXTURE_AGENT_DIR = Path(__file__).resolve().parent / "_fixtures" / "VendorInquirySol" / "VendorInquiryAgent"
PROCESS = "DownloadVendorInvoice"
# Ground truth from the fixture copy, so editing the RPA project can't move the target.
RPA_PROJECT_DIR = Path(__file__).resolve().parent / "_fixtures" / "VendorInquirySol" / PROCESS


def check_rpa_tool() -> None:
    _, tool = require_resource(
        AGENT_DIR,
        lambda d: d.get("$resourceType") == "tool"
        and (d.get("properties") or {}).get("processName") == PROCESS,
        f"tool for the {PROCESS!r} process",
    )
    if tool.get("type") != "process":
        fail(f"{PROCESS} is an RPA process — tool type must be 'process', got {tool.get('type')!r}")
    if tool.get("location") != "solution":
        fail(f"{PROCESS} is a project in this solution — location must be 'solution', got {tool.get('location')!r}")
    folder = (tool.get("properties") or {}).get("folderPath")
    if folder != "solution_folder":
        fail(f"{PROCESS} tool folderPath should be 'solution_folder' (Folder of a local resource), got {folder!r}")
    rkey = tool.get("referenceKey")
    if not isinstance(rkey, str) or not UUID_RE.match(rkey):
        fail(f"{PROCESS} tool referenceKey must be the local resource Key GUID from discovery, got {rkey!r}")

    out_props = ((tool.get("outputSchema") or {}).get("properties") or {})
    file_node = out_props.get("invoiceFile")
    ref = (file_node or {}).get("$ref", "")
    target = ((tool.get("outputSchema") or {}).get("definitions") or {}).get(ref.split("/")[-1]) if ref else file_node
    if not isinstance(target, dict) or target.get("x-uipath-resource-kind") != "JobAttachment":
        fail(
            f"{PROCESS} outputSchema.invoiceFile must be a job-attachment (the process's File output), "
            f"got {file_node!r}"
        )
    print("OK: the RPA tool's File output is typed as a job-attachment")

    want_in, want_out = entry_point_schemas(RPA_PROJECT_DIR)
    for label, mine, truth in (("inputSchema", tool.get("inputSchema"), want_in), ("outputSchema", tool.get("outputSchema"), want_out)):
        if strip_schema(mine) != strip_schema(truth):
            fail(f"{PROCESS} tool {label} does not mirror {PROCESS}/entry-points.json (descriptions ignored): {mine!r}")
    print(f"OK: {PROCESS} tool schemas mirror the solution's {PROCESS} project")


def check_outputs(out_schema: dict) -> None:
    f = assert_has_fields(
        out_schema,
        "outputSchema",
        {
            "invoiceNumber": [],
            "invoiceFound": ["found"],
            "invoiceAmount": ["amount"],
            "dueDate": [],
            "reply": [],
            "needsHumanFollowUp": ["humanFollowUp"],
        },
    )
    for name in ("invoiceFound", "needsHumanFollowUp"):
        if f[name].get("type") != "boolean":
            fail(f"{name} must be a boolean, got {f[name]!r}")


def main() -> None:
    agent = load(AGENT_DIR / "agent.json")
    entry = load(AGENT_DIR / "entry-points.json")
    assert_project_id(agent)
    assert_existing_project(AGENT_DIR, FIXTURE_AGENT_DIR)
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    inputs = [
        require_input(in_schema, "vendor name", "vendorName", "vendor", "supplierName", "name"),
        require_input(in_schema, "inquiry", "inquiry", "inquiryText", "emailText", "email", "emailBody", "query", "message", "body"),
    ]
    assert_inputs_referenced(agent, inputs)
    check_rpa_tool()
    require_resource(AGENT_DIR, is_file_reading_tool, "file-reading built-in tool")
    assert_unique_resource_ids(AGENT_DIR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
