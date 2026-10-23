"""check_testmanager_attachments.py: V1 and connector-mode HTTP shapes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_testmanager_attachments.py")
TM_KEY = "uipath-uipath-testmanager"

NODE = """
    <bpmn:sendTask id="Task_{object_name}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.ActivityExecution" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-testmanager" />
            <uipath:input name="objectName" type="string" value="{object_name}" />
            <uipath:input name="method" type="string" value="{method}" />
          </uipath:context>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>"""

HTTP_NODE = """
    <bpmn:sendTask id="Task_{index}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.UnifiedHttpRequest" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-http" />
            <uipath:input name="method" type="string" value="POST" />
            <uipath:input name="path" type="string" value="/http-request" />
            <uipath:input name="objectName" type="string" value="http-request" />
          </uipath:context>
          <uipath:input name="body" type="json" target="body"><![CDATA[{body}]]></uipath:input>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>"""

LEGACY_SDK_HTTP_NODE = """
    <bpmn:sendTask id="Task_{index}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Intsvc.ActivityExecution" version="v1" />
          <uipath:context>
            <uipath:input name="connectorKey" type="string" value="uipath-uipath-testmanager" />
            <uipath:input name="objectName" type="string" value="http-request" />
            <uipath:input name="method" type="string" value="POST" />
            <uipath:input name="path" type="string" value="/http-request" />
          </uipath:context>
          <uipath:input name="body" type="json" target="body"><![CDATA[{body}]]></uipath:input>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:sendTask>"""

LABELS = [
    "upload an attachment",
    "get attachments",
    "download an attachment",
    "delete an attachment",
]

P = "'/v2/' + vars.Var_ProjectId + '/attachments/' + vars.Var_ObjectType + '/' + "
HTTP_OPERATIONS = [
    ("POST", f"=js:{P}vars.Var_ObjectId + '/upload'"),
    ("GET", f"=js:{P}vars.Var_ObjectId + '/all'"),
    ("GET", f"=js:{P}vars.Var_AttachmentId + '/download'"),
    ("DELETE", f"=js:{P}vars.Var_AttachmentId"),
]


def _write(tmp_path: Path, body: str, *args: str) -> subprocess.CompletedProcess:
    (tmp_path / "Process.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        f'<bpmn:process id="Process_1">{body}</bpmn:process></bpmn:definitions>'
    )
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def _run(tmp_path: Path, download_method: str) -> subprocess.CompletedProcess:
    nodes = [
        ("UploadAttachment", "POST"),
        ("GetAttachments", "GET"),
        ("DownloadAttachment", download_method),
        ("DeleteAttachment", "DELETE"),
    ]
    body = "".join(NODE.format(object_name=o, method=m) for o, m in nodes)
    return _write(tmp_path, body, "--all-ops")


def _http_body(method: str, path: str, **overrides: str) -> str:
    body = {
        "authentication": "connector",
        "method": method,
        "targetConnector": TM_KEY,
        "path": path,
        "url": path,
    }
    body.update(overrides)
    return json.dumps(body)


def _http_nodes(template: str = HTTP_NODE, **overrides: str) -> list[str]:
    return [
        template.format(index=i, body=_http_body(m, p, **overrides))
        for i, (m, p) in enumerate(HTTP_OPERATIONS)
    ]


def _missing(stderr: str) -> list[str]:
    return [label for label in LABELS if f"\n  {label} (" in stderr]


@pytest.mark.parametrize("method", ["GETBYID", "GET", "get"])
def test_download_accepts_get_spellings(tmp_path: Path, method: str) -> None:
    result = _run(tmp_path, method)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("method", ["DELETE", "POST"])
def test_download_rejects_other_methods(tmp_path: Path, method: str) -> None:
    result = _run(tmp_path, method)
    assert result.returncode != 0
    assert "download an attachment" in result.stderr


def test_connector_mode_http_passes_all_ops(tmp_path: Path) -> None:
    result = _write(tmp_path, "".join(_http_nodes()), "--all-ops")
    assert result.returncode == 0, result.stderr
    assert "all four" in result.stdout


def test_mixed_activity_and_http_passes_all_ops(tmp_path: Path) -> None:
    activity = [
        NODE.format(object_name="UploadAttachment", method="POST"),
        NODE.format(object_name="GetAttachments", method="GET"),
    ]
    result = _write(tmp_path, "".join(activity + _http_nodes()[2:]), "--all-ops")
    assert result.returncode == 0, result.stderr
    assert "all four" in result.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"targetConnector": "uipath-salesforce-slack"},
        {"authentication": "manual"},
    ],
)
def test_http_not_through_test_manager_fails(tmp_path: Path, overrides: dict) -> None:
    result = _write(tmp_path, "".join(_http_nodes(**overrides)))
    assert result.returncode != 0
    assert "no bpmn:sendTask calls the Test Manager connector" in result.stderr


def test_http_with_unfilled_project_id_fails(tmp_path: Path) -> None:
    nodes = _http_nodes()
    path = "=js:'/v2/{projectId}/attachments/' + vars.Var_ObjectType + '/' + vars.Var_ObjectId + '/upload'"
    nodes[0] = HTTP_NODE.format(index=0, body=_http_body("POST", path))
    result = _write(tmp_path, "".join(nodes), "--all-ops")
    assert result.returncode != 0
    assert _missing(result.stderr) == ["upload an attachment"]
    assert "'/v2/{projectId}/attachments/{objType}/{id}/upload' with every placeholder" in result.stderr


@pytest.mark.parametrize("index", range(len(HTTP_OPERATIONS)))
def test_missing_one_operation_fails_all_ops(tmp_path: Path, index: int) -> None:
    nodes = _http_nodes()
    del nodes[index]
    result = _write(tmp_path, "".join(nodes), "--all-ops")
    assert result.returncode != 0
    assert _missing(result.stderr) == [LABELS[index]]


@pytest.mark.parametrize("index, method", [(2, "GETBYID"), (3, "GET"), (1, "POST")])
def test_http_wrong_method_fails_all_ops(tmp_path: Path, index: int, method: str) -> None:
    nodes = _http_nodes()
    nodes[index] = HTTP_NODE.format(index=index, body=_http_body(method, HTTP_OPERATIONS[index][1]))
    result = _write(tmp_path, "".join(nodes), "--all-ops")
    assert result.returncode != 0
    assert _missing(result.stderr) == [LABELS[index]]


@pytest.mark.parametrize("args", [(), ("--all-ops",)])
def test_legacy_sdk_connector_http_fails(tmp_path: Path, args: tuple) -> None:
    result = _write(tmp_path, "".join(_http_nodes(LEGACY_SDK_HTTP_NODE)), *args)
    assert result.returncode != 0
    assert "no bpmn:sendTask calls the Test Manager connector" in result.stderr
