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
from collections.abc import Iterator
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
    # One hook script is the whole of tests/ the agent gets.
    assert [str(p.relative_to(staged)) for p in sorted((staged / "tests").rglob("*")) if p.is_file()] == [
        "tests/scripts/stage-preview-sdk-workspace.sh"
    ]

    assert [p for p in staged.rglob("*.reference.*")] == []


def test_staged_tree_is_a_loadable_plugin_root(staged: Path) -> None:
    for rel in (
        ".claude-plugin/plugin.json",
        "skills/uipath-maestro-flow/SKILL.md",
        "commands",
        "hooks/hooks.json",
        # Both send-telemetry twins read skillsVersion out of the plugin root.
        "version-manifest.json",
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


def test_staging_refuses_a_source_symlink(tmp_path: Path) -> None:
    """A link under a staged source would otherwise copy tests/tasks in as real files."""
    fake_repo = tmp_path / "repo"
    for rel in ("skills", "commands", "hooks", ".claude-plugin", "preview", "tests/scripts"):
        (fake_repo / rel).mkdir(parents=True)
    (fake_repo / "tests" / "scripts" / "stage-preview-sdk-workspace.sh").write_text("")
    (fake_repo / "version-manifest.json").write_text("{}")
    (fake_repo / "tests" / "tasks").mkdir()
    (fake_repo / "tests" / "tasks" / "answer.reference.flow").write_text("golden")
    (fake_repo / "skills" / "leak").symlink_to(fake_repo / "tests" / "tasks")

    dest = tmp_path / ".plugin-root"
    done = subprocess.run(
        [sys.executable, str(SCRIPT), "--repo-root", str(fake_repo), "--dest", str(dest)],
        capture_output=True,
        text=True,
    )
    assert done.returncode != 0
    assert not dest.exists()


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


def _grader_common(monkeypatch: pytest.MonkeyPatch):
    import importlib.util

    path = REPO_ROOT / "tests" / "tasks" / "uipath-review" / "rpa" / "_shared" / "grader_common.py"
    spec = importlib.util.spec_from_file_location("grader_common_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_graders_resolve_the_skill_docs_the_agent_sees(staged: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The sandbox condition exactly: SKILLS_REPO_PATH set, only .plugin-root readable."""
    grader_common = _grader_common(monkeypatch)
    sandbox_repo = staged.parent / "not-mounted"
    sandbox_repo.mkdir(exist_ok=True)
    (sandbox_repo / ".plugin-root").symlink_to(staged, target_is_directory=True)

    monkeypatch.setenv("SKILLS_REPO_PATH", str(sandbox_repo))
    refs = grader_common.skill_references_dir("uipath-review")
    assert refs is not None and refs.is_dir()
    assert list(refs.glob("*.md"))

    # Host-side run: nothing staged, the repo itself answers.
    host_repo = staged.parent / "host-repo"
    (host_repo / "skills" / "uipath-review" / "references").mkdir(parents=True)
    monkeypatch.setenv("SKILLS_REPO_PATH", str(host_repo))
    assert grader_common.skill_references_dir("uipath-review") == (
        host_repo / "skills" / "uipath-review" / "references"
    )

    # Neither: the caller must be told, not silently handed an empty corpus.
    monkeypatch.setenv("SKILLS_REPO_PATH", str(staged.parent / "nowhere"))
    assert grader_common.skill_references_dir("uipath-review") is None

    monkeypatch.delenv("SKILLS_REPO_PATH")
    assert grader_common.skill_references_dir("uipath-review") is None


def _repo_var(value: str) -> str:
    """Both spellings of the variable must be caught, not just the bare one."""
    return value.replace("${SKILLS_REPO_PATH}", "$SKILLS_REPO_PATH")


def _experiments() -> list[Path]:
    return sorted(p for p in EXPERIMENTS.glob("*.yaml") if p.name not in EXEMPT_EXPERIMENTS)


@pytest.mark.parametrize("path", _experiments(), ids=lambda p: p.name)
def test_experiment_never_exposes_the_repo_root(path: Path) -> None:
    config = yaml.safe_load(path.read_text())
    blocks = [config.get("defaults") or {}, *(config.get("variants") or [])]

    for block in blocks:
        for plugin in ((block.get("agent") or {}).get("plugins") or []):
            plugin_path = _repo_var(plugin.get("path", ""))
            assert plugin_path == PLUGIN_ROOT or plugin_path.startswith(f"{PLUGIN_ROOT}/"), (
                f"{path.name}: plugin path {plugin_path!r} must be under {PLUGIN_ROOT} — "
                "the repo root mounts tests/tasks into the agent's container"
            )

        docker = ((block.get("sandbox") or {}).get("docker")) or {}
        for mount in docker.get("extra_mounts") or []:
            source = _repo_var(str(mount).split(":", 1)[0])
            if not source.startswith("$SKILLS_REPO_PATH"):
                continue
            assert source == PLUGIN_ROOT or source.startswith(f"{PLUGIN_ROOT}/"), (
                f"{path.name}: extra_mount {source!r} exposes part of the repo outside {PLUGIN_ROOT}"
            )

        for hook in (block.get("pre_run") or []) + (block.get("post_run") or []):
            command = _repo_var(hook.get("command", ""))
            assert "$SKILLS_REPO_PATH/tests/" not in command, (
                f"{path.name}: hook reads $SKILLS_REPO_PATH/tests/ — use {PLUGIN_ROOT}/tests/scripts/"
            )


def _task_hooks_and_commands(config: object) -> Iterator[str]:
    """Every task string that runs inside the sandbox, at any nesting depth."""
    if isinstance(config, dict):
        for key, value in config.items():
            if key == "command" and isinstance(value, str):
                yield value
            else:
                yield from _task_hooks_and_commands(value)
    elif isinstance(config, list):
        for item in config:
            yield from _task_hooks_and_commands(item)


def test_no_task_reaches_through_the_repo_root() -> None:
    """A task hook or criterion addressing $SKILLS_REPO_PATH now ERRORs every run.

    Only .plugin-root is mounted. $TASK_DIR and $REFERENCE_DIR are the addressing
    that survives, and neither reaches pre_run — a hook that needs the repo tree
    is a repo unit test, not an eval.
    """
    tasks_root = REPO_ROOT / "tests" / "tasks"
    violations = [
        f"{path.relative_to(tasks_root)}: {command.strip()[:120]}"
        for path in sorted(tasks_root.rglob("*.yaml"))
        for command in _task_hooks_and_commands(yaml.safe_load(path.read_text()))
        if "SKILLS_REPO_PATH" in _repo_var(command)
    ]
    assert violations == []


def _jobs_that_run_coder_eval() -> list[tuple[Path, str, list[dict]]]:
    """Every workflow job with a step whose env sets SKILLS_REPO_PATH."""
    found = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        if not re.search(r"^\s+SKILLS_REPO_PATH:\s", path.read_text(), re.M):
            continue
        for name, job in (yaml.safe_load(path.read_text()).get("jobs") or {}).items():
            steps = job.get("steps") or []
            if any("SKILLS_REPO_PATH" in (step.get("env") or {}) for step in steps):
                found.append((path, name, steps))
    return found


@pytest.mark.parametrize(
    "path,job,steps",
    _jobs_that_run_coder_eval(),
    ids=lambda v: v.name if isinstance(v, Path) else (v if isinstance(v, str) else ""),
)
def test_runner_stages_the_plugin_root_first(path: Path, job: str, steps: list[dict]) -> None:
    """Staging has to precede the run, not merely appear somewhere in the file."""
    stages_at = [i for i, step in enumerate(steps) if "stage_plugin_root.py" in (step.get("run") or "")]
    runs_at = [i for i, step in enumerate(steps) if "SKILLS_REPO_PATH" in (step.get("env") or {})]
    assert stages_at, f"{path.name}:{job} runs coder-eval but never stages {PLUGIN_ROOT}"
    assert min(stages_at) < min(runs_at), (
        f"{path.name}:{job} stages {PLUGIN_ROOT} after the step that runs coder-eval"
    )
