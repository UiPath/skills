"""Test Manager CRUD, lifecycle and generic-record checkers: V1 and connector-mode HTTP shapes."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import bpmn_check  # noqa: E402
import check_testmanager_generic_records as generic  # noqa: E402
from testmanager_fixtures import HTTP_NODE, LEGACY_SDK_HTTP_NODE, TM_KEY  # noqa: E402

HERE = Path(__file__).parent

NODE = """
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

# (label, objectName, V1 method, HTTP verb, IS enrichment path)
TESTCASE = [
    ("create a test case", "TestCase", "POST", "POST", "/v2/{ProjectId}/testcases"),
    ("get the test case", "TestCase", "GETBYID", "GET", "/v2/{ProjectId}/testcases/{id}"),
    ("update the test case", "TestCase", "PATCH", "PATCH", "/v2/{ProjectId}/testcases/{id}"),
    ("delete the test case", "TestCase", "DELETE", "DELETE", "/v2/{ProjectId}/testcases/{id}"),
    ("execute the test case(s)", "ExecuteTestCases", "POST", "POST",
     "/v2/{ProjectId}/testcases/startexecute"),
]
REQUIREMENT = [
    ("create a requirement", "Requirement", "POST", "POST", "/v2/{ProjectId}/requirements"),
    ("get the requirement", "Requirement", "GETBYID", "GET", "/v2/{ProjectId}/requirements/{id}"),
    ("update the requirement", "Requirement", "PATCH", "PATCH",
     "/v2/{ProjectId}/requirements/{id}"),
    ("delete the requirement", "Requirement", "DELETE", "DELETE",
     "/v2/{ProjectId}/requirements/{id}"),
    ("assign test cases to the requirement", "AssignTestCasesToRequirement", "POST", "POST",
     "/v2/{ProjectId}/requirements/{Id}/assigntestcases"),
    ("get the assigned test cases for the requirement", "GetAssignedTestCasesForRequirement",
     "GET", "GET", "/v2/{ProjectId}/requirements/{Id}/assignedtestcaseids"),
]
TESTSET = [
    ("create a test set", "TestSet", "POST", "POST", "/v2/{ProjectId}/testsets"),
    ("get the test set", "TestSet", "GETBYID", "GET", "/v2/{ProjectId}/testsets/{id}"),
    ("update the test set", "TestSet", "PATCH", "PATCH", "/v2/{ProjectId}/testsets/{id}"),
    ("delete the test set", "TestSet", "DELETE", "DELETE", "/v2/{ProjectId}/testsets/{id}"),
    ("assign test cases to the test set", "AssignTestCasesToTestSet", "POST", "POST",
     "/v2/{ProjectId}/testsets/{id}/assigntestcases"),
    ("list the test cases assigned to the test set", "GetAssignedTestCasesForTestSet",
     "GET", "GET", "/v2/{ProjectId}/testsets/{id}/assignedtestcaseids"),
    ("execute (run) the test set", "ExecuteTestSet", "POST", "POST",
     "/v2/{ProjectId}/testsets/{testSetId}/startexecute"),
]
GENERIC = [
    ("insert a record", "CreateDefect", "POST", "POST", "/v2/{ProjectId}/defects"),
    ("get a record", "TestStep", "GETBYID", "GET", "/v2/{ProjectId}/teststeps/{id}"),
    ("update a record", "Requirement", "PATCH", "PATCH", "/v2/{ProjectId}/requirements/{id}"),
    ("delete a record", "DeleteAttachment", "DELETE", "DELETE",
     "/v2/{projectId}/attachments/{objectType}/{id}"),
    ("list records", "GetTestStepLogs", "GET", "GET", "/v2/{projectId}/teststeplogs"),
]
# Test Manager catalog (`registry get` IsEnrichment.Operation.Path), by IS operation.
CATALOG = {
    "Create": [
        ("AssignTestCasesToRequirement", "/v2/{ProjectId}/requirements/{Id}/assigntestcases"),
        ("AssignTestCasesToTestSet", "/v2/{ProjectId}/testsets/{id}/assigntestcases"),
        ("CreateDefect", "/v2/{ProjectId}/defects"),
        ("ExecuteTestCases", "/v2/{ProjectId}/testcases/startexecute"),
        ("ExecuteTestSet", "/v2/{ProjectId}/testsets/{testSetId}/startexecute"),
        ("ReportRunCheckpoint", "/v2/factories/runs/checkpoints"),
        ("Requirement", "/v2/{ProjectId}/requirements"),
        ("TestCase", "/v2/{ProjectId}/testcases"),
        ("TestSet", "/v2/{ProjectId}/testsets"),
        ("TestStep", "/v2/{ProjectId}/teststeps"),
        ("UploadAttachment", "/v2/{projectId}/attachments/{objType}/{id}/upload"),
    ],
    "Retrieve": [
        ("DownloadAssertion",
         "/v2/{projectId}/testcaselogartifacts/{id}/assertions/{assertionId}/downloadscreenshot"),
        ("DownloadAttachment", "/v2/{projectId}/attachments/{objectType}/{id}/download"),
        ("GetDefect", "/v2/{ProjectId}/defects/{id}"),
        ("GetProjectByPrefix", "/v2/projects/prefix/{projectPrefix}"),
        ("Requirement", "/v2/{ProjectId}/requirements/{id}"),
        ("TestCase", "/v2/{ProjectId}/testcases/{id}"),
        ("TestCaseLog", "/v2/{projectId}/testcaselogs/{id}"),
        ("TestExecution", "/v2/{projectId}/testexecutions/{id}"),
        ("TestSet", "/v2/{ProjectId}/testsets/{id}"),
        ("TestStep", "/v2/{ProjectId}/teststeps/{id}"),
    ],
    "Update": [
        ("Requirement", "/v2/{ProjectId}/requirements/{id}"),
        ("TestCase", "/v2/{ProjectId}/testcases/{id}"),
        ("TestSet", "/v2/{ProjectId}/testsets/{id}"),
        ("TestStep", "/v2/{ProjectId}/teststeps/{id}"),
    ],
    "Delete": [
        ("DeleteAttachment", "/v2/{projectId}/attachments/{objectType}/{id}"),
        ("Requirement", "/v2/{ProjectId}/requirements/{id}"),
        ("TestCase", "/v2/{ProjectId}/testcases/{id}"),
        ("TestExecution", "/v2/{projectId}/testexecutions/{id}"),
        ("TestSet", "/v2/{ProjectId}/testsets/{id}"),
    ],
    "List": [
        ("GetAssertions", "/v2/{projectId}/testcaselogartifacts/{id}/assertions"),
        ("GetAssignedTestCasesForRequirement",
         "/v2/{ProjectId}/requirements/{Id}/assignedtestcaseids"),
        ("GetAssignedTestCasesForTestSet", "/v2/{ProjectId}/testsets/{id}/assignedtestcaseids"),
        ("GetAttachments", "/v2/{projectId}/attachments/{ObjectType}/{Id}/all"),
        ("GetImpactedTransactions", "/v2/{ProjectId}/sapplanner/transports/coverage"),
        ("GetRobotLogs", "/v2/{projectId}/orchestrator/testexecution/{id}/robotlogs/paged"),
        ("GetTestCaseLogsOfTestExecution",
         "/v2/{projectId}/testcaselogs/testexecution/{testExecutionId}/paged"),
        ("GetTestStepLogs", "/v2/{projectId}/teststeplogs"),
        ("GetTestSteps", "/v2/{ProjectId}/teststeps/testcase/{Id}"),
        ("Project", "/v2/projects"),
        ("Requirement", "/v2/{ProjectId}/requirements"),
        ("TestCase", "/v2/{ProjectId}/testcases"),
        ("TestExecution", "/v2/{projectId}/testexecutions"),
        ("TestManagerEvents", "/TestManagerEvents"),
        ("TestSet", "/v2/{ProjectId}/testsets"),
    ],
}
GENERIC_TARGETS = [
    (index, verb, target)
    for index, (verb, operation) in enumerate(
        [("POST", "Create"), ("GET", "Retrieve"), ("PATCH", "Update"), ("DELETE", "Delete"),
         ("GET", "List")]
    )
    for target in CATALOG[operation]
]

CHECKERS = {
    "crud_grounded": (("--node-types",), TESTCASE[:2]),
    "testcase_lifecycle": (("--all-ops",), TESTCASE),
    "requirement_lifecycle": (("--all-ops",), REQUIREMENT),
    "testset_lifecycle": (("--all-ops",), TESTSET),
    "generic_records": (("--all-ops",), GENERIC),
}
CASES = [(name, i) for name, (_, ops) in CHECKERS.items() for i in range(len(ops))]
SLOT_CASES = [
    (name, i, slot)
    for name, (_, ops) in CHECKERS.items()
    for i, op in enumerate(ops)
    for slot in range(op[4].count("{"))
]
NO_CONNECTOR = "no bpmn:sendTask calls the Test Manager connector"


def _run(tmp_path: Path, name: str, body: str, *args: str) -> subprocess.CompletedProcess:
    (tmp_path / "Process.bpmn").write_text(
        '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        f'<bpmn:process id="Process_1">{body}</bpmn:process></bpmn:definitions>'
    )
    result = subprocess.run(
        [sys.executable, str(HERE / f"check_testmanager_{name}.py"), *args],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    result.output = result.stdout + result.stderr
    return result


def _filled(path: str, keep: int = -1, spelling: str = "{{{}}}") -> str:
    """``=js:`` url with every placeholder but index ``keep`` filled from a
    variable, and ``keep`` written as ``spelling`` of its name."""
    slots = iter(range(path.count("{")))

    def fill(match: re.Match[str]) -> str:
        if next(slots) == keep:
            return spelling.format(match.group(1))
        return "' + vars.Var_Id + '"

    return "=js:'" + re.sub(r"\{([^}]+)\}", fill, path) + "'"


def _http_node(index: int, method: str, url: str, template: str = HTTP_NODE,
               **overrides: str) -> str:
    body = {
        "authentication": "connector",
        "method": method,
        "targetConnector": TM_KEY,
        "path": url,
        "url": url,
    }
    body.update(overrides)
    return template.format(index=index, body=json.dumps(body))


def _http_nodes(ops: list, **overrides: str) -> list[str]:
    return [_http_node(i, op[3], _filled(op[4]), **overrides) for i, op in enumerate(ops)]


def _missing(ops: list, stderr: str) -> list[str]:
    return [op[0] for op in ops if f"\n  {op[0]} (" in stderr]


@pytest.mark.parametrize("name", CHECKERS)
def test_v1_activity_passes(tmp_path: Path, name: str) -> None:
    args, ops = CHECKERS[name]
    body = "".join(NODE.format(index=i, object_name=op[1], method=op[2])
                   for i, op in enumerate(ops))
    result = _run(tmp_path, name, body, *args)
    assert result.returncode == 0, result.output


@pytest.mark.parametrize("name", CHECKERS)
def test_connector_mode_http_passes(tmp_path: Path, name: str) -> None:
    args, ops = CHECKERS[name]
    result = _run(tmp_path, name, "".join(_http_nodes(ops)), *args)
    assert result.returncode == 0, result.output
    for label, *_ in ops:
        assert f"OK: {label} -> Task_" in result.stdout


@pytest.mark.parametrize("name", CHECKERS)
def test_mixed_activity_and_http_passes(tmp_path: Path, name: str) -> None:
    args, ops = CHECKERS[name]
    nodes = _http_nodes(ops)
    nodes[0] = NODE.format(index=0, object_name=ops[0][1], method=ops[0][2])
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode == 0, result.output


@pytest.mark.parametrize("name", CHECKERS)
@pytest.mark.parametrize(
    "overrides", [{"targetConnector": "uipath-salesforce-slack"}, {"authentication": "manual"}]
)
def test_http_not_through_test_manager_fails(tmp_path: Path, name: str, overrides: dict) -> None:
    args, ops = CHECKERS[name]
    result = _run(tmp_path, name, "".join(_http_nodes(ops, **overrides)), *args)
    assert result.returncode != 0
    assert NO_CONNECTOR in result.output
    assert "context connectorKey 'uipath-uipath-http'" in result.output


@pytest.mark.parametrize("name", CHECKERS)
def test_legacy_sdk_connector_http_fails(tmp_path: Path, name: str) -> None:
    args, ops = CHECKERS[name]
    nodes = [_http_node(i, op[3], _filled(op[4]), LEGACY_SDK_HTTP_NODE)
             for i, op in enumerate(ops)]
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode != 0
    assert NO_CONNECTOR in result.output
    assert "objectName not 'http-request'" in result.output


@pytest.mark.parametrize("name, index", CASES)
def test_missing_operation_fails(tmp_path: Path, name: str, index: int) -> None:
    args, ops = CHECKERS[name]
    nodes = _http_nodes(ops)
    del nodes[index]
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode != 0
    assert _missing(ops, result.stderr) == [ops[index][0]]


@pytest.mark.parametrize("name, index, slot", SLOT_CASES)
def test_unfilled_placeholder_fails(tmp_path: Path, name: str, index: int, slot: int) -> None:
    args, ops = CHECKERS[name]
    nodes = _http_nodes(ops)
    op = ops[index]
    nodes[index] = _http_node(index, op[3], _filled(op[4], keep=slot))
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode != 0
    assert _missing(ops, result.stderr) == [op[0]]
    assert repr(op[4]) in result.stderr
    assert "with every placeholder filled" in result.stderr


@pytest.mark.parametrize("spelling", ["${{{}}}", "<{}>", ":{}", "{{}}"])
@pytest.mark.parametrize("name", CHECKERS)
def test_unfilled_placeholder_spelling_fails(tmp_path: Path, name: str, spelling: str) -> None:
    args, ops = CHECKERS[name]
    nodes = _http_nodes(ops)
    op = ops[1]
    nodes[1] = _http_node(1, op[3], _filled(op[4], keep=op[4].count("{") - 1, spelling=spelling))
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode != 0
    assert _missing(ops, result.stderr) == [op[0]]


def test_update_on_execute_path_fails(tmp_path: Path) -> None:
    nodes = _http_nodes(TESTCASE)
    nodes[2] = _http_node(2, "PATCH", "=js:'/v2/' + vars.Var_Id + '/testcases/startexecute'")
    result = _run(tmp_path, "testcase_lifecycle", "".join(nodes), "--all-ops")
    assert result.returncode != 0
    assert _missing(TESTCASE, result.stderr) == ["update the test case"]


@pytest.mark.parametrize("name, index", CASES)
def test_wrong_verb_fails(tmp_path: Path, name: str, index: int) -> None:
    args, ops = CHECKERS[name]
    nodes = _http_nodes(ops)
    op = ops[index]
    wrong = "GETBYID" if op[3] == "GET" else "HEAD"
    nodes[index] = _http_node(index, wrong, _filled(op[4]))
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode != 0
    assert _missing(ops, result.stderr) == [op[0]]


@pytest.mark.parametrize("name", ["testcase_lifecycle", "requirement_lifecycle", "testset_lifecycle"])
def test_lifecycle_update_rejects_put(tmp_path: Path, name: str) -> None:
    args, ops = CHECKERS[name]
    nodes = _http_nodes(ops)
    nodes[2] = _http_node(2, "PUT", _filled(ops[2][4]))
    result = _run(tmp_path, name, "".join(nodes), *args)
    assert result.returncode != 0
    assert _missing(ops, result.stderr) == [ops[2][0]]


@pytest.mark.parametrize(
    "operation, table",
    [("Create", generic.CREATE), ("Retrieve", generic.RETRIEVE), ("Update", generic.UPDATE),
     ("Delete", generic.DELETE), ("List", generic.LIST)],
)
def test_generic_tables_match_the_catalog(operation: str, table: list) -> None:
    assert table == CATALOG[operation]


@pytest.mark.parametrize("index, verb, target", GENERIC_TARGETS,
                         ids=[f"{i}-{t[0]}" for i, _, t in GENERIC_TARGETS])
def test_generic_accepts_every_catalog_object(tmp_path: Path, index: int, verb: str,
                                               target: tuple) -> None:
    args, ops = CHECKERS["generic_records"]
    v1 = [NODE.format(index=i, object_name=op[1], method=op[2]) for i, op in enumerate(ops)]
    http = _http_nodes(ops)
    v1[index] = NODE.format(index=index, object_name=target[0], method=ops[index][2])
    http[index] = _http_node(index, verb, _filled(target[1]))
    for nodes in (v1, http):
        result = _run(tmp_path, "generic_records", "".join(nodes), *args)
        assert result.returncode == 0, result.output


def test_generic_operations_pass_validation() -> None:
    with pytest.raises(SystemExit) as exc:
        bpmn_check.require_operations([], generic.OPERATIONS, "generic record")
    assert "\n  get a record (" in str(exc.value)


def test_generic_update_accepts_put(tmp_path: Path) -> None:
    args, ops = CHECKERS["generic_records"]
    nodes = _http_nodes(ops)
    nodes[2] = _http_node(2, "PUT", _filled(ops[2][4]))
    result = _run(tmp_path, "generic_records", "".join(nodes), *args)
    assert result.returncode == 0, result.output


def test_generic_v1_get_is_list_not_get(tmp_path: Path) -> None:
    args, ops = CHECKERS["generic_records"]
    nodes = [NODE.format(index=i, object_name=op[1], method=op[2]) for i, op in enumerate(ops)]
    nodes[1] = NODE.format(index=1, object_name="TestCase", method="GET")
    for body in ("".join(nodes), "".join(nodes[:4])):
        result = _run(tmp_path, "generic_records", body, *args)
        assert result.returncode != 0
        assert _missing(ops, result.stderr) == [ops[1][0]]


@pytest.mark.parametrize("index, object_name", [(0, "TestCaseLog"), (2, "TestExecution"),
                                                (3, "Project"), (4, "Other")])
def test_generic_rejects_object_without_the_operation(tmp_path: Path, index: int,
                                                      object_name: str) -> None:
    args, ops = CHECKERS["generic_records"]
    nodes = [NODE.format(index=i, object_name=op[1], method=op[2]) for i, op in enumerate(ops)]
    nodes[index] = NODE.format(index=index, object_name=object_name, method=ops[index][2])
    result = _run(tmp_path, "generic_records", "".join(nodes), *args)
    assert result.returncode != 0
    assert _missing(ops, result.stderr) == [ops[index][0]]
