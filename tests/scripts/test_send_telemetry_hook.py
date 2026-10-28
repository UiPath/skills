"""Contract guard for the telemetry hook registrations in ``hooks/hooks.json``.

Since UiPath/cli#4444 the field derivation lives in the CLI: the plugin no
longer ships a telemetry hook script at all. Every telemetry entry pipes the
RAW agent hook payload straight to ``uip track --hook``, and the CLI derives,
sanitizes, and emits the event in-process (guarded there by
``packages/cli/src/commands/track-hook.spec.ts``, the port of the suite that
used to live here against ``send-telemetry.mjs`` and the ``.sh``/``.ps1``
twins before it).

What is left to pin on the plugin side is the WRAPPER contract:

* every telemetry entry runs ``uip track --hook`` and passes stdin through
  verbatim — the CLI must receive the exact payload bytes the host piped;
* fail-soft: ``uip`` absent → exit 0; ``uip`` failing (e.g. a CLI predating
  ``--hook``, whose option parser rejects it) → exit 0 with NO output leaked;
* the hand-off is inline (the wrapper foregrounds ``uip``), so the synchronous
  SessionEnd registration still guarantees the last event is flushed before
  session teardown;
* registration shape: async on every event EXCEPT SessionEnd, which is
  synchronous with a 30s timeout, and all five events share one identical
  command string.

POSIX-only: the stub ``uip`` is a shebang script on ``PATH``; the sh branch of
the polyglot is exercised under bash, dash (``sh``), and zsh. The PowerShell
branch (``uip.cmd`` resolution) is covered by manual Windows verification —
see CONTRIBUTING.md § Hooks.

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
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_JSON = REPO_ROOT / "hooks" / "hooks.json"

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="stub uip requires a POSIX filesystem (CI runs this on ubuntu)",
)

PAYLOAD = json.dumps(
    {
        "hook_event_name": "PostToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "uip solution publish --output json"},
        "tool_response": {"success": True, "stdout": "customer content é"},
        "duration_ms": 1234,
    }
)


def hooks_config():
    return json.loads(HOOKS_JSON.read_text())["hooks"]


def telemetry_entries():
    """Every hook entry whose command invokes `uip track --hook`, keyed by
    event name."""
    entries = {}
    for event, groups in hooks_config().items():
        for group in groups:
            for hook in group["hooks"]:
                if "track --hook" in hook["command"]:
                    entries.setdefault(event, []).append(hook)
    return entries


# ── registration-shape tests ────────────────────────────────────────────────


def test_telemetry_registered_on_all_five_events():
    assert set(telemetry_entries()) == {
        "SessionStart",
        "PostToolUse",
        "SessionEnd",
        "Stop",
        "StopFailure",
    }
    assert all(len(hooks) == 1 for hooks in telemetry_entries().values())


def test_all_events_share_one_command_string():
    commands = {
        hooks[0]["command"] for hooks in telemetry_entries().values()
    }
    assert len(commands) == 1, "telemetry command strings have diverged"


def test_async_everywhere_except_synchronous_session_end():
    """SessionEnd must be synchronous: async hooks still running at session
    teardown are killed after a grace window shorter than the CLI's startup,
    which would silently drop the very last event."""
    entries = telemetry_entries()
    for event in ("SessionStart", "PostToolUse", "Stop", "StopFailure"):
        assert entries[event][0].get("async") is True, f"{event} must be async"
    session_end = entries["SessionEnd"][0]
    assert "async" not in session_end, "SessionEnd must be synchronous"
    assert session_end.get("timeout") == 30


def test_wrapper_keeps_the_polyglot_shape():
    """No `shell` field; sh branch first; PowerShell branch heredoc-wrapped and
    resolving uip.cmd (the bare name would hit npm's uip.ps1 shim, which
    PowerShell prefers and execution policy can block)."""
    command = telemetry_entries()["PostToolUse"][0]["command"]
    entry = telemetry_entries()["PostToolUse"][0]
    assert "shell" not in entry
    assert command.startswith("echo `# <#` >/dev/null\n")
    assert ": <<'POLYEOF' #> > $null" in command
    assert command.rstrip().endswith("POLYEOF")
    assert "uip.cmd" in command
    sh_branch = command.split(": <<'POLYEOF'")[0]
    assert "#>" not in sh_branch


# ── behavioral tests (sh branch under bash / dash / zsh) ────────────────────


SHELLS = [
    pytest.param("bash", id="bash"),
    pytest.param("sh", id="sh"),
    pytest.param("zsh", id="zsh"),
]


def run_wrapper(shell, *, with_uip=True, uip_body=None, payload=PAYLOAD):
    """Run the telemetry wrapper under `shell` with a stubbed `uip`; return
    (exit_code, stdout+stderr, captured argv or None, captured stdin or None).
    """
    command = telemetry_entries()["PostToolUse"][0]["command"]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        argv_file = tmp_path / "argv"
        stdin_file = tmp_path / "stdin"
        if with_uip:
            stub = tmp_path / "uip"
            stub.write_text(
                uip_body
                or (
                    "#!/bin/bash\n"
                    f'printf \'%s\' "$*" > "{argv_file}"\n'
                    f'cat > "{stdin_file}"\n'
                )
            )
            stub.chmod(stub.stat().st_mode | stat.S_IRWXU)
            path = f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}"
        else:
            # Minimal PATH holding only the shells — no uip anywhere.
            bindir = tmp_path / "bin"
            bindir.mkdir()
            for name in ("bash", "sh", "zsh", "cat", "printf"):
                target = shutil.which(name)
                if target:
                    (bindir / name).symlink_to(target)
            path = str(bindir)

        result = subprocess.run(
            [shell, "-c", command],
            input=payload,
            text=True,
            capture_output=True,
            env={**os.environ, "PATH": path},
            timeout=30,
        )
        argv = argv_file.read_text() if argv_file.exists() else None
        stdin = stdin_file.read_text() if stdin_file.exists() else None
        return result.returncode, result.stdout + result.stderr, argv, stdin


@pytest.fixture(autouse=True, params=SHELLS)
def shell(request):
    if shutil.which(request.param) is None:
        pytest.skip(f"{request.param} not available")
    return request.param


def test_invokes_track_hook_and_passes_stdin_verbatim(shell):
    code, output, argv, stdin = run_wrapper(shell)
    assert code == 0
    assert output == ""
    assert argv == "track --hook"
    assert stdin == PAYLOAD, "payload must reach the CLI byte-for-byte"


def test_missing_uip_is_a_silent_no_op(shell):
    code, output, argv, _ = run_wrapper(shell, with_uip=False)
    assert code == 0
    assert output == ""
    assert argv is None


def test_failing_uip_is_swallowed_without_output(shell):
    """A CLI predating --hook rejects the option, prints an error, and exits
    non-zero. The wrapper must exit 0 and leak nothing."""
    code, output, _, _ = run_wrapper(
        shell,
        uip_body=(
            "#!/bin/bash\n"
            "cat >/dev/null\n"
            "echo \"error: unknown option '--hook'\" >&2\n"
            "exit 1\n"
        ),
    )
    assert code == 0
    assert output == ""


def test_hand_off_is_inline_not_detached(shell):
    """The wrapper foregrounds `uip`, so by the time it exits the CLI has
    already consumed the payload — the property that makes the synchronous
    SessionEnd registration meaningful (a detached hand-off would let session
    teardown kill the CLI before it flushes the final event)."""
    code, _, _, stdin = run_wrapper(shell)
    assert code == 0
    # No polling: the capture must exist the moment the wrapper returns.
    assert stdin == PAYLOAD
