"""
Behaviour tests for the e2e_adopt_validate task fixtures: the stand-in `gh` and
the checker that reads its call log.

The task grades `uip extension init` by files on disk, so a run whose `init`
used the host `gh` would pass unless the stand-in leaves evidence. These tests
build a throwaway sandbox, drive the real stand-in and the real checker as
subprocesses, and cover both sides:

  - the stand-in resolves first on PATH, answers and logs the two index reads,
    and denies and logs everything else
  - the checker passes when the stand-in served `init`, and fails when `init`
    ran with the host PATH (no log), when only one index read was logged, and
    when only denied calls were logged

`uip` is replaced by a small fake that counts words, so the tests need no CLI.

Run from repo root:
    pytest tests/scripts/test_e2e_adopt_validate_stand_in.py
"""

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_DIR = REPO_ROOT / "tests" / "tasks" / "uipath-extension" / "e2e_adopt_validate"
CHECKER = TASK_DIR / "check_adopt_validate.py"
STAND_IN = TASK_DIR / "_setup" / "gh"

INDEX = "repos/UiPath/uipath-extensions"
POLICY = f"{INDEX}/contents/policy/gate-library.yaml"
LOG_NAME = "gh-calls.log"

FAKE_UIP = """#!/usr/bin/env python3
import json
import sys

args = sys.argv[1:]
payload = json.loads(args[args.index("--input") + 1])
result = {"status": "Successful", "outputArguments": {"words": len(payload["text"].split())}}
print("JobResult=" + json.dumps(result))
"""

FAKE_HOST_GH = """#!/bin/sh
echo '{"default_branch":"main"}'
"""

TEMPLATE = {
    "schema": 2,
    "license": "MIT",
    "display": {"label": "Word Count", "description": "Counts words.", "icon": "assets/icon.png"},
    "tags": ["text"],
}


def _write_executable(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


@pytest.fixture
def sandbox(tmp_path):
    root = tmp_path / "sandbox"
    setup = root / "_setup"
    setup.mkdir(parents=True)
    shutil.copy2(STAND_IN, setup / "gh")
    _write_executable(root / "bin" / "uip", FAKE_UIP)
    _write_executable(root / "host-bin" / "gh", FAKE_HOST_GH)

    project = root / "word-count"
    (project / "assets").mkdir(parents=True)
    (project / "assets" / "icon.png").write_bytes(b"png")
    (project / "uipath.json").write_text(json.dumps({"functions": {"count": {}}}), encoding="utf-8")
    (project / "package.json").write_text(
        json.dumps({"name": "uipath-extensions.acme.word-count"}), encoding="utf-8"
    )
    (project / "uipath-extensions.json").write_text(json.dumps(TEMPLATE), encoding="utf-8")
    return root


def _path(*dirs: Path) -> str:
    return os.pathsep.join([*(str(d) for d in dirs), os.environ["PATH"]])


def _stand_in(sandbox: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(sandbox / "_setup" / "gh"), *args], capture_output=True, text=True, check=False
    )


def _log_lines(sandbox: Path) -> list[str]:
    log = sandbox / "_setup" / LOG_NAME
    return log.read_text(encoding="utf-8").splitlines() if log.is_file() else []


def _run_checker(sandbox: Path, cwd: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "PATH": _path(sandbox / "bin")}
    return subprocess.run(
        [sys.executable, "-I", str(CHECKER)],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _command_v_gh(path: str) -> str:
    result = subprocess.run(
        ["sh", "-c", "command -v gh"],
        env={**os.environ, "PATH": path},
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def test_probe_stand_in_wins_only_with_the_setup_prefix(sandbox):
    with_prefix = _command_v_gh(_path(sandbox / "_setup", sandbox / "host-bin"))
    host_only = _command_v_gh(_path(sandbox / "host-bin"))

    assert with_prefix == str(sandbox / "_setup" / "gh")
    assert host_only == str(sandbox / "host-bin" / "gh")


def test_stand_in_answers_and_logs_the_index_reads(sandbox):
    index = _stand_in(sandbox, "api", "-X", "GET", INDEX)
    policy = _stand_in(sandbox, "api", "-X", "GET", POLICY, "--jq", ".content")
    auth = _stand_in(sandbox, "auth", "status")

    assert index.returncode == 0 and "default_branch" in index.stdout
    assert policy.returncode == 0 and "template_schema: 2" in policy.stdout
    assert auth.returncode == 0
    assert _log_lines(sandbox) == [
        f"OK GET {INDEX}",
        f"OK GET {POLICY}",
        "OK auth status",
    ]


def test_stand_in_denies_and_logs_everything_else(sandbox):
    write = _stand_in(sandbox, "api", "-X", "POST", f"{INDEX}/pulls")
    pr = _stand_in(sandbox, "pr", "create", "--title", "x")

    assert write.returncode == 1 and pr.returncode == 1
    lines = _log_lines(sandbox)
    assert lines == [f"DENIED api -X POST {INDEX}/pulls", "DENIED pr create --title x"]


@pytest.mark.parametrize("cwd_is_project", [True, False], ids=["cwd-project", "cwd-sandbox-root"])
def test_checker_passes_when_the_stand_in_served_init(sandbox, cwd_is_project):
    _stand_in(sandbox, "api", "-X", "GET", INDEX)
    _stand_in(sandbox, "api", "-X", "GET", POLICY)

    result = _run_checker(sandbox, sandbox / "word-count" if cwd_is_project else sandbox)

    assert result.returncode == 0, result.stderr
    assert "PASS" in result.stdout


def test_checker_fails_when_init_ran_with_the_host_path(sandbox):
    subprocess.run(
        [str(sandbox / "host-bin" / "gh"), "api", "-X", "GET", INDEX],
        capture_output=True,
        check=True,
    )
    assert _log_lines(sandbox) == []

    result = _run_checker(sandbox, sandbox / "word-count")

    assert result.returncode != 0
    assert "gh-calls.log does not exist" in result.stderr


def test_checker_fails_when_only_the_index_lookup_was_logged(sandbox):
    _stand_in(sandbox, "api", "-X", "GET", INDEX)

    result = _run_checker(sandbox, sandbox / "word-count")

    assert result.returncode != 0
    assert POLICY in result.stderr


def test_checker_fails_when_only_denied_calls_were_logged(sandbox):
    _stand_in(sandbox, "pr", "create")
    _stand_in(sandbox, "api", "-X", "POST", INDEX)

    result = _run_checker(sandbox, sandbox / "word-count")

    assert result.returncode != 0
    assert "lacks the index reads" in result.stderr
