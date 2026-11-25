"""rotate-auth.sh: a new login is recorded before it is handed out, or not handed out at all."""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / ".github/scripts/rotate-auth.sh"
ACCESS = "eyJaccess.token.value-0123456789abcdefghij"
REFRESH = "refresh-token-value-0123456789abcdefghij"


def _setup(tmp_path, mint_ok=True):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy(SCRIPT, scripts / "rotate-auth.sh")
    body = (
        f'printf "UIPATH_ACCESS_TOKEN={ACCESS}\\nUIPATH_REFRESH_TOKEN={REFRESH}\\nUIPATH_URL=https://x\\n" > "$AUTH_FILE"\n'
        if mint_ok
        else "exit 1\n"
    )
    (scripts / "refresh-auth.sh").write_text("#!/usr/bin/env bash\n" + body, encoding="utf-8")
    runner, home = tmp_path / "runner", tmp_path / "home"
    runner.mkdir()
    home.mkdir()
    env = {**os.environ, "RUNNER_TEMP": str(runner), "HOME": str(home), "ROTATE_QUIET": "1"}
    return scripts / "rotate-auth.sh", runner, home, env


def _run(script, env):
    return subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=30)


def test_tokens_are_recorded_then_installed(tmp_path):
    script, runner, home, env = _setup(tmp_path)
    assert _run(script, env).returncode == 0
    record = (runner / "issued-tokens").read_text(encoding="utf-8").split()
    assert ACCESS in record and REFRESH in record
    assert ACCESS in (home / ".uipath" / ".auth").read_text(encoding="utf-8")
    assert not (runner / "publication-disabled").exists() and not (runner / "auth.next").exists()


def test_recording_failure_hands_out_nothing_and_disables_publication(tmp_path):
    script, runner, home, env = _setup(tmp_path)
    (runner / "issued-tokens").mkdir()  # appending to a directory fails
    assert _run(script, env).returncode == 1
    assert (runner / "publication-disabled").exists()
    assert not (home / ".uipath" / ".auth").exists() and not (runner / "auth.next").exists()


def test_a_failed_mint_keeps_the_old_login_and_does_not_disable_publication(tmp_path):
    script, runner, home, env = _setup(tmp_path, mint_ok=False)
    (home / ".uipath").mkdir()
    (home / ".uipath" / ".auth").write_text("UIPATH_ACCESS_TOKEN=old\n", encoding="utf-8")
    assert _run(script, env).returncode == 1
    assert (home / ".uipath" / ".auth").read_text(encoding="utf-8") == "UIPATH_ACCESS_TOKEN=old\n"
    assert not (runner / "publication-disabled").exists()
