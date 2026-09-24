"""Guards for the agent-visible plugin root (tests/scripts/stage_plugin_root.py).

coder_eval bind-mounts `agent.plugins[].path` into the task container at its host
path, so whatever sits under it is readable by the agent under test. These tests
pin the two halves that keep the eval's own fixtures out of it: the staged tree
carries no grading material, and every experiment and runner points at that tree
rather than at the repo root.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "tests" / "scripts" / "stage_plugin_root.py"
EXPERIMENTS = REPO_ROOT / "tests" / "experiments"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

PLUGIN_ROOT = "$SKILLS_REPO_PATH/.plugin-root"

# Comparison harnesses: every plugin path is an operator-supplied worktree, and
# both pin the agent to its working directory in the system prompt.
EXEMPT_EXPERIMENTS = {"sherif-skill-comparison.yaml", "skill-comparison-template.yaml"}


@pytest.fixture(scope="module")
def staged(tmp_path_factory: pytest.TempPathFactory) -> Path:
    dest = tmp_path_factory.mktemp("staged") / ".plugin-root"
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "--dest", str(dest)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert out.stdout.strip() == str(dest)
    return dest


def test_staged_tree_carries_no_grading_material(staged: Path) -> None:
    # tests/scripts (the pre_run hooks) is the only slice of tests/ the agent gets.
    assert [p.name for p in (staged / "tests").iterdir()] == ["scripts"]

    assert [p for p in staged.rglob("*.reference.*")] == []


def test_staged_tree_is_a_loadable_plugin_root(staged: Path) -> None:
    for rel in (
        ".claude-plugin/plugin.json",
        "skills/uipath-maestro-flow/SKILL.md",
        "commands",
        "hooks/hooks.json",
        "preview/.claude-plugin/plugin.json",
        "preview/skills",
        # The docker experiments run this out of the mount as a pre_run hook.
        "tests/scripts/stage-preview-sdk-workspace.sh",
    ):
        assert (staged / rel).exists(), rel


def test_staged_tree_keeps_up_with_the_plugin_manifest(staged: Path) -> None:
    """A plugin dir added to the repo but not to STAGED_PATHS silently stops loading."""
    manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
    declared = [manifest.get("skills", "./skills/"), *(manifest.get("agents") or [])]
    for rel in declared:
        assert (staged / rel.lstrip("./")).exists(), rel

    # Everything claude-code auto-discovers at a plugin root.
    for name in (".claude-plugin", "skills", "commands", "hooks", "agents", ".mcp.json"):
        if (REPO_ROOT / name).exists():
            assert (staged / name).exists(), name


def test_staged_tree_has_no_symlink_back_into_the_repo(staged: Path) -> None:
    assert [p for p in staged.rglob("*") if p.is_symlink()] == []


def test_staging_is_idempotent(staged: Path) -> None:
    subprocess.run([sys.executable, str(SCRIPT), "--dest", str(staged)], check=True, capture_output=True)
    assert (staged / ".claude-plugin" / "plugin.json").exists()


def test_staging_refuses_to_overwrite_the_repo() -> None:
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--dest", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert done.returncode != 0


def _experiments() -> list[Path]:
    return sorted(p for p in EXPERIMENTS.glob("*.yaml") if p.name not in EXEMPT_EXPERIMENTS)


@pytest.mark.parametrize("path", _experiments(), ids=lambda p: p.name)
def test_experiment_never_exposes_the_repo_root(path: Path) -> None:
    config = yaml.safe_load(path.read_text())
    blocks = [config.get("defaults") or {}, *(config.get("variants") or [])]

    for block in blocks:
        for plugin in ((block.get("agent") or {}).get("plugins") or []):
            plugin_path = plugin.get("path", "")
            assert plugin_path == PLUGIN_ROOT or plugin_path.startswith(f"{PLUGIN_ROOT}/"), (
                f"{path.name}: plugin path {plugin_path!r} must be under {PLUGIN_ROOT} — "
                "the repo root mounts tests/tasks into the agent's container"
            )

        docker = ((block.get("sandbox") or {}).get("docker")) or {}
        for mount in docker.get("extra_mounts") or []:
            source = str(mount).split(":", 1)[0]
            assert source != "$SKILLS_REPO_PATH", f"{path.name}: extra_mount exposes the repo root"

        for hook in (block.get("pre_run") or []) + (block.get("post_run") or []):
            command = hook.get("command", "")
            assert "$SKILLS_REPO_PATH/tests/" not in command, (
                f"{path.name}: hook reads $SKILLS_REPO_PATH/tests/ — use {PLUGIN_ROOT}/tests/scripts/"
            )


@pytest.mark.parametrize(
    "path",
    sorted(p for p in WORKFLOWS.glob("*.yml") if re.search(r"^\s+SKILLS_REPO_PATH:\s", p.read_text(), re.M)),
    ids=lambda p: p.name,
)
def test_runner_stages_the_plugin_root(path: Path) -> None:
    assert "stage_plugin_root.py" in path.read_text(), (
        f"{path.name} runs coder-eval but never stages {PLUGIN_ROOT}"
    )
