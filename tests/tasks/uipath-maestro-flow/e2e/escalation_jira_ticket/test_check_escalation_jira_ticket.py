"""Unit tests for the EscalationJiraTicket effects grader.

The flow is cut down from what agents built on the 2026-11-17 nightly (manual
trigger, the real `create-issue` node bound to the CE connection, End). The
Jira tenant is faked at the `jira_is` boundary: `get_issue` returns the issue's
`fields` like the curated read does, or None when the key does not exist.
"""

from __future__ import annotations

import importlib.util
import json
import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
CORR = "ESC-JIRA-1e90fee1"
SEED = {
    "correlationId": CORR,
    "project_key": "CE",
    "inputs": {"correlationId": CORR, "customerTier": "Enterprise", "productionDown": True,
               "workaroundAvailable": False},
    "expected": {"severity": "Sev1", "engineeringNeeded": True, "caseKey": CORR},
}
CREATE_NODE = {
    "id": "createJiraIssue",
    "type": "uipath.connector.uipath-atlassian-jira.create-issue",
    "inputs": {
        "detail": {
            "connector": "uipath-atlassian-jira",
            "endpoint": "/curated_create_issue",
            "connectionId": "ac8506ff-65fd-4a7d-8698-c6a912134b11",
            "connectionFolderKey": "5da18ec0-7de1-4e57-aaf1-ddc8a369c199",
            "bodyParameters": {"fields.project.key": "CE", "fields.issuetype.id": "11457"},
        }
    },
}


@pytest.fixture
def grader(tmp_path, monkeypatch):
    project = tmp_path / "EscalationJiraTicket" / "EscalationJiraTicket"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"Name": "EscalationJiraTicket", "ProjectType": "Flow"}))
    (project / "new.flow").write_text(json.dumps({"nodes": [
        {"id": "start", "type": "core.trigger.manual"},
        CREATE_NODE,
        {"id": "end", "type": "core.control.end"},
    ], "edges": []}))
    monkeypatch.chdir(tmp_path)
    spec = importlib.util.spec_from_file_location(
        "check_escalation_jira_ticket", os.path.join(HERE, "check_escalation_jira_ticket.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    issues = {"CE-3481": {"summary": f"[Sev1] {CORR} Production down: checkout API returning 500s"},
              "CE-17": {"summary": "an older ticket"}}
    monkeypatch.setattr(module.jira_is, "connection_id", lambda: "conn")
    monkeypatch.setattr(module.jira_is, "get_issue", lambda conn, key: issues.get(key))
    return module


def _payload(*, key="CE-3481", outputs=None, executed=("start", "createJiraIssue", "end")):
    globals_ = {"severity": "Sev1", "engineeringNeeded": True, "caseKey": CORR, "jiraIssueKey": key,
                "createJiraIssue.output": {"id": "52114", "key": key, "self": f"https://x/rest/api/3/issue/{key}"}}
    globals_.update(outputs or {})
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in executed],
        "variables": {"globals": globals_},
    }


def test_passes_with_no_script_node_and_records_the_key(grader, tmp_path):
    # The old grader required a Script whose own output carried severity and
    # engineeringNeeded; this flow derives them in the End mapping.
    assert grader.check_payload(_payload(), SEED) == "CE-3481"
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]


def test_fails_when_the_ticket_does_not_carry_the_correlation_id(grader):
    with pytest.raises(SystemExit) as exc:
        grader.check_payload(_payload(key="CE-17"), SEED)
    assert "summary contains" in str(exc.value)


def test_fails_when_the_key_is_not_in_jira(grader):
    with pytest.raises(SystemExit) as exc:
        grader.check_payload(_payload(key="CE-999999"), SEED)
    assert "summary contains" in str(exc.value)


def test_fails_when_the_create_step_did_not_run(grader):
    with pytest.raises(SystemExit) as exc:
        grader.check_payload(_payload(executed=("start", "end")), SEED)
    assert "Create Issue step completed" in str(exc.value)


def test_fails_when_engineering_needed_is_missing(grader):
    with pytest.raises(SystemExit) as exc:
        grader.check_payload(_payload(outputs={"engineeringNeeded": None}), SEED)
    assert "engineeringNeeded" in str(exc.value)


def test_fails_when_jira_issue_key_is_not_returned(grader, tmp_path):
    with pytest.raises(SystemExit) as exc:
        grader.check_payload(_payload(outputs={"jiraIssueKey": ""}), SEED)
    assert "jiraIssueKey" in str(exc.value)
    # The ticket was still created by this run, so teardown must delete it.
    assert (tmp_path / ".created_keys").read_text().split() == ["CE-3481"]
