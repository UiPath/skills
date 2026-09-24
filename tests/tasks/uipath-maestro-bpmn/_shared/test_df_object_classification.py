"""Object-name classification boundaries for the Data Service graders.

Every Data Service operation is served under three spellings by
``uip is activities list`` -- plain, curated/``V2``, and ``_V3`` -- and the
graders accept all three (see #3494). The accept-sets are exact-match or
anchored-regex today, so a neighbouring object whose name merely *contains*
an accepted one is rejected. These tests pin that boundary, so a future
refactor to substring matching cannot silently widen the graders:
``QueryMultipleEntityRecords`` must never classify as ``QueryEntityRecords``.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_SHARED = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(_SHARED.parent))
sys.path.insert(0, str(_SHARED))

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"
UIPATH_NS = "http://uipath.org/schema/bpmn"
CONNECTOR = "uipath-uipath-dataservice"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _SHARED / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _node(object_name: str, entity: str, operation: str = "", method: str = "") -> ET.Element:
    return ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}" id="Task_1">'
        "<bpmn:extensionElements><uipath:activity version=\"v1\">"
        '<uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        "<uipath:context>"
        f'<uipath:input name="connectorKey" type="string" value="{CONNECTOR}" />'
        f'<uipath:input name="objectName" type="string" value="{object_name}" />'
        f'<uipath:input name="operation" type="string" value="{operation}" />'
        f'<uipath:input name="method" type="string" value="{method}" />'
        "</uipath:context>"
        f'<uipath:input name="entityName" target="path" type="string" value="{entity}" />'
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


# (grader, accept-set attribute, kind, entity, three accepted spellings, rejected neighbours)
_IS_KIND_CASES = [
    (
        "check_df_contractregistry_crud_filters",
        "QUERY_OBJECTS",
        "query",
        "ContractRegistry",
        ["QueryEntityRecords", "QueryEntityRecordsCurated", "QueryEntityRecords_V3"],
        ["QueryMultipleEntityRecords", "QueryMultipleEntityRecords_V3", "QueryEntityRecordsX"],
    ),
    (
        "check_df_contractregistry_crud_filters",
        "CREATE_OBJECTS",
        "create",
        "ContractRegistry",
        ["CreateEntityRecord", "CreateEntityRecordCurated", "CreateEntityRecord_V3"],
        ["CreateMultipleEntityRecords", "GetEntityRecord", "CreateEntityRecordsBulk"],
    ),
    (
        "check_df_e2e_contract_intake_pipeline",
        "DELETE_OBJECTS",
        "delete",
        "ContractRegistry",
        ["DeleteEntityRecord", "DeleteEntityRecordCurated", "DeleteEntityRecord_V3"],
        ["DeleteMultipleEntityRecords", "DeleteFileFromRecordField"],
    ),
]


@pytest.mark.parametrize("module_name,attr,kind,entity,accepted,rejected", _IS_KIND_CASES)
def test_is_kind_accepts_every_spelling_and_rejects_neighbours(
    module_name: str, attr: str, kind: str, entity: str, accepted: list[str], rejected: list[str]
) -> None:
    module = _load(module_name)
    objects = getattr(module, attr)
    for name in accepted:
        assert module.is_kind(_node(name, entity), objects, kind), f"{name} should classify as {kind}"
    for name in rejected:
        assert not module.is_kind(_node(name, entity), objects, kind), f"{name} must not classify as {kind}"


def test_query_filter_object_names_reject_the_multiple_variant() -> None:
    """The query graders match a lowercased exact set, not a substring."""
    for module_name in ("check_df_smoke_query_filter", "check_df_smoke_update_existing"):
        names = _load(module_name).OBJECT_NAMES
        assert "queryentityrecords" in names
        assert "queryentityrecordscurated" in names
        assert "queryentityrecords_v3" in names
        assert "querymultipleentityrecords" not in names
        assert not any(n != "queryentityrecords" and "queryentityrecords" in n and n.startswith("querymultiple") for n in names)


def test_create_all_types_object_regex_is_anchored() -> None:
    regex = _load("check_df_smoke_create_all_types").OBJECT_NAME_RE
    for name in ("CreateEntityRecord", "CreateEntityRecordCurated", "CreateEntityRecord_V3"):
        assert regex.match(name), f"{name} should match"
    for name in ("XCreateEntityRecord", "CreateEntityRecordX", "CreateMultipleEntityRecords"):
        assert not regex.match(name), f"{name} must not match"


def test_file_activity_object_sets_cover_three_spellings_only() -> None:
    module = _load("check_df_smoke_file_activities")
    for attr, stem in [
        ("DOWNLOAD_OBJS", "DownloadFileFromRecordField"),
        ("UPLOAD_OBJS", "UploadFileToRecordField"),
        ("DELETE_OBJS", "DeleteFileFromRecordField"),
    ]:
        objs = getattr(module, attr)
        assert objs == {stem, f"{stem}V2", f"{stem}_V3"}, attr


def test_file_activity_field_fallback_requires_the_file_input() -> None:
    """An input merely named after the field does not select it (#3494 review)."""
    module = _load("check_df_smoke_file_activities")
    decoy = ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}" id="Task_Delete">'
        '<bpmn:extensionElements><uipath:activity version="v1">'
        '<uipath:input name="file1" target="query" type="string" value="unrelated" />'
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )
    assert not module.mentions_field(decoy, "file1")

    real = ET.fromstring(
        f'<bpmn:sendTask xmlns:bpmn="{BPMN_NS}" xmlns:uipath="{UIPATH_NS}" id="Task_Upload">'
        '<bpmn:extensionElements><uipath:activity version="v1">'
        '<uipath:input name="file1" target="file" type="file" value="=vars.Var_Downloaded" />'
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )
    assert module.mentions_field(real, "file1")
