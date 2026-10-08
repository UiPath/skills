#!/usr/bin/env python3
"""Vendor inquiry — document + RPA (file returned by an RPA tool) check.

Final-state only. Validates:
  1. Autonomous agent; schemas in sync; vendorName / inquiry templated.
  2. An external RPA process tool for the deployed "DownloadVendorInvoice"
     (type=process, location=external, processName, folderPath from
     discovery, UUID referenceKey) whose input/output schemas mirror the
     process's own V2 argument schemas (descriptions ignored). In
     particular the `invoiceFile` File output must be a job-attachment
     ($ref to a definition with x-uipath-resource-kind JobAttachment) —
     mapping it to a string is the attachment-passing failure under test.
  3. bindings_v2.json carries the process binding, and the solution declares
     the process under resources/solution_folder/process/.
  4. A file-reading built-in tool is enabled to read the returned PDF.
  5. Output contract: invoiceNumber, invoiceFound (boolean), invoiceAmount,
     dueDate, reply, needsHumanFollowUp (boolean).
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from _shared.use_case_assertions import (  # noqa: E402
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
PROCESS = "DownloadVendorInvoice"
FOLDER_PATH = "Shared/uipath-agents/DownloadVendorInvoiceSol"
INPUTS = ["vendorName", "inquiry"]

JOB_ATTACHMENT = {
    "type": "object",
    "properties": {
        "ID": {"type": "string"},
        "FullName": {"type": "string"},
        "MimeType": {"type": "string"},
        "Metadata": {"type": "object", "additionalProperties": {"type": "string"}},
    },
    "required": ["ID"],
    "x-uipath-resource-kind": "JobAttachment",
}
# InputArgumentsSchemaV2 / OutputArgumentsSchemaV2 of the deployed process,
# as returned by `uip solution resources get` (descriptions stripped).
PROCESS_INPUT = {
    "type": "object",
    "properties": {"invoiceNumber": {"type": "string"}},
    "required": ["invoiceNumber"],
}
PROCESS_OUTPUT = {
    "type": "object",
    "properties": {
        "invoiceFile": {"$ref": "#/definitions/job-attachment"},
        "found": {"type": "boolean"},
    },
    "definitions": {"job-attachment": JOB_ATTACHMENT},
}


def strip(node):
    if isinstance(node, dict):
        return {
            k: strip(v) for k, v in node.items()
            if k not in ("description", "title") and not (k == "required" and v == [])
        }
    if isinstance(node, list):
        return [strip(i) for i in node]
    return node


def check_rpa_tool() -> None:
    _, tool = require_resource(
        AGENT_DIR,
        lambda d: d.get("$resourceType") == "tool"
        and (d.get("properties") or {}).get("processName") == PROCESS,
        f"tool for the {PROCESS!r} process",
    )
    if tool.get("type") != "process":
        fail(f"{PROCESS} is an RPA process — tool type must be 'process', got {tool.get('type')!r}")
    if tool.get("location") != "external":
        fail(f"{PROCESS} is deployed outside this solution — location must be 'external', got {tool.get('location')!r}")
    folder = (tool.get("properties") or {}).get("folderPath")
    if folder != FOLDER_PATH:
        fail(f"{PROCESS} tool folderPath should be {FOLDER_PATH!r} (literal Folder from discovery), got {folder!r}")
    rkey = tool.get("referenceKey")
    if not isinstance(rkey, str) or not UUID_RE.match(rkey):
        fail(f"{PROCESS} tool referenceKey must be the release Key GUID from discovery, got {rkey!r}")

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

    for label, mine, truth in (
        ("inputSchema", tool.get("inputSchema"), PROCESS_INPUT),
        ("outputSchema", tool.get("outputSchema"), PROCESS_OUTPUT),
    ):
        if strip(mine) != truth:
            fail(f"{PROCESS} tool {label} does not mirror the process's V2 argument schema (descriptions ignored): {mine!r}")
    print(f"OK: {PROCESS} tool schemas mirror the deployed process ({FOLDER_PATH})")


def check_binding_and_declaration() -> None:
    bindings = load(AGENT_DIR / "bindings_v2.json")
    hits = [
        r for r in bindings.get("resources") or []
        if isinstance(r, dict) and r.get("resource") == "process" and r.get("key") == PROCESS
    ]
    if not hits:
        fail(f"bindings_v2.json has no process binding keyed {PROCESS!r}")
    folder = ((hits[0].get("value") or {}).get("folderPath") or {}).get("defaultValue")
    if folder != FOLDER_PATH:
        fail(f"process binding folderPath should be {FOLDER_PATH!r}, got {folder!r}")
    decl = list((SOLUTION_DIR / "resources" / "solution_folder" / "process").rglob(f"{PROCESS}.json"))
    if not decl:
        fail(f"solution has no process declaration for {PROCESS} under resources/solution_folder/process/ — solution resources were not refreshed")
    print(f"OK: process binding and solution declaration present ({decl[0].relative_to(SOLUTION_DIR)})")


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
    assert_autonomous(agent)
    in_schema, out_schema = assert_schema_sync(agent, entry)
    assert_has_fields(in_schema, "inputSchema", {f: [] for f in INPUTS})
    assert_inputs_referenced(agent, INPUTS)
    check_rpa_tool()
    check_binding_and_declaration()
    require_resource(AGENT_DIR, is_file_reading_tool, "file-reading built-in tool")
    assert_unique_resource_ids(AGENT_DIR)
    check_outputs(out_schema)


if __name__ == "__main__":
    main()
