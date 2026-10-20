"""Behavioral tests for the memory space pre_run preflight."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from unittest import mock

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "_setup" / "preflight_memory_space.py"
SPEC = importlib.util.spec_from_file_location("preflight_memory_space", SCRIPT)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)

SPACE = "UiPathAgentsSupportMemory"
FOLDER = "Shared/uipath-agents"
SELECTOR = f"{SPACE}={FOLDER}"
CURSOR = "eyJhdCI6InJlbW90ZSJ9"
NOT_READY = "TENANT NOT READY"


def _row(name: str, folder: str) -> dict:
    return {"Source": "Remote", "Key": "k", "Name": name, "Kind": "MemorySpace", "Folder": folder}


def _listing(rows: list[dict], next_page: str | None = None) -> mock.Mock:
    pagination = {"Returned": len(rows), "Limit": 50, "HasMore": next_page is not None}
    if next_page:
        pagination["NextPage"] = next_page

    payload = {"Result": "Success", "Code": "ResourceList", "Data": rows, "Pagination": pagination}
    return mock.Mock(returncode=0, stdout=json.dumps(payload), stderr="")


def _run(responses: list) -> tuple[int, mock.Mock]:
    with mock.patch.object(preflight.subprocess, "run", side_effect=responses) as run:
        return preflight.main([SELECTOR]), run


def test_found_in_named_folder():
    code, _ = _run([_listing([_row(SPACE, FOLDER)])])

    assert code == 0


def test_substring_match_does_not_count():
    code, _ = _run([_listing([_row(f"{SPACE}Old", FOLDER)])])

    assert code == 1


def test_other_folder_is_reported(capsys):
    code, _ = _run([_listing([_row(SPACE, "Shared/elsewhere")])])

    err = capsys.readouterr().err
    assert code == 1
    assert NOT_READY in err
    assert "found in: Shared/elsewhere" in err


def test_follows_next_page():
    code, run = _run([_listing([], next_page=CURSOR), _listing([_row(SPACE, FOLDER)])])

    assert code == 0
    assert run.call_args_list[1].args[0][-2:] == ["--next-page", CURSOR]


def test_repeated_next_page_stops(capsys):
    code, run = _run([_listing([], next_page=CURSOR)] * 3)

    assert code == 1
    assert run.call_count == 2
    assert "repeated NextPage" in capsys.readouterr().err


def test_cli_failure_is_not_ready(capsys):
    failure = {"Result": "Failure", "Message": "Failed to authenticate", "Instructions": "token expired"}
    code, _ = _run([mock.Mock(returncode=1, stdout=json.dumps(failure), stderr="")])

    assert code == 1
    assert "Failed to authenticate: token expired" in capsys.readouterr().err


def test_non_json_is_not_ready(capsys):
    code, _ = _run([mock.Mock(returncode=127, stdout="", stderr="uip: not found")])

    assert code == 1
    assert "uip: not found" in capsys.readouterr().err


def test_timeout_is_not_ready(capsys):
    code, _ = _run([subprocess.TimeoutExpired(cmd="uip", timeout=preflight.LIST_TIMEOUT_S)])

    assert code == 1
    assert "did not answer" in capsys.readouterr().err


@pytest.mark.parametrize("selector", [SPACE, f"{SPACE}=", f"={FOLDER}"])
def test_bad_selector_is_rejected(selector):
    with mock.patch.object(preflight.subprocess, "run") as run:
        assert preflight.main([selector]) == 1

    run.assert_not_called()
