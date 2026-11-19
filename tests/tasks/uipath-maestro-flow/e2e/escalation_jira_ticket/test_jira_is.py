"""Teardown contract for the escalation task's Jira helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).parent


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("escalation_jira_is", HERE / "_setup" / "jira_is.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, envelope: object, returncode: int = 0) -> None:
        self.stdout = json.dumps(envelope)
        self.stderr = ""
        self.returncode = returncode


def _stub(monkeypatch: pytest.MonkeyPatch, jira_is: ModuleType, envelope: object) -> list[list[str]]:
    seen: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        seen.append(list(cmd))
        return Result(envelope)

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)
    return seen


def test_delete_issue_confirms_and_reports_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI refuses an unconfirmed delete with a Failure envelope
    ("Confirmation required … Re-run with --yes"), which `delete_issue`
    correctly reports as NOT confirmed — so every run 08-19 → 09-01 printed
    `WARN: could NOT confirm deletion` and left its ticket in CE. `--yes` is
    the missing word."""
    jira_is = _load_module()
    seen = _stub(monkeypatch, jira_is, {"Result": "Success", "Data": {"Value": ""}})
    assert jira_is.delete_issue("conn", "CE-1257") is True
    (cmd,) = seen
    assert cmd[:5] == ["uip", "is", "resources", "run", "delete"]
    assert "--yes" in cmd and "issueId=CE-1257" in cmd


def test_delete_issue_unconfirmed_failure_is_not_a_deletion(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    _stub(monkeypatch, jira_is, {
        "Result": "Failure",
        "Message": "Confirmation required: this will delete resource 'issue' and cannot be undone.",
        "Instructions": "Re-run with --yes to confirm.",
    })
    assert jira_is.delete_issue("conn", "CE-1257") is False


def test_delete_issue_structured_404_counts_as_gone(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    _stub(monkeypatch, jira_is, {
        "Result": "Failure",
        "Message": "Request failed with status code '404': Issue does not exist or you do not have permission to see it.",
    })
    assert jira_is.delete_issue("conn", "CE-1257") is True


SHARED = HERE.parents[1] / "_shared" / "jira_is.py"
WORKSTREAM = {"Result": "Success", "Data": {"fields": {"summary": "[TEST] ESC-1", "issuetype": {"name": "Workstream"}}}}


def _load_shared() -> ModuleType:
    spec = importlib.util.spec_from_file_location("shared_jira_is", SHARED)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("load", [_load_module, _load_shared])
def test_get_issue_reads_any_issue_type(monkeypatch: pytest.MonkeyPatch, load) -> None:
    jira_is = load()
    seen = _stub(monkeypatch, jira_is, WORKSTREAM)
    fields = jira_is.get_issue("conn", "CE-9")
    assert fields["issuetype"]["name"] == "Workstream"
    (cmd,) = seen
    assert "curated_get_issue" in cmd and "issuetype" not in " ".join(cmd)


@pytest.mark.parametrize("load", [_load_module, _load_shared])
def test_issue_absent_reads_any_issue_type(monkeypatch: pytest.MonkeyPatch, load) -> None:
    jira_is = load()
    seen = _stub(monkeypatch, jira_is, WORKSTREAM)
    assert jira_is.issue_absent("conn", "CE-9") is False
    (cmd,) = seen
    assert "curated_get_issue" in cmd and "issuetype" not in " ".join(cmd)
