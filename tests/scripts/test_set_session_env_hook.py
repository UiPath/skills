"""Contract guard for the session-env SessionStart step
(``hooks/set-session-env.mjs`` under node).

Runs the hook as a subprocess with a SessionStart payload on stdin and asserts
what lands in ``CLAUDE_ENV_FILE``. Covers:

* the happy path — ``export UIPATH_SESSION_ID='<id>'`` appended, followed by
  the agent-session context (``UIPATH_AGENT_MODEL``, ``UIPATH_PERMISSION_MODE``,
  ``UIPATH_EFFORT_LEVEL``, ``UIPATH_SKILLS_VERSION``) the CLI stamps on every
  command request;
* host wins — no session-id export when ``UIPATH_SESSION_ID`` is already set;
* idempotence — no duplicate line when the file already exports the value, and
  a re-export when a later SessionStart carries a changed value;
* sanitization — hostile values are stripped to a safe charset before being
  written into the sourced env file;
* the skip paths — no ``CLAUDE_ENV_FILE``, malformed JSON, or a payload without
  ``session_id``.

POSIX-only, like the telemetry wrapper guard; CI runs it on ubuntu (``node``
is preinstalled on the runners).

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

HOOK_ARGV = ["node", str(HOOKS_DIR / "set-session-env.mjs")]

SKILLS_VERSION = json.loads((REPO_ROOT / "version-manifest.json").read_text())[
    "skillsVersion"
]
SESSION_LINE = "export UIPATH_SESSION_ID='3f2504e0-4f89-41d3-9a0c-0305e82c3301'\n"
SKILLS_VERSION_LINE = f"export UIPATH_SKILLS_VERSION='{SKILLS_VERSION}'\n"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="POSIX-only guard (CI runs this on ubuntu)",
)


@pytest.fixture(autouse=True)
def require_node():
    """Skip the suite if node is absent."""
    if shutil.which("node") is None:
        pytest.skip("node not available")

PAYLOAD = {
    "hook_event_name": "SessionStart",
    "session_id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
    "source": "startup",
}

FULL_PAYLOAD = {
    **PAYLOAD,
    "model": "claude-sonnet-5",
    "permission_mode": "acceptEdits",
    "effort": {"level": "high"},
}


def test_writes_export_line():
    content = run_hook(PAYLOAD)
    assert content == SESSION_LINE + SKILLS_VERSION_LINE


def test_exports_agent_session_context():
    content = run_hook(FULL_PAYLOAD)
    assert content == (
        SESSION_LINE
        + "export UIPATH_AGENT_MODEL='claude-sonnet-5'\n"
        + "export UIPATH_PERMISSION_MODE='acceptEdits'\n"
        + "export UIPATH_EFFORT_LEVEL='high'\n"
        + SKILLS_VERSION_LINE
    )


def test_object_shaped_model_uses_id_then_display_name():
    by_id = run_hook(
        {**PAYLOAD, "model": {"id": "claude-opus-5-5", "display_name": "Opus"}}
    )
    assert "export UIPATH_AGENT_MODEL='claude-opus-5-5'\n" in by_id

    by_name = run_hook({**PAYLOAD, "model": {"display_name": "Opus 5.5"}})
    assert "export UIPATH_AGENT_MODEL='Opus 5.5'\n" in by_name


def test_host_provided_session_id_wins():
    content = run_hook(PAYLOAD, extra_env={"UIPATH_SESSION_ID": "host-id"})
    assert content == SKILLS_VERSION_LINE


def test_no_duplicate_when_already_exported():
    preexisting = "export UIPATH_SESSION_ID='earlier-id'\n" + SKILLS_VERSION_LINE
    content = run_hook(PAYLOAD, env_file_content=preexisting)
    assert content == preexisting


def test_reexports_a_changed_context_value():
    """SessionStart re-fires on resume/clear/compact; a changed value is
    appended so the last export wins when the file is sourced."""
    first = run_hook(FULL_PAYLOAD)
    content = run_hook(
        {**FULL_PAYLOAD, "model": "claude-opus-5-5"}, env_file_content=first
    )
    assert content == first + "export UIPATH_AGENT_MODEL='claude-opus-5-5'\n"


def test_appends_after_unrelated_lines():
    preexisting = "export OTHER_VAR='x'\n"
    content = run_hook(PAYLOAD, env_file_content=preexisting)
    assert content == preexisting + SESSION_LINE + SKILLS_VERSION_LINE


def test_repairs_missing_trailing_newline_before_appending():
    """A pre-existing file WITHOUT a final newline must not have the export
    concatenated onto its last line (that could break the sourced env file)."""
    preexisting = "export OTHER_VAR='x'"  # no trailing newline
    content = run_hook(PAYLOAD, env_file_content=preexisting)
    assert content == (
        "export OTHER_VAR='x'\n" + SESSION_LINE + SKILLS_VERSION_LINE
    )


def test_sanitizes_hostile_session_id():
    """The env file is sourced by the agent, so a quote-breaking id must not
    survive: everything outside [A-Za-z0-9._-] is stripped."""
    content = run_hook({**PAYLOAD, "session_id": "x'; rm -rf $HOME; echo 'y"})
    assert content == "export UIPATH_SESSION_ID='xrm-rfHOMEechoy'\n" + SKILLS_VERSION_LINE


def test_sanitizes_hostile_context_values():
    """Context values keep a readable charset but lose every quote, `$` and
    shell metacharacter, and are capped at 120 chars."""
    content = run_hook(
        {
            **PAYLOAD,
            "model": "m'; rm -rf $HOME; echo 'x",
            "permission_mode": "p" * 300,
        }
    )
    assert "export UIPATH_AGENT_MODEL='m__ rm -rf _HOME_ echo _x'\n" in content
    assert f"export UIPATH_PERMISSION_MODE='{'p' * 120}'\n" in content


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


def test_skips_malformed_payload():
    content = run_hook(raw_input="{not json")
    assert content == ""


def test_skips_session_id_when_payload_has_none():
    content = run_hook({"hook_event_name": "SessionStart", "source": "startup"})
    assert content == SKILLS_VERSION_LINE


# ── helpers ────────────────────────────────────────────────────────────────


def run_hook(payload=None, *, extra_env=None, env_file_content=None, raw_input=None):
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
            input=raw_input if raw_input is not None else json.dumps(payload),
            text=True,
            env=env,
            timeout=15,
            check=True,
        )

        return env_file.read_text() if env_file.exists() else ""
