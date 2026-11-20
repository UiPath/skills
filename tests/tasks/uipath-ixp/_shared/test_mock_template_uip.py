"""Unit tests for mock_template/mocks/uip. Run with ``pytest`` from any directory.

What these pin: the mock answers like the real CLI's pre-auth stage. A broken
JSON option file gets the real local error, everything else the auth error,
and every call is still logged with a readable payload inlined after its path.
"""

import pathlib
import shutil
import subprocess
import sys

import pytest

MOCKS = pathlib.Path(__file__).resolve().parent / "mock_template" / "mocks"
AUTH = "not connected to a tenant"


@pytest.fixture
def mock(tmp_path):
    shutil.copytree(MOCKS, tmp_path / "mocks")

    def run(*args):
        res = subprocess.run(
            [sys.executable, str(tmp_path / "mocks" / "uip"), *args],
            capture_output=True, text=True, cwd=tmp_path, stdin=subprocess.DEVNULL,
        )
        log = (tmp_path / "mocks" / "calls.log").read_text(encoding="utf-8")
        return res, log

    run.dir = tmp_path
    return run


def test_missing_json_file_gets_the_real_file_not_found_error(mock):
    res, log = mock("ixp", "groups", "update-prompts", "p-ixp", "--updates-file", "missing.json")
    assert res.returncode == 1
    assert "File not found: " in res.stderr and str(mock.dir / "missing.json") in res.stderr
    assert AUTH not in res.stderr
    assert "uip ixp groups update-prompts p-ixp --updates-file missing.json" in log


def test_empty_json_file_is_rejected_locally(mock):
    (mock.dir / "empty.json").write_text("  \n", encoding="utf-8")
    res, _ = mock("ixp", "groups", "add", "p-ixp", "--fields-file", "empty.json")
    assert "Expected JSON in empty.json but the file is empty." in res.stderr


def test_unparseable_json_file_is_rejected_locally(mock):
    (mock.dir / "bad.json").write_text("[{name: 1}]", encoding="utf-8")
    res, _ = mock("ixp", "data-types", "add", "p-ixp", "--choices-file", "bad.json")
    assert "--choices-file bad.json is not valid JSON" in res.stderr


def test_valid_json_file_gets_auth_error_and_is_inlined_in_the_log(mock):
    (mock.dir / "u.json").write_text('[{"name": "Invoice Header"}]', encoding="utf-8")
    res, log = mock("ixp", "groups", "update-prompts", "p-ixp", "--updates-file", "u.json")
    assert res.returncode == 1 and AUTH in res.stderr
    assert '--updates-file u.json [{"name": "Invoice Header"}]' in log


def test_utf16le_json_file_is_accepted_like_the_real_cli(mock):
    (mock.dir / "w.json").write_bytes(b"\xff\xfe" + '[{"occurrence": 0}]'.encode("utf-16-le"))
    res, _ = mock("ixp", "labellings", "confirm", "p-ixp", "d", "--updates-file", "w.json")
    assert AUTH in res.stderr


@pytest.mark.parametrize("args", [
    ("ixp", "projects", "list"),
    ("ixp", "projects", "get-metrics", "p-ixp", "--output-file", "missing-out.json"),
])
def test_calls_without_a_json_input_file_get_the_auth_error(mock, args):
    res, _ = mock(*args)
    assert res.returncode == 1 and AUTH in res.stderr
