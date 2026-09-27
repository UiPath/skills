"""Contract guard for the suggest-permissions SessionStart hook.

Runs both implementations against the same scenarios:

- hooks/suggest-permissions.sh
- hooks/suggest-permissions.ps1

The hook must suggest /uipath:install-permissions only inside Claude Code
when no explicit Bash(uip...) permission rule exists.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"

SUGGESTION = (
    "uipath: To skip 25+ approval prompts per uip build, "
    "run: /uipath:install-permissions"
)

TWINS = [
    pytest.param(
        ["bash", str(HOOKS_DIR / "suggest-permissions.sh")],
        id="bash",
    ),
    pytest.param(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(HOOKS_DIR / "suggest-permissions.ps1"),
        ],
        id="pwsh",
    ),
]

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="CI executes both twins on an Ubuntu runner",
)

HOOK_ARGV = None


@pytest.fixture(autouse=True, params=TWINS)
def hook_argv(request):
    """Run every test against both hook implementations."""
    global HOOK_ARGV

    argv = request.param

    if shutil.which(argv[0]) is None:
        pytest.skip(f"{argv[0]} not available")

    HOOK_ARGV = argv


def test_suggests_permissions_when_no_rule_exists():
    result = run_hook()

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr.strip() == SUGGESTION


def test_skips_outside_claude_plugin_context():
    result = run_hook(claude_plugin=False)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_skips_inside_codex():
    result = run_hook(extra_env={"PLUGIN_ROOT": "/fake/codex/plugin"})

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize(
    "settings_file",
    [
        ".claude/settings.local.json",
        ".claude/settings.json",
    ],
)
def test_skips_when_project_has_explicit_uip_rule(settings_file):
    result = run_hook(
        project_files={
            settings_file: """
            {
              "permissions": {
                "allow": ["Bash(uip project validate:*)"]
              }
            }
            """
        }
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_skips_when_global_settings_have_uip_rule():
    result = run_hook(
        home_files={
            ".claude/settings.json": """
            {
              "permissions": {
                "allow": ["Bash(uip:*)"]
              }
            }
            """
        }
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize("permission_group", ["allow", "ask", "deny"])
def test_any_explicit_uip_decision_suppresses_suggestion(permission_group):
    result = run_hook(
        project_files={
            ".claude/settings.json": f"""
            {{
              "permissions": {{
                "{permission_group}": ["Bash(uip solution publish:*)"]
              }}
            }}
            """
        }
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_unrelated_bash_rule_does_not_suppress_suggestion():
    result = run_hook(
        project_files={
            ".claude/settings.json": """
            {
              "permissions": {
                "allow": ["Bash(git status)"]
              }
            }
            """
        }
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr.strip() == SUGGESTION


def test_handles_paths_with_spaces():
    result = run_hook(
        project_files={
            ".claude/settings.local.json": """
            {
              "permissions": {
                "allow": ["Bash(uip project build:*)"]
              }
            }
            """
        },
        temp_prefix="uipath permissions test ",
    )

    assert result.returncode == 0
    assert result.stderr == ""


def run_hook(
    *,
    claude_plugin=True,
    project_files=None,
    home_files=None,
    extra_env=None,
    temp_prefix="uipath-hook-test-",
):
    """Execute one hook twin in a completely isolated environment."""

    with tempfile.TemporaryDirectory(prefix=temp_prefix) as tmp:
        root = Path(tmp)
        project_dir = root / "project"
        home_dir = root / "home"
        plugin_dir = root / "plugin"

        project_dir.mkdir()
        home_dir.mkdir()
        plugin_dir.mkdir()

        write_files(project_dir, project_files or {})
        write_files(home_dir, home_files or {})

        env = {
            **os.environ,
            "HOME": str(home_dir),
            "CLAUDE_PROJECT_DIR": str(project_dir),
        }

        # Prevent the test from inheriting the developer's actual context.
        env.pop("CLAUDE_PLUGIN_ROOT", None)
        env.pop("PLUGIN_ROOT", None)

        if claude_plugin:
            env["CLAUDE_PLUGIN_ROOT"] = str(plugin_dir)

        if extra_env:
            env.update(extra_env)

        return subprocess.run(
            HOOK_ARGV,
            cwd=project_dir,
            env=env,
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )


def write_files(base_dir, files):
    """Create a set of files relative to an isolated directory."""

    for relative_path, content in files.items():
        destination = base_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")
