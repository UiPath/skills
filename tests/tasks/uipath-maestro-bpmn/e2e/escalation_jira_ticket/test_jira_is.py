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


PROJECTS = {"Result": "Success", "Data": [{"id": "10000", "key": "CE"}, {"id": "10001", "key": "OPS"}]}


def _types(*types: dict) -> dict:
    return {"Result": "Success", "Data": list(types)}


def _stub_lists(monkeypatch: pytest.MonkeyPatch, jira_is: ModuleType, types: dict) -> list[list[str]]:
    seen: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        seen.append(list(cmd))
        return Result(PROJECTS if "project" in cmd else types)

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)
    return seen


def test_the_issue_type_id_is_read_from_the_connections_site(monkeypatch: pytest.MonkeyPatch) -> None:
    """A project-scoped Task wins over a global one and over another project's Task."""
    jira_is = _load_module()
    types = _types(
        {"id": "3", "name": "Task"},
        {"id": "10109", "name": "Task", "scope": {"project": {"id": "10001"}}},
        {"id": "10009", "name": "Task", "scope": {"project": {"id": "10000"}}},
        {"id": "10007", "name": "Epic", "scope": {"project": {"id": "10000"}}},
    )
    seen = _stub_lists(monkeypatch, jira_is, types)

    assert jira_is.issuetype_id("conn-1") == "10009"
    assert jira_is.issuetype_id("conn-1") == "10009"
    assert len(seen) == 2  # one project list, one issuetype list, then cached


def test_a_record_s_nested_objects_are_not_records(monkeypatch: pytest.MonkeyPatch) -> None:
    """A type's `scope.project` is not an issue type, and a wrapper's list holds the records."""
    jira_is = _load_module()
    wrapped = {"Result": "Success", "Data": {"values": [{"id": "10009", "name": "Task", "scope": {"project": {"id": "10000"}}}]}}
    _stub_lists(monkeypatch, jira_is, wrapped)
    assert [t["id"] for t in jira_is._listed("conn-1", "issuetype")] == ["10009"]


def test_a_global_type_is_used_only_when_the_project_has_none(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    _stub_lists(monkeypatch, jira_is, _types({"id": "3", "name": "Task"}))
    assert jira_is.issuetype_id("conn-1") == "3"


def test_a_site_without_the_project_or_the_type_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    _stub_lists(monkeypatch, jira_is, _types({"id": "10007", "name": "Epic"}))
    with pytest.raises(RuntimeError, match="no 'Task' issue type in project CE"):
        jira_is.issuetype_id("conn-1")


def test_a_failed_list_is_read_once_more(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    answers = [{"Result": "Failure", "ErrorCode": "server_error"}, PROJECTS]
    seen: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        seen.append(list(cmd))
        return Result(answers.pop(0))

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)
    assert [p["key"] for p in jira_is._listed("conn-1", "project")] == ["CE", "OPS"]
    assert len(seen) == 2


def test_a_list_that_fails_twice_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    seen = _stub(monkeypatch, jira_is, {"Result": "Failure", "Message": "boom"})
    with pytest.raises(RuntimeError, match="run list project failed: boom"):
        jira_is._listed("conn-1", "project")
    assert len(seen) == 2


def test_an_unresolvable_issue_type_reads_as_no_issue_not_as_proof_of_deletion(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_issue reports None and issue_absent reports False, so a grader never crashes or passes a delete."""
    jira_is = _load_module()
    _stub_lists(monkeypatch, jira_is, _types({"id": "10007", "name": "Epic"}))
    assert jira_is.get_issue("conn-1", "CE-1") is None
    assert jira_is.issue_absent("conn-1", "CE-1") is False


def test_every_jira_helper_copy_resolves_the_issue_type_the_same_way() -> None:
    """The helpers are per-task copies by design; the resolver must not drift between them."""
    tasks = HERE.parents[2]
    copies = sorted(tasks.glob("uipath-maestro-*/**/jira_is.py"))
    assert len(copies) >= 9

    def resolver(path: Path) -> str:
        text = path.read_text(encoding="utf-8")
        return text[text.index("_ISSUETYPE_IDS: dict[str, str] = {}") : text.index("\ndef connection_id(")]

    reference = resolver(HERE / "_setup" / "jira_is.py")
    for path in copies:
        assert resolver(path) == reference, path
    # No Jira helper of any name pins the cloud site's Task id.
    for path in sorted(tasks.glob("uipath-maestro-*/**/*_is.py")):
        if not path.name.startswith("test_"):
            assert "11457" not in path.read_text(encoding="utf-8"), path
