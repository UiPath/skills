"""seed-uipath-auth.sh: each smoke container gets a private copy of the login, never the host's own."""

from __future__ import annotations

import os
import pathlib
import stat
import subprocess

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "tests/docker/seed-uipath-auth.sh"
LOGIN = "UIPATH_ACCESS_TOKEN=not-a-real-token\nUIPATH_URL=https://x\n"


def _host(tmp_path):
    src = tmp_path / "host" / ".uipath"
    src.mkdir(parents=True)
    (src / ".auth").write_text(LOGIN, encoding="utf-8")
    (src / "config.json").write_text("{}", encoding="utf-8")
    src.chmod(0o755)
    return src


def _run(*args):
    return subprocess.run(["sh", str(SCRIPT), *map(str, args)], capture_output=True, text=True, timeout=30)


def _mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_copies_the_login_owner_only(tmp_path):
    src, dst = _host(tmp_path), tmp_path / "container" / ".uipath"
    assert _run(src, dst).returncode == 0
    assert (dst / ".auth").read_text(encoding="utf-8") == LOGIN
    assert (dst / "config.json").exists()
    assert _mode(dst) == 0o700 and _mode(dst / ".auth") & 0o077 == 0


def test_changing_the_copy_leaves_the_host_login_alone(tmp_path):
    # What the CLI does on a credentials save: tighten the directory and rewrite .auth.
    src, dst = _host(tmp_path), tmp_path / "container" / ".uipath"
    assert _run(src, dst).returncode == 0
    (dst / ".auth").write_text("UIPATH_ACCESS_TOKEN=rotated\n", encoding="utf-8")
    dst.chmod(0o700)
    assert _mode(src) == 0o755
    assert (src / ".auth").read_text(encoding="utf-8") == LOGIN


def test_a_missing_login_fails_and_creates_nothing(tmp_path):
    src, dst = tmp_path / "empty", tmp_path / "container" / ".uipath"
    src.mkdir()
    result = _run(src, dst)
    assert result.returncode == 1 and "no login" in result.stderr
    assert not dst.exists()


def test_an_existing_destination_is_not_overwritten(tmp_path):
    src, dst = _host(tmp_path), tmp_path / "container" / ".uipath"
    dst.mkdir(parents=True)
    (dst / ".auth").write_text("UIPATH_ACCESS_TOKEN=other\n", encoding="utf-8")
    assert _run(src, dst).returncode == 1
    assert (dst / ".auth").read_text(encoding="utf-8") == "UIPATH_ACCESS_TOKEN=other\n"


def test_the_script_is_executable_in_git():
    # The image installs it with COPY --chmod=0755; the bit here keeps a local run working too.
    assert os.access(SCRIPT, os.X_OK)
