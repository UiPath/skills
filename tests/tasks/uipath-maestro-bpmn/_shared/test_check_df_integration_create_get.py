"""expansionLevel coverage in check_df_integration_create_get, V1 and V2 node shapes."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

GRADER = Path(__file__).parent / "check_df_integration_create_get.py"
NS = (
    'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
    'xmlns:uipath="http://uipath.org/schema/bpmn"'
)
ENTITY_PATH = (
    '<uipath:input name="pathParameters" type="json" target="pathParameters">'
    '<![CDATA[{"entityName":"FlowCodeEvalEntity"}]]></uipath:input>'
)


def _v2_node(node_id: str, object_name: str, params: str) -> str:
    """A trimmed V2 element from the CI run 2026-10-21 artifact."""
    return (
        f'<bpmn:sendTask id="{node_id}"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        "<uipath:context>"
        '<uipath:input name="connectorKey" type="string" value="uipath-uipath-dataservice" />'
        f'<uipath:input name="objectName" type="string" value="{object_name}" />'
        '<uipath:input name="activityConfigurationVersion" type="string" value="v2" />'
        "</uipath:context>"
        f"{ENTITY_PATH}{params}"
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def _query(payload: str) -> str:
    return (
        '<uipath:input name="queryParameters" type="json" target="queryParameters">'
        f"<![CDATA[{payload}]]></uipath:input>"
    )


def _v2_get(node_id: str, level: str | None) -> str:
    extra = "" if level is None else f',"expansionLevel":{level}'
    query = _query(f'{{"recordId":"=js:vars.C2_Create_response.Id"{extra}}}')
    return _v2_node(node_id, "GetEntityRecordByIdCurated", query)


def _v1_get(node_id: str, level: str) -> str:
    return _v2_node(
        node_id,
        "GetEntityRecordByIdCurated",
        f'<uipath:input name="expansionLevel" type="integer" target="query" value="{level}" />',
    ).replace(ENTITY_PATH, '<uipath:input name="entityName" target="path" value="FlowCodeEvalEntity"/>')


def _bpmn(gets: list[str]) -> str:
    creates = [_v2_node(f"C{i}_Create", "CreateEntityRecordCurated", _query("{}")) for i in (1, 2)]
    nodes = "".join(creates + gets)
    return f'<bpmn:definitions {NS}><bpmn:process id="p">{nodes}</bpmn:process></bpmn:definitions>'


def _run(tmp_path: Path, gets: list[str]) -> tuple[int, str]:
    (tmp_path / "P.bpmn").write_text(_bpmn(gets), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(GRADER)], cwd=tmp_path, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def test_v2_query_parameters_levels_pass(tmp_path: Path) -> None:
    gets = [_v2_get("C1_Retrieve", None)] + [_v2_get(f"C2_Level_{n}", str(n)) for n in (1, 2, 3)]
    rc, out = _run(tmp_path, gets)
    assert rc == 0, out
    assert "expansionLevel [1, 2, 3]" in out


def test_v1_and_v2_levels_combine(tmp_path: Path) -> None:
    gets = [_v2_get("C1_Retrieve", None), _v1_get("C2_Level_1", "1")]
    gets += [_v2_get("C2_Level_2", "2"), _v2_get("C2_Level_3", "3")]
    rc, out = _run(tmp_path, gets)
    assert rc == 0, out


def test_v2_float_level_reads_as_v1_does(tmp_path: Path) -> None:
    gets = [_v2_get("C1_Retrieve", None), _v2_get("C2_Level_1", "1")]
    gets += [_v2_get("C2_Level_2", "2.0"), _v2_get("C2_Level_3", "3")]
    rc, out = _run(tmp_path, gets)
    assert rc == 0, out


def _v2_list(node_id: str, query: str) -> str:
    """The generic entity-CRUD form: objectName is the entity, the verb is List."""
    return _v2_node(node_id, "FlowCodeEvalEntity", _query(query)).replace(
        "</uipath:context>", '<uipath:input name="operation" type="string" value="List" /></uipath:context>'
    )


@pytest.mark.parametrize(
    ("query", "counted"),
    [
        ('{"where":"=js:\'Id = \' + vars.C1_Create_response.Id"}', True),
        ('{"id":"=js:vars.C1_Create_response.Id"}', True),
        ('{"where":"title = \'X\'"}', False),
        ('{"queryExpression":"Id = \'=js:vars.C1_Create_response.Id\'"}', True),
        ('{"queryExpression":"title = \'X\'"}', False),
        ("{}", False),
    ],
    ids=[
        "v2-where-id",
        "v2-id",
        "v2-where-other",
        "v2-query-expression-id",
        "v2-query-expression-other",
        "v2-no-filter",
    ],
)
def test_v2_list_by_id_counts_as_a_get(query: str, counted: bool) -> None:
    spec = importlib.util.spec_from_file_location("_check_df_integration_create_get", GRADER)
    grader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grader)
    task = ET.fromstring(f"<bpmn:definitions {NS}>{_v2_list('C1_Retrieve', query)}</bpmn:definitions>")[0]
    assert grader.is_retrieval_node(task, "FlowCodeEvalEntity") is counted


@pytest.mark.parametrize(
    "level_3",
    [None, '"three"', "null", "4"],
    ids=["missing", "not-a-number", "null", "wrong-level"],
)
def test_v2_missing_level_fails(tmp_path: Path, level_3: str | None) -> None:
    gets = [_v2_get("C1_Retrieve", None), _v2_get("C2_Level_1", "1")]
    gets += [_v2_get("C2_Level_2", "2"), _v2_get("C2_Level_3", level_3)]
    rc, out = _run(tmp_path, gets)
    assert rc != 0
    assert "missing expansionLevel(s) [3]" in out


def test_level_in_v2_path_parameters_does_not_count(tmp_path: Path) -> None:
    misplaced = _v2_get("C2_Level_3", None).replace(
        '{"entityName":"FlowCodeEvalEntity"}', '{"entityName":"FlowCodeEvalEntity","expansionLevel":3}'
    )
    gets = [_v2_get("C1_Retrieve", None), _v2_get("C2_Level_1", "1"), _v2_get("C2_Level_2", "2")]
    gets.append(misplaced)
    rc, out = _run(tmp_path, gets)
    assert rc != 0
    assert "missing expansionLevel(s) [3]" in out
