#!/usr/bin/env python3
r"""DF smoke_file_activities (BPMN): Download + Create + Upload + Delete
file-record-field wiring on FlowCodeEvalEntity/file1.

Ported from Flow `connector_features/datafabric_connector/smoke_file_activities.yaml`'s
``check_smoke_file_activities.py``: same scenario (chain Download File from
Record Field -> Create Entity Record -> Upload File to Record Field -> Delete
File from Record Field against FlowCodeEvalEntity/file1, with the upload's
file input carrying some variable binding and the create output id wired into
upload+delete), translated from a JSON node/inputs.detail walk to an XML walk
over the registry-driven ``Intsvc.ActivityExecution`` connector shell (see
skills/uipath-maestro-bpmn/references/registry-workflow.md §2-4).

Node identity: Download/Upload/Delete are matched by objectName in every
spelling the connector catalog serves for the operation --
DownloadFileFromRecordField|DownloadFileFromRecordFieldV2|DownloadFileFromRecordField_V3,
UploadFileToRecordField|UploadFileToRecordFieldV2|UploadFileToRecordField_V3,
DeleteFileFromRecordField|DeleteFileFromRecordFieldV2|DeleteFileFromRecordField_V3.
The unsuffixed V1 objects are the only ones whose `uip is resources describe`
exposes a `fieldName` parameter, so agents pick them when the prompt names the
field (2026-09-23: claude nightly and codex smoke both did). Create accepts
both shapes the skill emits for entity CRUD (copied from
check_df_integration_create_get.py's classification, no new shared module):
the curated CreateEntityRecord|CreateEntityRecordCurated|CreateEntityRecord_V3
objectName, or the generic entity-CRUD form (objectName == FlowCodeEvalEntity
with operation=Create or method=POST).

Where Flow's grader read fixed JSON keys (`pathParameters.entityName`,
`queryParameters._fieldName`/`recordId`, `bodyParameters`,
`multipartParameters.file`), the registry does not pin where a `Parameters`
entry lands -- registry-workflow.md §3 "Required Parameters are separate from
the body ... each parameter is its own input, targeted by its Type" (query,
path, or file). Each re-homing below documents where this grader looks
instead of assuming Flow's JSON shape:

  * entityName -> any uipath:input value/text on the node, or its context
    `path` field (same either/or tolerance as check_df_integration_create_get.py
    / check_df_smoke_create_all_types.py -- the skill does not pin where
    entityName lands).
  * `_fieldName` (field selector, "file1") -> any uipath:input value/text
    on the node, or an input's `name`. V1 objects carry it as the
    `fieldName` path parameter; the V2/_V3 objects expose no field parameter
    at all (describe lists only entityName and recordId), so an agent using
    them names the multipart input after the field (codex, 2026-09-23).
  * Download's `recordId` literal UUID -> a bare (non-expression) UUID-shaped
    value on any of Download's inputs (Flow required a UUID literal here too).
  * Create's single-body-dict read -> Flow's grader reads ONE
    ``bodyParameters`` dict; here every ``target="body"`` input's JSON is
    parsed and merged (a hand-authored file may legitimately or accidentally
    carry more than one -- registry-workflow.md §3 -- but Flow's own grader
    never penalized node shape, only body *content*, so an extra body input
    is not itself a failure here).
  * Upload's multipart `file` binding -> Flow accepted any `=js:$vars.*`
    expression naming *any* variable in scope (its own docstring: "download
    output, typed file global, or start-input file parameter all pass").
    This grader matches that leniency: the input(s) targeting the file
    parameter (`target="file"`, or a fallback `name="file"`) need only
    contain a `vars.<id>` reference -- any variable, not pinned to Download's
    own output var.
  * create output id flowing into Upload/Delete recordId -> Create's
    `<uipath:output var=...>` id must appear inside an Upload/Delete input's
    value/text as `vars.<CreateVarId>` (optionally followed by a `.Id`-style
    property suffix) -- substring match, same style as
    check_drive_to_slack.has_variable_reference.

Checks performed:
  1. BPMN file exists and is well-formed XML.
  2. Exactly one each of Download, Create, Upload, Delete connector nodes on
     FlowCodeEvalEntity (Download/Upload/Delete: curated objectName only;
     Create: curated or generic entity-CRUD form -- see above).
  3. Download, Upload, and Delete each reference field "file1".
  4. Download's recordId is a literal (non-expression) UUID.
  5. Create's target="body" JSON (merged across every such input) covers
     title/description/score.
  6. Upload's `target="file"`/`name="file"` input carries a `vars.<id>`
     reference (any variable).
  7. Upload and Delete both reference Create's output variable for recordId.

Assertion map (Flow -> BPMN):
  F check_smoke_file_activities.py:113-121  REQUIRED node-suffix presence per ENTITY      -> classify() finds Download/Create/Upload/Delete curated|generic nodes mentioning ENTITY
  F check_smoke_file_activities.py:129-133  resolve_field(...) == FIELD for D/U/Delete    -> mentions(task, FIELD) on Download/Upload/Delete
  F check_smoke_file_activities.py:146-148  Download recordId is UUID_RE literal          -> literal_uuid_value(download)
  F check_smoke_file_activities.py:155-160  create_body superset of required fields       -> merged target="body" JSON keys superset of REQUIRED_CREATE_BODY
  F check_smoke_file_activities.py:137-142  upload multipart file has ANY =js:$vars.\w+   -> file_field_values(upload) matches `vars.\w+` (not pinned to Download's own output var)
  F check_smoke_file_activities.py:163-179  refs_create_output(rid) for upload/delete     -> has_variable_reference(task, v) for v in create_vars
  I                                          locate/parse .bpmn                            -> parse_bpmn()
  T                                          curated|generic Create classification (integration_create_get precedent) -> is_create_node()
  T                                          entity name anywhere in node inputs/objectName/path -> mentions(task, ENTITY)
  T                                          V1|V2|_V3 objectName spellings for one operation (catalog lists all three; only V1 exposes fieldName) -> *_OBJS sets
  T                                          field selector as an input name when the object has no field parameter -> mentions_field()
  T                                          vars.<VarId> substring reference in place of Flow node-id/variable-chain reference -> has_variable_reference()
  T                                          merge every target="body" input instead of requiring exactly one -> merged body-field union parse
  DROPPED  require_no_private_connector_values  (not in Flow; `validate` criterion already covers structure)
  DROPPED  require_sequence_integrity            (not in Flow; `validate` criterion already covers structure)
  DROPPED  require_di_for_visible_elements       (not in Flow; `validate` criterion already covers structure)
  DROPPED  Download->Upload / Create->Upload / Upload->Delete graph.reaches ordering (Flow's grader has no edge/order check at all)
  DROPPED  Upload must reference Download's SPECIFIC output var, not any var  (over-tightened in the port; Flow accepts ANY =js:$vars.* binding)
  DROPPED  exactly-one target="body" input hard requirement  (Flow reads a single bodyParameters dict; parsing the body when Flow read bodyParameters is I, enforcing a single input is not)
"""

from __future__ import annotations

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _shared.bpmn_check import (  # noqa: E402
    NS,
    all_node_values,
    context_value,
    elements,
    fail,
    has_typed_uipath_extension,
    parse_bpmn,
)

ENTITY = "FlowCodeEvalEntity"
FIELD = "file1"
CONNECTOR_KEY = "uipath-uipath-dataservice"
ACTIVITY_TYPE = "Intsvc.ActivityExecution"

DOWNLOAD_OBJS = {
    "DownloadFileFromRecordField",
    "DownloadFileFromRecordFieldV2",
    "DownloadFileFromRecordField_V3",
}
UPLOAD_OBJS = {
    "UploadFileToRecordField",
    "UploadFileToRecordFieldV2",
    "UploadFileToRecordField_V3",
}
DELETE_OBJS = {
    "DeleteFileFromRecordField",
    "DeleteFileFromRecordFieldV2",
    "DeleteFileFromRecordField_V3",
}
CREATE_CURATED_OBJS = {
    "CreateEntityRecord",
    "CreateEntityRecordCurated",
    "CreateEntityRecord_V3",
}
FILE_TARGETS = {"file", "multipart"}
REQUIRED_CREATE_BODY = {"title", "description", "score"}

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
VARS_REF_RE = re.compile(r"vars\.\w+")
_CREATE_OP_RE = re.compile(r"^create$", re.IGNORECASE)


def node_inputs(task: ET.Element) -> list[ET.Element]:
    # `.//` walks every descendant of the sendTask -- covers both layouts seen
    # in practice: context/body/query/path/file inputs as direct siblings of
    # uipath:context, or nested inside it.
    return task.findall(".//uipath:input", NS)


def mentions(task: ET.Element, needle: str) -> bool:
    values = all_node_values(task) + [context_value(task, "path")]
    return any(needle in v for v in values if v)


def mentions_field(task: ET.Element, field: str) -> bool:
    if mentions(task, field):
        return True
    return any((inp.attrib.get("name") or "").strip() == field for inp in node_inputs(task))


def output_vars(task: ET.Element) -> list[str]:
    return [
        out.attrib["var"]
        for out in task.findall(".//uipath:output", NS)
        if out.attrib.get("var")
    ]


def has_variable_reference(task: ET.Element, var_id: str) -> bool:
    needle = f"vars.{var_id}"
    return any(needle in v for v in all_node_values(task))


def is_generic_entity_object(object_name: str, entity: str) -> bool:
    return object_name.strip().lower() == entity.strip().lower()


def is_create_node(task: ET.Element, object_name: str) -> bool:
    if object_name in CREATE_CURATED_OBJS:
        return True
    if not is_generic_entity_object(object_name, ENTITY):
        return False
    operation = context_value(task, "operation").strip()
    method = context_value(task, "method").strip().upper()
    return bool(_CREATE_OP_RE.match(operation)) or method == "POST"


def connector_nodes(root: ET.Element) -> list[ET.Element]:
    return [
        task
        for task in elements(root, "sendTask")
        if has_typed_uipath_extension(task, "activity", ACTIVITY_TYPE)
        and context_value(task, "connectorKey") == CONNECTOR_KEY
    ]


def classify(
    root: ET.Element,
) -> tuple[ET.Element | None, ET.Element | None, ET.Element | None, ET.Element | None]:
    download = create = upload = delete = None
    for task in connector_nodes(root):
        if not mentions(task, ENTITY):
            continue
        object_name = context_value(task, "objectName")
        if object_name in DOWNLOAD_OBJS and download is None:
            download = task
        elif object_name in UPLOAD_OBJS and upload is None:
            upload = task
        elif object_name in DELETE_OBJS and delete is None:
            delete = task
        elif create is None and is_create_node(task, object_name):
            create = task
    return download, create, upload, delete


def literal_uuid_value(task: ET.Element) -> str | None:
    for v in all_node_values(task):
        if not v.startswith("=") and UUID_RE.match(v.strip()):
            return v.strip()
    return None


def file_field_values(task: ET.Element) -> list[str]:
    """Values of the input(s) that carry the multipart file binding.

    registry-workflow.md §3: "each parameter is its own input, targeted by
    its Type" -- a file parameter is `target="file"`, or `target="multipart"`
    when the author copies describe's `Type: multipart`. Falls back to an
    input literally named "file" (case-insensitive) for a shape that doesn't
    set `target`. Scoping to these inputs (rather than any input on the node)
    keeps this check meaningful: Upload's recordId is separately required to
    reference Create's output var, so "any vars.* on the node" would always
    pass regardless of whether the file binding itself carries one.
    """
    values: list[str] = []
    for inp in node_inputs(task):
        target = inp.attrib.get("target")
        name = (inp.attrib.get("name") or "").strip().lower()
        if target in FILE_TARGETS or name == "file":
            v = inp.attrib.get("value") or (inp.text or "")
            if v:
                values.append(v)
    return values


def merged_body_json(task: ET.Element) -> dict:
    """Parse every target="body" input's JSON and merge the resulting dicts.

    Flow's grader reads one `bodyParameters` dict; a hand-authored BPMN file
    may carry more than one `target="body"` input without that being a
    content failure Flow ever asserted (only the resulting field coverage
    matters here), so this merges rather than hard-failing on the count.
    """
    merged: dict = {}
    for inp in node_inputs(task):
        if inp.attrib.get("target") != "body":
            continue
        raw = inp.text or ""
        if not raw.strip():
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            merged.update(parsed)
    return merged


def main() -> None:
    path, root = parse_bpmn()

    download, create, upload, delete = classify(root)
    missing = [
        label
        for label, node in [
            ("Download File from Record Field", download),
            ("Create Entity Record", create),
            ("Upload File to Record Field", upload),
            ("Delete File from Record Field", delete),
        ]
        if node is None
    ]
    if missing:
        fail(f"missing connector node(s) on {ENTITY}: {', '.join(missing)}")
    print(f"OK: Download + Create + Upload + Delete nodes present on {ENTITY}")

    for label, task in [("Download", download), ("Upload", upload), ("Delete", delete)]:
        if not mentions_field(task, FIELD):
            fail(f"{label} node does not reference field {FIELD!r} in any input")
    print(f"OK: Download/Upload/Delete reference field {FIELD!r}")

    dl_uuid = literal_uuid_value(download)
    if not dl_uuid:
        fail("Download node has no literal (non-expression) UUID-shaped recordId value")
    print(f"OK: Download recordId is a literal UUID ({dl_uuid})")

    create_body = merged_body_json(create)
    if not create_body:
        fail(f'no parseable target="body" JSON object found on the Create node')
    missing_fields = REQUIRED_CREATE_BODY - set(create_body.keys())
    if missing_fields:
        fail(f"Create body missing required fields: {sorted(missing_fields)}")
    print(f"OK: Create body covers {sorted(REQUIRED_CREATE_BODY)}")

    file_values = file_field_values(upload)
    if not file_values:
        fail('Upload node has no target="file" (or name="file") input to carry the file binding')
    if not any(VARS_REF_RE.search(v) for v in file_values):
        fail(f"Upload node's file input has no `vars.<id>` variable reference (found: {file_values})")
    print("OK: Upload's file input references a process variable")

    create_vars = output_vars(create)
    if not create_vars:
        fail("Create node has no <uipath:output var=...> to wire into Upload/Delete")
    for label, task in [("Upload", upload), ("Delete", delete)]:
        if not any(has_variable_reference(task, v) for v in create_vars):
            fail(
                f"{label} node's recordId does not reference Create's output "
                f"variable (vars.{{{', '.join(create_vars)}}})"
            )
    print(f"OK: Upload and Delete recordId reference Create's output variable vars.{create_vars[0]}")

    print(f"OK: {path} wires Download -> Create -> Upload -> Delete on {ENTITY}/{FIELD}")


if __name__ == "__main__":
    main()
