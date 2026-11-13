"""check_extraction_check.py and the uip shim it reads the log of."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_extraction_check as cec  # noqa: E402

_SHIM = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "_setup",
    "extraction_check_shim",
    ".uip-fake",
    "uip",
)

CHECK = "uip maestro flow extraction check --output json"
CREATE = (
    "uip maestro flow nodes create PermitReader/PermitReader/PermitReader.flow "
    "uipath.ixp.extract-document-builder --label Extract permit --output json"
)
INIT = "uip maestro flow init PermitReader --output json"
SEARCH = "uip maestro flow registry search uipath.ixp -f type:startsWith=uipath.ixp --output json"


@pytest.mark.parametrize(
    ("check", "lines", "ok"),
    [
        ("ran", [INIT, CHECK], True),
        ("ran", [INIT], False),
        ("ran", [], False),
        ("before-node", [CHECK, INIT, CREATE], True),
        ("before-node", [INIT, CREATE, CHECK], False),
        ("before-node", [INIT, CREATE], False),
        ("before-node", [CHECK, INIT], False),
        ("before-node", [CHECK, "uip maestro flow nodes add f.flow uipath.ixp.extract-document-builder"], True),
        ("before-node", [CHECK, "uip maestro flow nodes create f.flow core.action.script"], False),
        ("searched-ixp", [CHECK, SEARCH], True),
        ("searched-ixp", ["uip maestro flow registry list --output json --filter ixp"], True),
        ("searched-ixp", ["uip maestro flow registry search slack"], False),
    ],
)
def test_run(check: str, lines: list[str], ok: bool) -> None:
    assert cec.run(check, lines)[0] is ok


def test_missing_log_fails(tmp_path, capsys) -> None:
    assert cec.main(["--log", str(tmp_path / "absent"), "ran"]) == 1
    assert "FAIL" in capsys.readouterr().err


def test_main_reads_log(tmp_path, capsys) -> None:
    log = tmp_path / ".uip-cmdlog"
    log.write_text(f"{CHECK}\n{INIT}\n{CREATE}\n", encoding="utf-8")
    assert cec.main(["--log", str(log), "before-node"]) == 0
    assert capsys.readouterr().out.startswith("OK:")


_SH = shutil.which("sh")


@pytest.fixture
def sandbox(tmp_path):
    """A sandbox holding the shim, and a fake real `uip` later on PATH."""
    fake = tmp_path / ".uip-fake"
    fake.mkdir()
    shim = fake / "uip"
    shutil.copyfile(_SHIM, shim)
    real_dir = tmp_path / "real-bin"
    real_dir.mkdir()
    real = real_dir / "uip"
    real.write_text('#!/bin/sh\necho "REAL $*"\n', encoding="utf-8")
    for path in (shim, real):
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    env = dict(os.environ, PATH=f"{fake}{os.pathsep}{real_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return tmp_path, env


def _shim(sandbox, *args: str) -> subprocess.CompletedProcess[str]:
    root, env = sandbox
    return subprocess.run(
        [_SH, str(root / ".uip-fake" / "uip"), *args],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.skipif(_SH is None, reason="needs a POSIX sh")
@pytest.mark.parametrize(
    ("status", "available"),
    [
        (None, True),
        ("Available", True),
        ("FeatureDisabled", False),
        ("ServiceUnavailable", False),
        ("ModelUnavailable", False),
        ("Unknown", False),
    ],
)
def test_shim_answers_check(sandbox, status: str | None, available: bool) -> None:
    root, _ = sandbox
    if status is not None:
        (root / ".uip-fake" / "extraction-status").write_text(f"{status}\n", encoding="utf-8")
    result = _shim(sandbox, "maestro", "flow", "extraction", "check", "--output", "json")
    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["Result"] == "Success"
    assert envelope["Code"] == "ExtractionCheckSuccess"
    assert envelope["Data"]["Status"] == (status or "Available")
    assert envelope["Data"]["Available"] is available
    assert envelope["Data"]["Reason"]
    assert ("do not add" in envelope["Instructions"]) is not available


@pytest.mark.skipif(_SH is None, reason="needs a POSIX sh")
@pytest.mark.parametrize("args", [["-t", "Other"], ["--tenant", "Other"], ["--tenant=Other"]])
def test_shim_reports_named_tenant(sandbox, args: list[str]) -> None:
    result = _shim(sandbox, "maestro", "flow", "extraction", "check", *args)
    assert json.loads(result.stdout)["Data"]["Tenant"] == "Other"


@pytest.mark.skipif(_SH is None, reason="needs a POSIX sh")
def test_shim_rejects_unknown_status(sandbox) -> None:
    root, _ = sandbox
    (root / ".uip-fake" / "extraction-status").write_text("Maybe", encoding="utf-8")
    assert _shim(sandbox, "maestro", "flow", "extraction", "check").returncode == 127


@pytest.mark.skipif(_SH is None, reason="needs a POSIX sh")
def test_shim_passes_other_calls_through_and_logs_all(sandbox) -> None:
    root, _ = sandbox
    passed = _shim(sandbox, "maestro", "flow", "validate", "f.flow")
    assert passed.stdout.strip() == "REAL maestro flow validate f.flow"
    _shim(sandbox, "maestro", "flow", "extraction", "check")
    log = (root / ".uip-cmdlog").read_text(encoding="utf-8").splitlines()
    assert log == ["uip maestro flow validate f.flow", "uip maestro flow extraction check"]
