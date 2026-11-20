"""Guard the auth retry and error detail in the connections preflight."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1] / "tasks"
SCRIPTS = [ROOT / "uipath-maestro-bpmn" / "_setup" / "preflight_connections.py",
           ROOT / "uipath-maestro-flow" / "_setup" / "preflight_connections.py"]


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(f"pf_{path.parts[-3]}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _proc(code: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], code, stdout, stderr)


OK = _proc(0, json.dumps({"Result": "Success", "Data": [{"Id": "1"}]}))
AUTH = _proc(2, json.dumps({"Result": "Failure", "Message": "Token expired", "Instructions": "Run uip login"}))
VALIDATION = _proc(3, json.dumps({"Result": "Failure", "Message": "bad key"}))


@pytest.fixture(params=SCRIPTS, ids=lambda p: p.parts[-3])
def pf(request, monkeypatch):
    mod = _load(request.param)
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    return mod


def _script(monkeypatch, pf, results):
    calls = []

    def run(*_a, **_k):
        calls.append(1)
        return results[min(len(calls), len(results)) - 1]

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def test_auth_then_success_retries(pf, monkeypatch):
    calls = _script(monkeypatch, pf, [AUTH, AUTH, OK])
    assert pf._connections("k") == [{"Id": "1"}]
    assert len(calls) == 3


def test_persistent_auth_fails_with_stdout_message(pf, monkeypatch):
    calls = _script(monkeypatch, pf, [AUTH])
    with pytest.raises(RuntimeError) as exc:
        pf._connections("k")
    assert len(calls) == 3
    msg = str(exc.value)
    assert "exited 2" in msg and "Token expired" in msg and "Run uip login" in msg


def test_validation_error_not_retried(pf, monkeypatch):
    calls = _script(monkeypatch, pf, [VALIDATION, OK])
    with pytest.raises(RuntimeError, match="exited 3.*bad key"):
        pf._connections("k")
    assert len(calls) == 1
