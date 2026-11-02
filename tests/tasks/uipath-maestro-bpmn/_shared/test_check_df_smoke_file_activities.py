"""Upload file binding in check_df_smoke_file_activities, V1 and V2 node shapes."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

GRADER = Path(__file__).parent / "check_df_smoke_file_activities.py"
NS = (
    'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
    'xmlns:uipath="http://uipath.org/schema/bpmn"'
)
RECORD_ID = "11111111-1111-1111-1111-111111111111"
FIELD_BODY = '<uipath:input name="body" type="json" target="body"><![CDATA[{"fieldName":"file1"}]]></uipath:input>'
V2_FILE_PART = '{"name":"file","dataType":"file","value":"=js:vars.Var_DownloadedFile"}'
V2_OTHER_PART = '{"name":"attachment","dataType":"file","value":"=js:vars.Var_DownloadedFile"}'


def _node(node_id: str, object_name: str, record_id: str, inputs: str, outputs: str = "") -> str:
    """A V2 element trimmed from the smoke run artifact on skills#4147."""
    return (
        f'<bpmn:sendTask id="{node_id}"><bpmn:extensionElements>'
        '<uipath:activity version="v1"><uipath:type value="Intsvc.ActivityExecution" version="v1" />'
        "<uipath:context>"
        '<uipath:input name="connectorKey" type="string" value="uipath-uipath-dataservice" />'
        '<uipath:input name="resourceKey" type="string" value="0f6156da-7a1c-4cd8-910e-d7fd338baef7" />'
        f'<uipath:input name="objectName" type="string" value="{object_name}" />'
        '<uipath:input name="activityConfigurationVersion" type="string" value="v2" />'
        "</uipath:context>"
        '<uipath:input name="pathParameters" type="json" target="pathParameters">'
        '<![CDATA[{"entityName":"FlowCodeEvalEntity"}]]></uipath:input>'
        '<uipath:input name="queryParameters" type="json" target="queryParameters">'
        f'<![CDATA[{{"recordId":"{record_id}"}}]]></uipath:input>'
        f"{inputs}{outputs}"
        "</uipath:activity></bpmn:extensionElements></bpmn:sendTask>"
    )


def _metadata(parts: str) -> str:
    return (
        '<uipath:input name="metadata" type="json" target="metadata"><![CDATA['
        '{"inputMetadata":{"type":"multipart","multipart":{"bodyFieldName":"body"}}'
        f"{parts}}}]]></uipath:input>"
    )


def _bpmn(upload_inputs: str) -> str:
    created = "=js:vars.Var_CreatedRecord.Id"
    nodes = [
        _node("Task_Download", "DownloadFileFromRecordFieldV2", RECORD_ID, FIELD_BODY),
        _node(
            "Task_Create",
            "CreateEntityRecordCurated",
            "",
            '<uipath:input name="body" type="json" target="body"><![CDATA['
            '{"title":"T","description":"D","score":42.5}]]></uipath:input>',
            '<uipath:output name="response" type="jsonSchema" source="=response" var="Var_CreatedRecord" />',
        ),
        _node("Task_Upload", "UploadFileToRecordFieldV2", created, FIELD_BODY + upload_inputs),
        _node("Task_Delete", "DeleteFileFromRecordFieldV2", created, FIELD_BODY),
    ]
    body = "".join(nodes)
    return f'<bpmn:definitions {NS}><bpmn:process id="p">{body}</bpmn:process></bpmn:definitions>'


def _run(tmp_path: Path, upload_inputs: str) -> tuple[int, str]:
    (tmp_path / "P.bpmn").write_text(_bpmn(upload_inputs), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(GRADER)], cwd=tmp_path, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


@pytest.mark.parametrize(
    "upload_inputs",
    [
        _metadata(f',"multipartParameters":[{V2_FILE_PART}]'),
        '<uipath:input name="file" type="file" target="file" value="=js:vars.Var_DownloadedFile" />',
    ],
    ids=["v2-multipart", "v1-file-input"],
)
def test_file_binding_passes(tmp_path: Path, upload_inputs: str) -> None:
    rc, out = _run(tmp_path, upload_inputs)
    assert rc == 0, out


@pytest.mark.parametrize(
    ("upload_inputs", "message"),
    [
        (_metadata(""), "no file input"),
        (_metadata(f',"multipartParameters":[{V2_OTHER_PART}]'), "no file input"),
        (_metadata(',"multipartParameters":[{"name":"file","dataType":"file","value":"report.pdf"}]'), "no `vars.<id>`"),
        (_metadata(',"multipartParameters":"not a list"'), "no file input"),
    ],
    ids=["no-multipart-parameters", "other-part-name", "no-vars-reference", "not-a-list"],
)
def test_file_binding_fails(tmp_path: Path, upload_inputs: str, message: str) -> None:
    rc, out = _run(tmp_path, upload_inputs)
    assert rc != 0
    assert message in out
