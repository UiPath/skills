"""Regression tests for the two static gates in scripts/check-task-driver.py.

Gate 1 (no `sandbox.driver: tempdir`) predates these tests and was previously
unguarded; it is pinned here alongside the new one.

Gate 2 (experiment hook commands must be a single line) exists because of the
2026-09-04 outage: a multi-line POSIX sh `pre_run` hook landed in
`tests/experiments/nightly.yaml` (skills #2756, commit 80c757e03), cmd.exe on
the Windows split parses only the first line of what it is handed, and the whole
split came back `7/7 status=ERROR score=0.000 iterations=0`. skills #3116 fixed
the hook by collapsing it to one line.

`test_would_have_caught_the_2026_09_04_outage` is the point of this file: it
feeds the real historical command back through the gate and asserts it fails.

Run from repo root:
    pytest tests/scripts/test_check_task_driver.py
"""

import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-task-driver.py"

# The `pre_run` command exactly as it stood on main between skills #2756
# (80c757e03, 2026-09-04) and #3116 (ead274593, 2026-09-07). Verified against
# git history by `test_broken_hook_fixture_matches_git_history` below.
BROKEN_HOOK = (
    'if [ "${MAESTRO_FLOW_SDK_SETUP:-0}" = "1" ]; then\n'
    '  bash "$SKILLS_REPO_PATH/tests/scripts/stage-preview-sdk-workspace.sh"\n'
    "fi"
)

# The command #3116 replaced it with, currently live in nightly.yaml.
FIXED_HOOK = (
    ':; if [ "${MAESTRO_FLOW_SDK_SETUP:-0}" = "1" ]; then '
    'bash "$SKILLS_REPO_PATH/tests/scripts/stage-preview-sdk-workspace.sh"; fi'
)


def _run(*paths: Path) -> tuple[int, str]:
    """Run the gate as the workflow does, returning (exit code, combined output)."""
    proc = subprocess.run(
        ["python3", str(SCRIPT), *map(str, paths)], capture_output=True, text=True, check=False
    )
    return proc.returncode, proc.stdout + proc.stderr


def _write_experiment(tmp_path: Path, hook: str, command: str) -> Path:
    path = tmp_path / "nightly.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "experiment_id": "test-experiment",
                "defaults": {hook: [{"command": command, "timeout": 30}]},
                "variants": [{"variant_id": "default"}],
            },
            sort_keys=False,
        )
    )
    return path


class TestWouldHaveCaughtTheOutage:
    def test_would_have_caught_the_2026_09_04_outage(self, tmp_path):
        rc, out = _run(_write_experiment(tmp_path, "pre_run", BROKEN_HOOK))
        assert rc == 1, out
        assert "span multiple lines" in out
        assert "defaults.pre_run[0].command" in out

    def test_the_shipped_fix_passes(self, tmp_path):
        rc, out = _run(_write_experiment(tmp_path, "pre_run", FIXED_HOOK))
        assert rc == 0, out

    def test_post_run_is_covered_too(self, tmp_path):
        """post_run failures only warn-log at runtime, so nothing else catches them."""
        rc, out = _run(_write_experiment(tmp_path, "post_run", "echo one\necho two"))
        assert rc == 1, out
        assert "defaults.post_run[0].command" in out

    def test_known_gap_single_line_posix_passes(self, tmp_path):
        """Documents the deliberate limit of this gate.

        A POSIX hook that fits on one line still breaks cmd.exe (no `[`, no
        `test`, `==` not `=`, no `then`/`fi`) and this gate lets it through.
        Catching it needs a construct table plus quote-awareness plus a
        Windows-reachability list plus an exemption for the overlay-translated
        cleanup. That was built and deliberately cut as too much machinery for a
        failure mode that has not happened yet.
        """
        one_line = " ".join(line.strip() for line in BROKEN_HOOK.splitlines())
        rc, _ = _run(_write_experiment(tmp_path, "pre_run", one_line))
        assert rc == 0

    @pytest.mark.skipif(
        subprocess.run(
            ["git", "cat-file", "-e", "80c757e03^{commit}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        ).returncode
        != 0,
        reason="commit 80c757e03 not in this clone (shallow checkout)",
    )
    def test_broken_hook_fixture_matches_git_history(self):
        """BROKEN_HOOK is the real string, not a retyped approximation."""
        blob = subprocess.run(
            ["git", "show", "80c757e03:tests/experiments/nightly.yaml"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        assert yaml.safe_load(blob)["defaults"]["pre_run"][0]["command"] == BROKEN_HOOK


class TestDriverGate:
    def _write(self, tmp_path: Path, driver: str) -> Path:
        path = tmp_path / "task.yaml"
        path.write_text(
            textwrap.dedent(
                f"""\
                task_id: fixture-task
                description: "fixture"
                initial_prompt: "do a thing"
                sandbox:
                  driver: {driver}
                success_criteria:
                  - type: file_exists
                    description: "exists"
                    path: out.txt
                    weight: 1.0
                """
            )
        )
        return path

    def test_tempdir_pin_fails(self, tmp_path):
        rc, out = _run(self._write(tmp_path, "tempdir"))
        assert rc == 1, out
        assert "sandbox.driver: tempdir" in out
        assert ",line=5" in out

    def test_docker_pin_is_a_note_not_a_failure(self, tmp_path):
        rc, out = _run(self._write(tmp_path, "docker"))
        assert rc == 0, out
        assert "redundant with the Linux default" in out


def test_live_corpus_passes_both_gates():
    rc, out = _run(REPO_ROOT / "tests" / "tasks", REPO_ROOT / "tests" / "experiments")
    assert rc == 0, out
    assert "no task pins `sandbox.driver: tempdir`" in out
    assert "experiment hook command(s) are single-line" in out
