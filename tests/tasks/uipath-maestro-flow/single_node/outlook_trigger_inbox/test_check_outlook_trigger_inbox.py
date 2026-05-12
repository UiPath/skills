"""Tests for the Outlook trigger checker."""

from __future__ import annotations

import importlib.util
from pathlib import Path


CHECKER = Path(__file__).with_name("check_outlook_trigger_inbox.py")


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_outlook_trigger_inbox", CHECKER)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_check_folder_id_fresh_uses_resources_run_list(monkeypatch) -> None:
    checker = _load_checker()
    calls: list[list[str]] = []

    monkeypatch.setattr(checker, "_read_flow", lambda: ({}, "OutlookTriggerInbox.flow"))
    monkeypatch.setattr(
        checker,
        "_find_trigger_node",
        lambda _flow: {
            "inputs": {
                "detail": {
                    "eventParameters": {
                        "parentFolderId": "mail-folder-1",
                    }
                }
            }
        },
    )
    monkeypatch.setattr(
        checker,
        "_find_default_outlook_connection",
        lambda: ("connection-1", "folder-key-1", "connection-name"),
    )

    def fake_uip_json(args: list[str]) -> dict:
        calls.append(args)
        return {"Data": [{"id": "mail-folder-1"}]}

    monkeypatch.setattr(checker, "_uip_json", fake_uip_json)

    checker.check_folder_id_fresh()

    assert calls == [
        [
            "uip",
            "is",
            "resources",
            "run",
            "list",
            checker.CONNECTOR_KEY,
            "MailFolder",
            "--connection-id",
            "connection-1",
            "--output",
            "json",
        ]
    ]
