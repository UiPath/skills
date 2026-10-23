"""Every flow `jira_is.py` copy retries a 5xx on its setup reads."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

FLOW_TASKS = Path(__file__).resolve().parent.parent
COPIES = sorted(FLOW_TASKS.rglob("jira_is.py"))
BAD_GATEWAY = {"Result": "Failure", "ErrorCode": "unknown_error", "Message": "502 Bad Gateway", "Retry": "RetryWillNotFix"}


def _load(path: Path) -> ModuleType:
    name = "jira_is_" + "_".join(path.relative_to(FLOW_TASKS).parts[:-1])
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, envelope: object) -> None:
        self.stdout = json.dumps(envelope)
        self.stderr = ""
        self.returncode = 0


def _record_sleeps(monkeypatch: pytest.MonkeyPatch, jira_is: ModuleType) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(jira_is.time, "sleep", sleeps.append)
    return sleeps


def test_every_copy_is_covered() -> None:
    assert len(COPIES) == 6


@pytest.mark.parametrize("path", COPIES, ids=lambda p: p.relative_to(FLOW_TASKS).as_posix())
def test_connection_id_retries_a_5xx_envelope(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    jira_is = _load(path)
    seen: list[str] = []
    connection = {"Id": "connection-id", "Name": jira_is.CONNECTION_NAME, "Folder": "uipath-maestro-flow"}

    def fake_run(cmd, **kwargs):
        operation = " ".join(cmd[1:4])
        seen.append(operation)
        if seen.count(operation) == 1:
            return Result(BAD_GATEWAY)
        if operation == "or folders get":
            return Result({"Result": "Success", "Data": {"Key": "folder-key"}})
        return Result({"Result": "Success", "Data": [connection]})

    monkeypatch.setattr(jira_is.subprocess, "run", fake_run)
    sleeps = _record_sleeps(monkeypatch, jira_is)

    assert jira_is.connection_id() == "connection-id"
    assert all(seen.count(operation) == 2 for operation in seen)
    assert sleeps == [jira_is._RETRY_DELAY_SECONDS] * len(set(seen))


@pytest.mark.parametrize(
    "path",
    [path for path in COPIES if "def myself(" in path.read_text()],
    ids=lambda p: p.relative_to(FLOW_TASKS).as_posix(),
)
def test_myself_retries_a_5xx_envelope(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    jira_is = _load(path)
    responses = iter([BAD_GATEWAY, {"Result": "Success", "Data": {"accountId": "acc-1"}}])
    monkeypatch.setattr(jira_is.subprocess, "run", lambda *args, **kwargs: Result(next(responses)))
    sleeps = _record_sleeps(monkeypatch, jira_is)

    assert jira_is.myself("conn") == "acc-1"
    assert sleeps == [jira_is._RETRY_DELAY_SECONDS]
