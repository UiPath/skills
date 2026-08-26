from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


HERE = Path(__file__).parent


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("jira_create_issue_is", HERE / "jira_is.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Result:
    def __init__(self, envelope: object, returncode: int = 0) -> None:
        self.stdout = json.dumps(envelope)
        self.stderr = ""
        self.returncode = returncode


def test_connection_id_retries_transient_folder_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    responses = iter([
        Result({"Result": "Failure", "ErrorCode": "server_error", "Retry": "RetryLater"}),
        Result({"Result": "Success", "Data": {"Key": "folder-key"}}),
        Result({"Result": "Success", "Data": [{"Id": "connection-id", "Name": jira_is.CONNECTION_NAME}]}),
    ])
    monkeypatch.setattr(jira_is.subprocess, "run", lambda *args, **kwargs: next(responses))

    assert jira_is.connection_id() == "connection-id"


def test_missing_data_reports_redacted_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    envelope = json.loads((HERE / "fixtures" / "folder_get_missing_data.json").read_text())
    envelope["AccessToken"] = "must-not-appear"
    monkeypatch.setattr(jira_is.subprocess, "run", lambda *args, **kwargs: Result(envelope))

    with pytest.raises(RuntimeError) as exc_info:
        jira_is.connection_id()

    message = str(exc_info.value)
    assert '"Result": "Failure"' in message
    assert "Data" not in message
    assert "must-not-appear" not in message


def test_invalid_json_does_not_echo_cli_output(monkeypatch: pytest.MonkeyPatch) -> None:
    jira_is = _load_module()
    result = Result({})
    result.stdout = "not-json access_token=must-not-appear"
    result.stderr = "must-not-appear"
    result.returncode = 1
    monkeypatch.setattr(jira_is.subprocess, "run", lambda *args, **kwargs: result)

    with pytest.raises(RuntimeError) as exc_info:
        jira_is.connection_id()

    message = str(exc_info.value)
    assert "invalid JSON" in message
    assert "exit 1" in message
    assert "must-not-appear" not in message
