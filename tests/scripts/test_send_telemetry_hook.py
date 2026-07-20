"""Contract guard for the skills telemetry hook — BOTH twins
(``hooks/send-telemetry.sh`` under bash, ``hooks/send-telemetry.ps1`` under
pwsh). Every test is parametrized over the two implementations, so this suite
is the executable form of the twin keep-in-sync rule in CLAUDE.md: a
behavioral change to one twin without the equivalent change to the other
fails here.

Runs the hook as a subprocess with a stubbed ``uip`` on ``PATH``, pipes a Claude
Code hook payload on stdin, and asserts the single flat JSON object the hook
forwards to ``uip track``. Covers:

* the ``eventName`` mapping — ``PostToolUse``→``tool-use``,
  ``SessionStart``→``session-start``, ``SessionEnd``→``session-end``,
  ``Stop``/``StopFailure``→``completion``;
* the lifecycle fields ``session_source`` / ``reason`` / ``outcome`` and
  ``schemaVersion``;
* the v2 key set — canonical ``session_id`` (not the v1 ``sessionId``) and no
  ``environment`` / ``baseUrl`` (the CLI stamps its own base dimensions);
* Codex-shaped payloads — Codex fires ``SessionStart``/``Stop`` under the same
  names with a matching envelope, so mapping and fields work unchanged and
  Codex-only extras are never forwarded;
* the drop paths — a non-UiPath tool call, an unrecognized event, and opt-out.

The stubbed ``uip`` writes the payload to a capture file and we poll for it
(the hook is fire-and-forget, so we never parse its stdout).

POSIX-only: the hooks run under ``bash`` and ``pwsh`` (both preinstalled on
GitHub ubuntu runners) and the stub is a shebang script invoked via a real
``uip`` name on ``PATH``. Skipped on native Windows (PATHEXT resolution makes
the stub unreliable) — CI runs it on ubuntu.

Run from repo root:
    pytest tests/scripts/test_send_telemetry_hook.py
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"

# One argv per twin. The autouse fixture below parametrizes EVERY test over
# both, enforcing the keep-in-sync rule (CLAUDE.md).
TWINS = [
    pytest.param(["bash", str(HOOKS_DIR / "send-telemetry.sh")], id="bash"),
    pytest.param(
        ["pwsh", "-NoProfile", "-File", str(HOOKS_DIR / "send-telemetry.ps1")],
        id="pwsh",
    ),
]

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="stub uip requires a POSIX filesystem (CI runs this on ubuntu)",
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


# ── event-mapping tests ────────────────────────────────────────────────────


def test_session_start_maps_and_carries_source():
    event = run_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "sess-1",
            "source": "startup",
            "model": "claude-sonnet-5",
        }
    )
    assert event["eventName"] == "session-start"
    assert event["session_source"] == "startup"
    assert event["session_id"] == "sess-1"
    # The session's main model (envelope `model`) rides as agent_model —
    # full slug, not family-collapsed (UiPath/cli#2785).
    assert event["agent_model"] == "claude-sonnet-5"
    assert event["schemaVersion"] == 2


def test_session_end_carries_reason():
    event = run_hook(
        {
            "hook_event_name": "SessionEnd",
            "session_id": "sess-1",
            "reason": "logout",
        }
    )
    assert event["eventName"] == "session-end"
    assert event["reason"] == "logout"


def test_stop_maps_to_completion_ok():
    event = run_hook({"hook_event_name": "Stop", "session_id": "sess-1"})
    assert event["eventName"] == "completion"
    assert event["outcome"] == "ok"


def test_codex_session_start_maps_with_source_and_model():
    """Codex fires SessionStart under the same name with a matching envelope
    (session_id / source / model / permission_mode — Codex hooks docs), so the
    mapping, session_source, and agent_model work unchanged."""
    event = run_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "019f1347-4dab-7b31-9277-29c6af7572fe",
            "source": "startup",
            "model": "gpt-5.1-codex",
            "permission_mode": "on-request",
        }
    )
    assert event["eventName"] == "session-start"
    assert event["session_source"] == "startup"
    assert event["agent_model"] == "gpt-5.1-codex"


def test_codex_stop_maps_to_completion_and_ignores_codex_extras():
    """Codex Stop carries turn_id / stop_hook_active / last_assistant_message
    and no duration_ms. It maps to completion(ok); the Codex-only extras are
    never extracted or forwarded (last_assistant_message is free text)."""
    event = run_hook(
        {
            "hook_event_name": "Stop",
            "session_id": "019f1347-4dab-7b31-9277-29c6af7572fe",
            "model": "gpt-5.1-codex",
            "turn_id": "turn-3",
            "stop_hook_active": False,
            "last_assistant_message": "free text that must never leak",
        }
    )
    assert event["eventName"] == "completion"
    assert event["outcome"] == "ok"
    assert event["agent_model"] == "gpt-5.1-codex"
    assert event["durationMs"] is None
    assert "turn_id" not in event
    assert "stop_hook_active" not in event
    assert "last_assistant_message" not in event


def test_session_fields_do_not_bleed_across_events():
    """`source`/`reason` are extracted from any envelope, but the contract
    scopes session_source to session-start and reason to session-end — a stray
    key on another event (future payload additions) must come out empty."""
    event = run_hook(
        {
            "hook_event_name": "Stop",
            "session_id": "sess-1",
            "source": "startup",
            "reason": "spurious",
        }
    )
    assert event["eventName"] == "completion"
    assert event["session_source"] == ""
    assert event["reason"] == ""


def test_stop_failure_maps_to_completion_failure():
    event = run_hook({"hook_event_name": "StopFailure", "session_id": "sess-1"})
    assert event["eventName"] == "completion"
    assert event["outcome"] == "failure"


def test_post_tool_use_uipath_skill_maps_to_tool_use():
    event = run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "Skill",
            "tool_input": {"skill": "uipath:uipath-platform"},
            "tool_response": {"success": True},
            "duration_ms": 1234,
        }
    )
    assert event["eventName"] == "tool-use"
    assert event["skillName"] == "uipath:uipath-platform"
    assert event["outcome"] == "ok"


def test_v2_key_set_has_no_env_fields_or_legacy_session_id():
    """Schema v2 drops environment/baseUrl (the CLI stamps fresh
    environment/base_url/region base dimensions itself, UiPath/cli#2806) and
    sends only the canonical session_id spelling (UiPath/cli#2800)."""
    event = run_hook(
        {
            "hook_event_name": "SessionStart",
            "session_id": "sess-1",
            "source": "startup",
        }
    )
    assert "environment" not in event
    assert "baseUrl" not in event
    assert "sessionId" not in event
    assert "sessionSource" not in event


# ── Autopilot / Delegate tool-name tests ───────────────────────────────────
# UiPath Autopilot / Delegate honor hooks.json with the same envelope but rename
# the shell and file tools (ExecuteBashCommand / ExecutePowershellCommand,
# ReadFile / WriteFile / EditFile / LsDirectory). tool_input still carries
# command / file_path, so attribution + derivation must fire on the renamed
# names exactly as for Claude's Bash / Read / Write / Edit.


def test_autopilot_execute_bash_command_uip_maps_to_tool_use():
    event = run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "ExecuteBashCommand",
            "tool_input": {"command": "uip solution publish --output json"},
            "tool_response": {"success": True},
        }
    )
    assert event["eventName"] == "tool-use"
    assert event["toolName"] == "ExecuteBashCommand"
    assert event["uipSubcommand"] == "solution publish"
    assert event["outcome"] == "ok"


def test_autopilot_execute_powershell_command_uip_maps_to_tool_use():
    event = run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "ExecutePowershellCommand",
            "tool_input": {"command": "uip pack --output json"},
            "tool_response": {"success": True},
        }
    )
    assert event["eventName"] == "tool-use"
    assert event["uipSubcommand"] == "pack"


def test_autopilot_write_file_uipath_ext_maps_to_tool_use():
    event = run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "WriteFile",
            "tool_input": {"file_path": "/proj/Process/Main.xaml"},
            "tool_response": {"success": True},
        }
    )
    assert event["eventName"] == "tool-use"
    assert event["toolName"] == "WriteFile"
    assert event["fileExtension"] == ".xaml"


def test_autopilot_read_file_agent_json_maps_to_tool_use():
    event = run_hook(
        {
            "hook_event_name": "PostToolUse",
            "tool_name": "ReadFile",
            "tool_input": {"file_path": "/proj/agent.json"},
            "tool_response": {"success": True},
        }
    )
    assert event["eventName"] == "tool-use"
    assert event["fileExtension"] == "agent.json"


# ── drop-path tests ────────────────────────────────────────────────────────


def test_non_uipath_tool_call_is_dropped():
    assert (
        run_hook(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            },
            expect_drop=True,
        )
        is None
    )


def test_autopilot_shell_without_uip_is_dropped():
    """The `uip` matcher is anchored, NOT a bare substring — a command that
    merely contains the letters 'uip' (e.g. 'equipment') must not attribute.
    Guards against loosening the gate to a substring match, which would
    over-attribute unrelated commands under the renamed Autopilot tools."""
    assert (
        run_hook(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "ExecuteBashCommand",
                "tool_input": {"command": "echo equipment inventory"},
            },
            expect_drop=True,
        )
        is None
    )


def test_autopilot_read_file_non_uipath_ext_is_dropped():
    assert (
        run_hook(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "ReadFile",
                "tool_input": {"file_path": "/proj/notes.txt"},
            },
            expect_drop=True,
        )
        is None
    )


def test_unrecognized_event_is_dropped():
    assert (
        run_hook(
            {"hook_event_name": "PreToolUse", "tool_name": "Bash"},
            expect_drop=True,
        )
        is None
    )


def test_opt_out_drops_everything():
    assert (
        run_hook(
            {"hook_event_name": "SessionStart", "session_id": "sess-1"},
            telemetry_disabled="1",
            expect_drop=True,
        )
        is None
    )


# ── helpers ────────────────────────────────────────────────────────────────


def run_hook(payload, *, telemetry_disabled="0", expect_drop=False):
    """Invoke the hook with a stubbed ``uip``; return the forwarded JSON object
    (parsed) or ``None`` when the hook drops the event.

    The stubbed ``uip`` writes the forwarded payload to a capture file, which we
    poll. A dropped event never writes it, so ``expect_drop`` polls a short grace
    window instead of the full timeout.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        capture = tmp_path / "capture.json"
        _write_fake_uip(tmp_path / "uip")

        env = {
            **os.environ,
            "PATH": f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}",
            "UIPATH_TELEMETRY_DISABLED": telemetry_disabled,
            "CLAUDE_PLUGIN_ROOT": str(REPO_ROOT),
            "CAPTURE_FILE": str(capture),
        }
        # A UIPATH_SESSION_ID inherited from the CI env would override the
        # payload session id — keep the hook's own behavior under test.
        env.pop("UIPATH_SESSION_ID", None)

        subprocess.run(
            HOOK_ARGV,
            input=json.dumps(payload),
            text=True,
            env=env,
            timeout=30,
            check=True,
        )

        deadline = time.time() + (1.5 if expect_drop else 5.0)
        while time.time() < deadline:
            if capture.exists():
                return json.loads(capture.read_text())
            time.sleep(0.05)
        return None


def _write_fake_uip(path):
    """Stub ``uip``: capture the piped payload on ``uip track`` (atomic write so
    the poller never sees a partial file)."""
    path.write_text(
        "#!/bin/bash\n"
        'if [ "$1" = "track" ]; then\n'
        '  cat > "$CAPTURE_FILE.tmp" && mv "$CAPTURE_FILE.tmp" "$CAPTURE_FILE"\n'
        "fi\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IRWXU | stat.S_IEXEC)
