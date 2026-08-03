"""Contract guard for the session-env SessionStart step — BOTH twins
(``hooks/set-session-env.sh`` under bash, ``hooks/set-session-env.ps1`` under
pwsh). Every test is parametrized over the two implementations, enforcing the
twin keep-in-sync rule in CLAUDE.md.

Runs the hook as a subprocess with a SessionStart payload on stdin and asserts
what lands in ``CLAUDE_ENV_FILE``. Covers:

* the happy path — ``export UIPATH_SESSION_ID='<id>'`` appended;
* host wins — no-op when ``UIPATH_SESSION_ID`` is already set in the env;
* idempotence — no duplicate line when the file already exports it;
* sanitization — hostile ``session_id`` values are stripped to a safe charset
  before being written into the sourced env file;
* the skip paths — no ``CLAUDE_ENV_FILE``, or a payload without ``session_id``.

POSIX-only, like the send-telemetry guard — the hooks run under ``bash`` and
``pwsh`` (both preinstalled on GitHub ubuntu runners); CI runs it on ubuntu.

Run from repo root:
    pytest tests/scripts/test_set_session_env_hook.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"

TWINS = [
    pytest.param(["bash", str(HOOKS_DIR / "set-session-env.sh")], id="bash"),
    pytest.param(
        ["pwsh", "-NoProfile", "-File", str(HOOKS_DIR / "set-session-env.ps1")],
        id="pwsh",
    ),
]

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX-only guard (CI runs this on ubuntu)",
)

HOOK_ARGV = None


@pytest.fixture(autouse=True, params=TWINS)
def hook_argv(request):
    """Select the twin under test; skip if its interpreter is absent."""
    global HOOK_ARGV
    argv = request.param
    if shutil.which(argv[0]) is None:
        pytest.skip(f"{argv[0]} not available")
    HOOK_ARGV = argv

PAYLOAD = {
    "hook_event_name": "SessionStart",
    "session_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
    "source": "startup",
}


def test_writes_export_line():
    content = run_hook(PAYLOAD)
    assert (
        content
        == "export UIPATH_SESSION_ID='3f2504e0-4f89-41d3-9a0c-0305e82c3301'\n"
    )


def test_host_provided_session_id_wins():
    content = run_hook(PAYLOAD, extra_env={"UIPATH_SESSION_ID": "host-id"})
    assert content == ""


def test_no_duplicate_when_already_exported():
    preexisting = "export UIPATH_SESSION_ID='earlier-id'\n"
    content = run_hook(PAYLOAD, env_file_content=preexisting)
    assert content == preexisting


def test_appends_after_unrelated_lines():
    preexisting = "export OTHER_VAR='x'\n"
    content = run_hook(PAYLOAD, env_file_content=preexisting)
    assert content == (
        preexisting
        + "export UIPATH_SESSION_ID='3f2504e0-4f89-41d3-9a0c-0305e82c3301'\n"
    )


def test_repairs_missing_trailing_newline_before_appending():
    """A pre-existing file WITHOUT a final newline must not have the export
    concatenated onto its last line (that could break the sourced env file)."""
    preexisting = "export OTHER_VAR='x'"  # no trailing newline
    content = run_hook(PAYLOAD, env_file_content=preexisting)
    assert content == (
        "export OTHER_VAR='x'\n"
        "export UIPATH_SESSION_ID='3f2504e0-4f89-41d3-9a0c-0305e82c3301'\n"
    )


def test_sanitizes_hostile_session_id():
    """The env file is sourced by the agent, so a quote-breaking id must not
    survive: everything outside [A-Za-z0-9._-] is stripped."""
    content = run_hook({**PAYLOAD, "session_id": "x'; rm -rf $HOME; echo 'y"})
    assert content == "export UIPATH_SESSION_ID='xrm-rfHOMEechoy'\n"


def test_skips_without_env_file():
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ}
        env.pop("CLAUDE_ENV_FILE", None)
        env.pop("UIPATH_SESSION_ID", None)
        subprocess.run(
            HOOK_ARGV,
            input=json.dumps(PAYLOAD),
            text=True,
            env=env,
            cwd=tmp,
            timeout=15,
            check=True,
        )


def test_skips_payload_without_session_id():
    content = run_hook({"hook_event_name": "SessionStart", "source": "startup"})
    assert content == ""


# ── helpers ────────────────────────────────────────────────────────────────


def run_hook(payload, *, extra_env=None, env_file_content=None):
    """Invoke the hook with a temp CLAUDE_ENV_FILE; return the file's content
    afterwards ("" when the hook wrote nothing and the file did not pre-exist)."""
    with tempfile.TemporaryDirectory() as tmp:
        env_file = Path(tmp) / "claude-env"
        if env_file_content is not None:
            env_file.write_text(env_file_content)

        env = {**os.environ, "CLAUDE_ENV_FILE": str(env_file)}
        env.pop("UIPATH_SESSION_ID", None)
        if extra_env:
            env.update(extra_env)

        subprocess.run(
            HOOK_ARGV,
            input=json.dumps(payload),
            text=True,
            env=env,
            timeout=15,
            check=True,
        )

        return env_file.read_text() if env_file.exists() else ""
