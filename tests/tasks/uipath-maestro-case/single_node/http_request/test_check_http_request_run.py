"""check_http_request_run.py against a real debug run's instance evidence.

testdata/ holds what alpha returned for a real HttpRequestSingleCase debug run:
the `case debug` Data, the instance list row and `instance variables-all`, plus
that run's plan. No tenant is touched.

    cd tests && uv run -q --with pytest python -m pytest -q tasks/uipath-maestro-case/single_node/http_request
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
EVIDENCE = json.loads((HERE / "testdata" / "http_run_evidence.json").read_text())
PLAN = json.loads((HERE / "testdata" / "plan.json").read_text())


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


grader = _load("check_http_request_run_under_test", HERE / "check_http_request_run.py")
evidence_mod = _load(
    "case_run_evidence_http_under_test", HERE.parent.parent / "_shared" / "case_run_evidence.py"
)


def _evidence(variables_all: dict | None = None):
    return grader.RunEvidence((variables_all or EVIDENCE["variables_all"])["Data"])


def _globals(variables_all: dict) -> dict:
    return next(b for b in variables_all["Data"]["Variables"] if b["ParentElementId"] is None)["Globals"]


def test_the_recorded_run_passes() -> None:
    assert grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence()) == "'Post Invoice'"


def test_reads_the_variable_by_its_plan_name_although_the_cli_pascalcases_it() -> None:
    evidence = _evidence()
    assert "EchoResponse" in evidence.globals
    assert evidence.value("echoResponse")["Json"]["Probe"] == "skills-case-http-7f3a"


def test_an_echo_without_the_probe_fails() -> None:
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    _globals(variables_all)["EchoResponse"] = {"Json": {"InvoiceNumber": "INV-1042"}}
    with pytest.raises(SystemExit, match="skills-case-http-7f3a"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(variables_all))


def test_an_unbound_response_fails() -> None:
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    _globals(variables_all)["EchoResponse"] = {}
    with pytest.raises(SystemExit, match="does not hold the echo"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(variables_all))


def test_a_run_where_the_call_failed_fails() -> None:
    debug = copy.deepcopy(EVIDENCE["debug"]["Data"])
    for execution in debug["elementExecutions"]:
        if execution["elementId"] == "trBBgDSNV":
            execution["status"] = "Failed"
    with pytest.raises(SystemExit, match="'Post Invoice' finished 'Failed'"):
        grader.check_run(PLAN, debug, _evidence())


def test_any_task_name_and_variable_layout_pass() -> None:
    """Nothing pins the task's name or id: a renamed task that did the call passes."""
    plan = copy.deepcopy(PLAN)
    debug = copy.deepcopy(EVIDENCE["debug"]["Data"])
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    for node in plan["nodes"]:
        for lane in node["data"].get("tasks") or []:
            for task in lane:
                task["id"], task["displayName"] = "tOther1", "Send invoice to echo"
    for execution in debug["elementExecutions"]:
        if execution["elementId"] == "trBBgDSNV":
            execution["elementId"] = "tOther1"
    for block in variables_all["Data"]["Variables"]:
        for element in block["Elements"]:
            if element["ElementId"] == "trBBgDSNV":
                element["ElementId"] = "tOther1"
    assert grader.check_run(plan, debug, _evidence(variables_all)) == "'Send invoice to echo'"


def test_a_credential_header_fails() -> None:
    plan = copy.deepcopy(PLAN)
    task = next(t for n in plan["nodes"] for lane in n["data"].get("tasks") or [] for t in lane)
    body = next(i for i in task["data"]["inputs"] if i["name"] == "body")["body"]
    body["headers"]["Authorization"] = "Bearer x"
    with pytest.raises(SystemExit, match="Authorization"):
        grader.check_no_credential_headers(plan)


def test_folder_key_is_found_in_the_instance_list(monkeypatch: pytest.MonkeyPatch) -> None:
    listed = json.dumps(EVIDENCE["instance_list"])

    def fake_run(cmd, **kwargs):  # noqa: ANN001, ANN003
        return subprocess.CompletedProcess(cmd, 0, listed, "")

    monkeypatch.setattr(evidence_mod, "_run", lambda cmd, **kw: fake_run(cmd))
    instance = EVIDENCE["debug"]["Data"]["instanceId"]
    assert evidence_mod.folder_key_of(instance, "2026-11-18T13:00:00Z") == (
        EVIDENCE["instance_list"]["Data"][0]["FolderKey"]
    )


def test_an_instance_missing_from_the_list_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    empty = json.dumps({"Result": "Success", "Data": [], "Pagination": {"HasMore": False}})
    monkeypatch.setattr(
        evidence_mod, "_run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 0, empty, "")
    )
    monkeypatch.setattr(evidence_mod, "LIST_SLEEP_S", 0)
    with pytest.raises(SystemExit, match="is not in"):
        evidence_mod.folder_key_of("00000000-0000-0000-0000-000000000000", "2026-11-18T13:00:00Z")


def test_the_instance_list_stops_at_its_deadline(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = [0.0]
    calls = []
    paged = json.dumps(
        {"Result": "Success", "Data": [], "Pagination": {"HasMore": True, "NextPage": "n"}}
    )

    def slow_run(cmd, **kw):  # noqa: ANN001, ANN003
        calls.append(kw["timeout"])
        clock[0] += kw["timeout"]
        return subprocess.CompletedProcess(cmd, 0, paged, "")

    monkeypatch.setattr(evidence_mod, "_run", slow_run)
    monkeypatch.setattr(evidence_mod.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(evidence_mod.time, "sleep", lambda s: clock.__setitem__(0, clock[0] + s))
    with pytest.raises(SystemExit, match="is not in"):
        evidence_mod.folder_key_of("00000000-0000-0000-0000-000000000000", "2026-11-18T13:00:00Z")
    assert clock[0] <= evidence_mod.LIST_DEADLINE_S
    assert calls


@pytest.mark.parametrize("header", ["Authorization", "XApiKey", "ProxyAuthorization"])
def test_a_credential_header_the_service_received_fails(header: str) -> None:
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    _globals(variables_all)["EchoResponse"]["Headers"][header] = "secret"
    with pytest.raises(SystemExit, match=header):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(variables_all))


def test_a_cookie_the_service_replayed_from_its_own_set_cookie_passes() -> None:
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    _globals(variables_all)["EchoResponse"]["Headers"]["Cookie"] = "sails.sid=s%3Aabc"
    assert grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(variables_all)) == "'Post Invoice'"


def test_a_cookie_header_in_the_plan_fails() -> None:
    plan = copy.deepcopy(PLAN)
    task = next(t for n in plan["nodes"] for lane in n["data"].get("tasks") or [] for t in lane)
    body = next(i for i in task["data"]["inputs"] if i["name"] == "body")["body"]
    body["headers"]["Cookie"] = "sid=1"
    with pytest.raises(SystemExit, match="Cookie"):
        grader.check_no_credential_headers(plan)


def test_a_variable_bound_to_the_request_instead_of_the_echo_fails() -> None:
    """The request inputs carry the invoice, the probe and the source query too."""
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    request = next(
        element["Inputs"]["Body"]
        for block in variables_all["Data"]["Variables"]
        for element in block["Elements"]
        if element["ElementId"] == "trBBgDSNV"
    )
    _globals(variables_all)["EchoResponse"] = copy.deepcopy(request)
    with pytest.raises(SystemExit, match="Args"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(variables_all))


def _recorded(mutate) -> dict:
    variables_all = copy.deepcopy(EVIDENCE["variables_all"])
    mutate(_globals(variables_all)["EchoResponse"])
    return variables_all


@pytest.mark.parametrize("accept", [None, "text/html", "*/*"])
def test_an_echo_without_the_json_accept_header_fails(accept: object) -> None:
    def mutate(echo: dict) -> None:
        echo["Headers"].pop("Accept")
        if accept is not None:
            echo["Headers"]["Accept"] = accept

    with pytest.raises(SystemExit, match="Accept"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(_recorded(mutate)))


@pytest.mark.parametrize("field", ["InvoiceNumber", "Probe"])
def test_values_sent_under_other_body_fields_fail(field: str) -> None:
    def mutate(echo: dict) -> None:
        echo["Json"] = {"Other" + k if k == field else k: v for k, v in echo["Json"].items()}

    with pytest.raises(SystemExit, match="body"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(_recorded(mutate)))


def test_values_sent_as_text_instead_of_a_json_body_fail() -> None:
    def mutate(echo: dict) -> None:
        echo["Json"] = None
        echo["Data"] = "INV-1042 skills-case-http-7f3a"

    with pytest.raises(SystemExit, match="body"):
        grader.check_run(PLAN, EVIDENCE["debug"]["Data"], _evidence(_recorded(mutate)))
