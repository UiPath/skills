"""A missing Jira connection fails pre_run with the preflight message, not a StopIteration."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).parent
TASKS = ("jira_create_issue", "jira_get_issue", "jira_lifecycle", "jira_search_triage")


class Result:
    def __init__(self, envelope: object) -> None:
        self.stdout = json.dumps(envelope)
        self.stderr = ""
        self.returncode = 0


def _load(task: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"{task}_jira_is", HERE / task / "_setup" / "jira_is.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stub(monkeypatch: pytest.MonkeyPatch, jira_is: ModuleType, connections: list[dict]) -> None:
    def fake_run(cmd, **kwargs):
        if cmd[1] == "or":
            return Result({"Result": "Success", "Data": {"Key": "folder-key"}})
        return Result({"Result": "Success", "Data": connections})

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)


@pytest.mark.parametrize("task", TASKS)
def test_missing_connection_is_an_infrastructure_failure(task: str, monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load(task)
    _stub(monkeypatch, jira_is, [{"Id": "other", "Name": "someone-else"}])

    with pytest.raises(SystemExit) as exc:
        jira_is.require_connection()

    message = str(exc.value)
    assert "not an agent failure" in message
    assert jira_is.CONNECTION_NAME in message
    assert jira_is.FOLDER_PATH in message


@pytest.mark.parametrize("task", TASKS)
def test_connection_id_raises_for_teardown_to_swallow(task: str, monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load(task)
    _stub(monkeypatch, jira_is, [])

    with pytest.raises(Exception) as exc:
        jira_is.connection_id()

    assert not isinstance(exc.value, StopIteration)


@pytest.mark.parametrize("task", TASKS)
def test_present_connection_is_returned(task: str, monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load(task)
    _stub(monkeypatch, jira_is, [{"Id": "abc", "Name": jira_is.CONNECTION_NAME}])

    assert jira_is.require_connection() == "abc"
