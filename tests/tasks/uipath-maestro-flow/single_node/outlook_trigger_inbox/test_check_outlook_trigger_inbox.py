"""Tests for the Outlook trigger checker.

Exercises the verb-tolerant `_uip_resources_run` helper that backs
``check_folder_id_fresh`` so the checker keeps working across both the
post-rename CLI (``uip is resources run``) and any sandbox that still
ships the legacy CLI (``uip is resources execute``). See MST-9674.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).with_name("check_outlook_trigger_inbox.py")


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_outlook_trigger_inbox", CHECKER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _patch_static(monkeypatch, checker, folder_id: str = "mail-folder-1") -> None:
    """Stub the non-CLI dependencies so we can focus on the verb path."""
    monkeypatch.setattr(checker, "_read_flow", lambda: ({}, "OutlookTriggerInbox.flow"))
    monkeypatch.setattr(
        checker,
        "_find_trigger_node",
        lambda _flow: {
            "inputs": {"detail": {"eventParameters": {"parentFolderId": folder_id}}}
        },
    )
    monkeypatch.setattr(
        checker,
        "_find_default_outlook_connection",
        lambda: ("connection-1", "folder-key-1", "connection-name"),
    )


def _fake_proc(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


def _success_payload(folder_id: str = "mail-folder-1") -> str:
    return json.dumps({"Data": [{"id": folder_id}]})


def test_uses_run_verb_when_cli_supports_it(monkeypatch) -> None:
    """Happy path: post-rename CLI accepts `run`; no fallback issued."""
    checker = _load_checker()
    _patch_static(monkeypatch, checker)
    calls: list[list[str]] = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        return _fake_proc(0, stdout=_success_payload())

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    checker.check_folder_id_fresh()

    assert len(calls) == 1, calls
    assert calls[0][:5] == ["uip", "is", "resources", "run", "list"]


def test_falls_back_to_execute_on_unknown_command_run(monkeypatch) -> None:
    """Legacy CLI: rejects `run` with 'unknown command' — retry with `execute`."""
    checker = _load_checker()
    _patch_static(monkeypatch, checker)
    calls: list[list[str]] = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        if args[3] == "run":
            return _fake_proc(
                1,
                stdout=json.dumps(
                    {"Result": "ValidationError", "Message": "error: unknown command 'run'"}
                ),
            )
        return _fake_proc(0, stdout=_success_payload())

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    checker.check_folder_id_fresh()

    assert len(calls) == 2, calls
    assert calls[0][:5] == ["uip", "is", "resources", "run", "list"]
    assert calls[1][:5] == ["uip", "is", "resources", "execute", "list"]


def test_does_not_fall_back_on_unrelated_failure(monkeypatch) -> None:
    """A genuine CLI error (auth, network) must not be retried — fail fast."""
    checker = _load_checker()
    _patch_static(monkeypatch, checker)
    calls: list[list[str]] = []

    def fake_run(args, **_kwargs):
        calls.append(args)
        return _fake_proc(1, stdout="", stderr="403 Forbidden")

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    try:
        checker.check_folder_id_fresh()
    except SystemExit:
        pass
    else:
        raise AssertionError("expected SystemExit on a 403")

    assert len(calls) == 1, calls
    assert calls[0][3] == "run"


def test_folder_id_mismatch_fails_with_pr348_signature(monkeypatch) -> None:
    """If the flow's parentFolderId is not in the live ID set, the checker
    fails with the PR #348 regression marker (independent of the verb)."""
    checker = _load_checker()
    _patch_static(monkeypatch, checker, folder_id="stale-id-from-old-connection")

    def fake_run(_args, **_kwargs):
        return _fake_proc(0, stdout=_success_payload(folder_id="fresh-id"))

    monkeypatch.setattr(checker.subprocess, "run", fake_run)
    try:
        checker.check_folder_id_fresh()
    except SystemExit as exc:
        message: Any = exc.code
        assert "PR #348 regression" in str(message)
    else:
        raise AssertionError("expected SystemExit on a stale folder id")
