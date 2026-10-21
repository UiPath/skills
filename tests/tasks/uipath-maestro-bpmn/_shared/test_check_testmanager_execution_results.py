"""check_testmanager_execution_results.py: V1 and connector-mode HTTP shapes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_testmanager_execution_results.py")
TM_KEY = "uipath-uipath-testmanager"

V1_NODE = """
    <bpmn:sendTask id="Task_{index}">
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

V1_OPERATIONS = [
    ("TestExecution", "GETBYID"),
    ("TestExecution", "DELETE"),
    ("GetTestCaseLogsOfTestExecution", "GET"),
    ("TestCaseLog", "GETBYID"),
    ("GetRobotLogs", "GET"),
    ("GetAssertions", "GET"),
    ("DownloadAssertion", "GETBYID"),
    ("GetTestSteps", "GET"),
    ("GetTestStepLogs", "GET"),
]

LABELS = [
    "get a test execution",
    "delete a test execution",
    "get the test case logs of a test execution",
    "get a test case log",
    "get robot logs",
    "get assertions",
    "download an assertion",
    "get test steps",
    "get test step logs",
]


P = "'/v2/' + vars.Var_ProjectId + "
HTTP_OPERATIONS = [
    ("GET", f"=js:{P}'/testexecutions/' + vars.Var_TestExecutionId"),
    ("DELETE", f"=js:{P}'/testexecutions/' + vars.Var_TestExecutionId"),
    ("GET", f"=js:{P}'/testcaselogs/testexecution/' + vars.Var_TestExecutionId + '/paged'"),
    ("GET", f"=js:{P}'/testcaselogs/' + vars.Var_TestCaseLogId"),
    ("GET", f"=js:{P}'/orchestrator/testexecution/' + vars.Var_TestExecutionId + '/robotlogs/paged'"),
    ("GET", f"=js:{P}'/testcaselogartifacts/' + vars.Var_TestCaseLogId + '/assertions'"),
    (
        "GET",
        f"=js:{P}'/testcaselogartifacts/' + vars.Var_TestCaseLogId + '/assertions/' "
        "+ vars.Var_AssertionId + '/downloadscreenshot'",
    ),
    ("GET", f"=js:{P}'/teststeps/testcase/' + vars.Var_TestCaseId"),
    ("GET", f"=js:{P}'/teststeplogs'"),
]


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


def _run(tmp_path: Path, nodes: list[str], *args: str) -> subprocess.CompletedProcess:
    (tmp_path / "Process.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        f'<bpmn:process id="Process_1">{"".join(nodes)}</bpmn:process></bpmn:definitions>'
    )
    return subprocess.run(
        [sys.executable, str(CHECKER), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


def _missing(stderr: str) -> list[str]:
    return [label for label in LABELS if f"\n  {label} (" in stderr]


def _v1_nodes() -> list[str]:
    return [
        V1_NODE.format(index=i, object_name=o, method=m)
        for i, (o, m) in enumerate(V1_OPERATIONS)
    ]


def _http_nodes(**overrides: str) -> list[str]:
    return [
        HTTP_NODE.format(index=i, body=_http_body(m, p, **overrides))
        for i, (m, p) in enumerate(HTTP_OPERATIONS)
    ]


def test_v1_activity_execution_passes_all_ops(tmp_path: Path) -> None:
    result = _run(tmp_path, _v1_nodes(), "--all-ops")
    assert result.returncode == 0, result.stderr


def test_connector_mode_http_passes_all_ops(tmp_path: Path) -> None:
    result = _run(tmp_path, _http_nodes(), "--all-ops")
    assert result.returncode == 0, result.stderr
    assert "all nine" in result.stdout


@pytest.mark.parametrize(
    "overrides",
    [
        {"targetConnector": "uipath-salesforce-slack"},
        {"authentication": "manual"},
    ],
)
def test_http_not_through_test_manager_fails(tmp_path: Path, overrides: dict) -> None:
    result = _run(tmp_path, _http_nodes(**overrides))
    assert result.returncode != 0
    assert "no bpmn:sendTask calls the Test Manager connector" in result.stderr


@pytest.mark.parametrize("index", range(len(HTTP_OPERATIONS)))
def test_missing_one_operation_fails_all_ops(tmp_path: Path, index: int) -> None:
    nodes = _http_nodes()
    del nodes[index]
    result = _run(tmp_path, nodes, "--all-ops")
    assert result.returncode != 0
    assert _missing(result.stderr) == [LABELS[index]]


@pytest.mark.parametrize(
    "index, method, label",
    [
        (1, "GET", "delete a test execution"),
        (5, "POST", "get assertions"),
        (0, "GETBYID", "get a test execution"),
    ],
)
def test_wrong_method_fails_all_ops(tmp_path: Path, index: int, method: str, label: str) -> None:
    nodes = _http_nodes()
    nodes[index] = HTTP_NODE.format(index=index, body=_http_body(method, HTTP_OPERATIONS[index][1]))
    result = _run(tmp_path, nodes, "--all-ops")
    assert result.returncode != 0
    assert _missing(result.stderr) == [label]


def test_wrong_v1_method_fails_all_ops(tmp_path: Path) -> None:
    nodes = _v1_nodes()
    nodes[1] = V1_NODE.format(index=1, object_name="TestExecution", method="GETBYID")
    result = _run(tmp_path, nodes, "--all-ops")
    assert result.returncode != 0
    assert _missing(result.stderr) == ["delete a test execution"]


@pytest.mark.parametrize(
    "url",
    [
        "=js:'/v2/' + vars.P + '/teststeplogs?testCaseLogId=' + vars.L",
        "https://x/api/v2/p/teststeplogs",
    ],
)
def test_http_url_with_query_or_host_passes(tmp_path: Path, url: str) -> None:
    nodes = _http_nodes()
    nodes[-1] = HTTP_NODE.format(index=len(nodes) - 1, body=_http_body("GET", url))
    result = _run(tmp_path, nodes, "--all-ops")
    assert result.returncode == 0, result.stderr
