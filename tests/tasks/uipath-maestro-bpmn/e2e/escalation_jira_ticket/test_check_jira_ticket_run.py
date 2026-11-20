"""check_jira_ticket_run.py grades the run's Jira ticket and named outputs.

Fixtures: `sw_generic_issue_Process.bpmn` is the Studio Web agent's process
from run adhoc-2026-11-14_08-01-54, whose Create Issue step the builder
emitted as the generic `issue` object (POST /issue).
`nightly_curated_EscalationJiraTicket.bpmn` and
`run_seed.json` are from claude-code nightly 2026-11-17_04-23-30 (passed), which
used `curated_create_issue`.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checker = _load("check_jira_ticket_run", HERE / "check_jira_ticket_run.py")

SEED = json.loads((FIXTURES / "run_seed.json").read_text())
CORR = SEED["correlationId"]
SW = (FIXTURES / "sw_generic_issue_Process.bpmn").read_text()
NIGHTLY = (FIXTURES / "nightly_curated_EscalationJiraTicket.bpmn").read_text()


@pytest.fixture(autouse=True)
def _live_target(monkeypatch):
    monkeypatch.setattr(checker.escalation_is, "assert_live_target", lambda: {})


def _root(text: str) -> ET.Element:
    return ET.fromstring(text.encode())


def _process(text: str) -> ET.Element:
    return _root(text).find(f"{{{checker.BPMN_NS}}}process")


def _debug(step: str, status="Completed"):
    return {
        "InstanceId": "inst-1",
        "FinalStatus": "Completed",
        "ElementExecutions": [
            {"ElementId": "manualStart", "ElementType": "StartEvent", "Status": "Completed"},
            {"ElementId": step, "ElementType": "SendTask", "Status": status},
            {"ElementId": "done", "ElementType": "EndEvent", "Status": "Completed"},
        ],
    }


def _variables(step: str, key="CE-4242", exposed_key=None):
    exposed = {"Severity": "Sev1", "CaseKey": CORR, "JiraIssueKey": exposed_key or key}
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Globals": {"CorrelationId": CORR, **exposed},
                "Elements": [
                    {"ElementId": step, "Outputs": {"Response": {"id": "10001", "key": key, "self": "https://x/rest/api/3/issue/10001"}}},
                    {"ElementId": "done", "Outputs": exposed},
                ],
            }
        ]
    }


@pytest.mark.parametrize("text", [SW, NIGHTLY], ids=["sw-generic-issue", "nightly-curated"])
def test_static_checks_accept_both_create_operations(text):
    assert checker.jira_ids(_process(text))
    checker.assert_rule_encoded(text)


def test_the_studio_web_generic_issue_step_is_the_jira_step():
    assert checker.jira_ids(_process(SW)) == {"createJiraIssue"}


TASK_IN_CE = {
    "project": {"id": "10000", "key": "CE", "name": "Coder Eval"},
    "issuetype": {"id": SEED["issuetype_id"], "name": "Task", "subtask": False},
}


def _sandbox(tmp_path, monkeypatch, text, step, *, summary=None, exposed_key=None, fields=None):
    project = tmp_path / "EscalationJiraTicket" / "EscalationJiraTicket"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "EscalationJiraTicket", "ProjectType": "ProcessOrchestration"}')
    (project / "Process.bpmn").write_text(text)
    (tmp_path / "seed.json").write_text(json.dumps(SEED))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(checker, "run_debug", lambda *a, **k: (_debug(step), "inst-1"))
    monkeypatch.setattr(checker, "fetch_variables", lambda i: (_variables(step, exposed_key=exposed_key), ""))
    monkeypatch.setattr(checker, "fetch_incidents", lambda i: ([], []))
    monkeypatch.setattr(checker.jira_is, "connection_id", lambda: "conn")
    monkeypatch.setattr(
        checker.jira_is, "get_issue",
        lambda conn, key: {"summary": summary if summary is not None else f"[Sev1] {CORR} Production down", **(fields or TASK_IN_CE)},
    )


@pytest.mark.parametrize(
    "fields, problem",
    [
        ({**TASK_IN_CE, "project": {"id": "10001", "key": "OPS", "name": "Operations"}}, "project"),
        ({**TASK_IN_CE, "issuetype": {"id": "10004", "name": "Bug", "subtask": False}}, "Task"),
    ],
    ids=["other-project", "bug-not-task"],
)
def test_the_ticket_must_be_a_task_in_ce(tmp_path, monkeypatch, fields, problem):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue", fields=fields)
    with pytest.raises(checker.CheckFailure, match=problem):
        checker.main()


def test_main_checks_the_live_target_before_any_debug(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")

    def refuse():
        raise checker.CheckFailure("wrong tenant")

    def no_debug(*a, **k):
        raise AssertionError("debug ran before the target check")

    monkeypatch.setattr(checker.escalation_is, "assert_live_target", refuse)
    monkeypatch.setattr(checker, "run_debug", no_debug)
    monkeypatch.setattr(checker, "import_exact", no_debug)
    with pytest.raises(checker.CheckFailure, match="wrong tenant"):
        checker.main()


def test_two_owned_issues_from_the_jira_step_fail(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")
    variables = _variables("createJiraIssue")
    variables["Variables"][0]["Elements"].insert(
        1, {"ElementId": "createJiraIssue", "Outputs": {"Response": {"id": "9", "key": "CE-9"}}}
    )
    monkeypatch.setattr(checker, "fetch_variables", lambda i: (variables, ""))
    monkeypatch.setattr(
        checker.jira_is, "get_issue", lambda conn, key: {"summary": f"[Sev1] {CORR} down", **TASK_IN_CE}
    )
    with pytest.raises(checker.CheckFailure, match="exactly one Jira issue"):
        checker.main()


def test_the_summary_format_is_only_an_example(tmp_path, monkeypatch):
    """The prompt gives "[Sev1] <correlationId> <subject>" "for example"; only
    the correlationId is required."""
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue", summary=f"Checkout outage ({CORR})")
    checker.main()


def test_studio_web_process_passes_end_to_end(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")
    checker.main()
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-4242"]


def test_a_ticket_without_this_runs_correlation_id_fails_and_is_not_journalled(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue", summary="[Sev1] someone else's ticket")
    with pytest.raises(checker.CheckFailure, match="summary carries"):
        checker.main()
    assert not (tmp_path / ".created_keys").exists()


def test_only_the_key_owned_by_this_run_is_journalled(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")
    variables = _variables("createJiraIssue")
    variables["Variables"][0]["Elements"].insert(
        1, {"ElementId": "createJiraIssue", "Outputs": {"Response": {"id": "9", "key": "CE-9"}}}
    )
    monkeypatch.setattr(checker, "fetch_variables", lambda i: (variables, ""))
    monkeypatch.setattr(
        checker.jira_is, "get_issue",
        lambda conn, key: {"summary": f"[Sev1] {CORR} down" if key == "CE-4242" else "an existing ticket", **TASK_IN_CE},
    )
    checker.main()
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-4242"]


def test_a_variables_read_failure_still_journals_this_runs_key(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")
    debug = {**_debug("createJiraIssue"), "Output": f"created CE-4242 and CE-9 for {CORR}"}
    monkeypatch.setattr(checker, "run_debug", lambda *a, **k: (debug, "inst-1"))

    def unreadable(instance_id):
        raise subprocess.TimeoutExpired("uip", 120)

    monkeypatch.setattr(checker, "fetch_variables", unreadable)
    monkeypatch.setattr(
        checker.jira_is, "get_issue",
        lambda conn, key: {"summary": f"[Sev1] {CORR} down" if key == "CE-4242" else "someone else's"},
    )
    with pytest.raises(subprocess.TimeoutExpired):
        checker.main()
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-4242"]


def test_a_created_key_that_is_not_journalled_is_reported(tmp_path, monkeypatch, capsys):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue", summary="[Sev1] someone else's ticket")
    with pytest.raises(checker.CheckFailure):
        checker.main()
    assert "NOTE: not journaled, delete by hand if this run created them: CE-4242" in capsys.readouterr().out


def test_an_unreadable_key_is_reported(tmp_path, monkeypatch, capsys):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")

    def unreadable(conn, key):
        raise checker.CheckFailure("read failed")

    monkeypatch.setattr(checker.jira_is, "get_issue", unreadable)
    with pytest.raises(checker.CheckFailure):
        checker.main()
    assert "NOTE: not journaled, delete by hand if this run created them: CE-4242" in capsys.readouterr().out


def test_a_journaled_key_is_not_reported(tmp_path, monkeypatch, capsys):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue")
    checker.main()
    assert "NOTE" not in capsys.readouterr().out


def test_jira_issue_key_output_must_be_the_created_key(tmp_path, monkeypatch):
    _sandbox(tmp_path, monkeypatch, SW, "createJiraIssue", exposed_key="CE-1")
    with pytest.raises(checker.CheckFailure, match="jiraIssueKey"):
        checker.main()


def test_hardcoded_severity_fails():
    hardcoded = SW.replace("Sev2", "x").replace("Sev3", "y")
    with pytest.raises(checker.CheckFailure, match="never names"):
        checker.assert_rule_encoded(hardcoded)
