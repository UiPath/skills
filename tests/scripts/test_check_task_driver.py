"""Regression tests for the gates in scripts/check-task-driver.py.

Gate 1 (no `sandbox.driver: tempdir`) predates these tests and was unguarded.
Gate 2 (single-line experiment hooks) exists because of the 2026-09-04 outage:
a multi-line POSIX pre_run in nightly.yaml (skills #2756, 80c757e03) left the
Windows split at 7/7 status=ERROR. #3116 fixed it; nothing caught it.
Gate 4 (no catastrophic backtracking) exists because #4574 shipped a clone
pattern that did not finish a failing search in 120s at 20 quoted words.
"""

import importlib.util
import subprocess
import textwrap
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check-task-driver.py"

# As it stood on main between #2756 and #3116. Pinned to git history below.
BROKEN_HOOK = (
    'if [ "${MAESTRO_FLOW_SDK_SETUP:-0}" = "1" ]; then\n'
    '  bash "$SKILLS_REPO_PATH/tests/scripts/stage-preview-sdk-workspace.sh"\n'
    "fi"
)

# What #3116 replaced it with, live in nightly.yaml today.
FIXED_HOOK = (
    ':; if [ "${MAESTRO_FLOW_SDK_SETUP:-0}" = "1" ]; then '
    'bash "$SKILLS_REPO_PATH/tests/scripts/stage-preview-sdk-workspace.sh"; fi'
)


def _run(*paths: Path) -> tuple[int, str]:
    """Run the gate as the workflow does: (exit code, combined output)."""
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


def _write_task(tmp_path: Path, tags: list[str], hook: str, command: str) -> Path:
    path = tmp_path / "task.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "task_id": "fixture-task",
                "description": "fixture",
                "initial_prompt": "do a thing",
                "tags": tags,
                hook: [{"command": command, "timeout": 30}],
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
        """post_run only warn-logs at runtime, so nothing else catches it."""
        rc, out = _run(_write_experiment(tmp_path, "post_run", "echo one\necho two"))
        assert rc == 1, out
        assert "defaults.post_run[0].command" in out

    def test_known_gap_single_line_posix_passes(self, tmp_path):
        """One-line POSIX still breaks cmd and is deliberately not caught.

        Catching it needs a construct table, quote-awareness (every
        windows-tagged run_command is a cmd-safe `python -c "..."`), a
        Windows-reachability list, and an exemption for the overlay-translated
        cleanup. Built, then cut: too much machinery for a failure mode that
        has not happened.
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



class TestHookScope:
    """The gate scans what cmd.exe can reach, and nothing else."""

    def test_windows_tagged_task_hook_is_caught(self, tmp_path):
        path = _write_task(tmp_path, ["uipath-rpa", "windows"], "pre_run", BROKEN_HOOK)
        rc, out = _run(path)
        assert rc == 1, out
        assert "pre_run[0].command" in out

    def test_untagged_task_hook_is_left_alone(self, tmp_path):
        """24 multi-line task hooks exist and none runs on Windows; don't flag them."""
        rc, out = _run(_write_task(tmp_path, ["uipath-rpa"], "pre_run", BROKEN_HOOK))
        assert rc == 0, out

    def test_variant_level_hook_is_caught(self, tmp_path):
        """`variants` is a list, so the scope walk has to descend into it."""
        path = tmp_path / "experiment.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "experiment_id": "test-experiment",
                    "variants": [
                        {"variant_id": "a", "pre_run": [{"command": BROKEN_HOOK}]}
                    ],
                },
                sort_keys=False,
            )
        )
        rc, out = _run(path)
        assert rc == 1, out
        assert "variants[0].pre_run[0].command" in out


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


class TestStagedSkillGate:
    """Gate 3 — a skill directory in template_sources feeds the preview arm the
    shipped v1 guidance and destroys the v1-vs-v2 comparison. Every
    uipath-maestro-bpmn task did it until 2026-09-23; the README said not to and
    the porting brief said to, so it needs a gate rather than a convention."""

    def _write(self, tmp_path: Path, src_path: str) -> Path:
        path = tmp_path / "task.yaml"
        path.write_text(
            textwrap.dedent(
                f"""\
                task_id: fixture-task
                description: "fixture"
                initial_prompt: "do a thing"
                sandbox:
                  template_sources:
                    - type: template_dir
                      path: {src_path}
                success_criteria:
                  - type: file_exists
                    description: "exists"
                    path: out.txt
                    weight: 1.0
                """
            )
        )
        return path

    def test_staged_skill_dir_fails(self, tmp_path):
        rc, out = _run(self._write(tmp_path, "../../../../../skills/uipath-maestro-bpmn"))
        assert rc == 1, out
        assert "stage a skill directory" in out

    def test_deeper_relative_path_is_caught_too(self, tmp_path):
        # The porting brief told authors to "adjust the .. count to depth", so the
        # gate must not key on one spelling.
        rc, out = _run(self._write(tmp_path, "../../../../../../skills/uipath-maestro-flow"))
        assert rc == 1, out
        assert "stage a skill directory" in out

    def test_a_skill_subdirectory_is_caught(self, tmp_path):
        # Staging skills/<name>/references puts the same v1 guidance in cwd as
        # staging the skill root does. The first version of this gate anchored on
        # end-of-string and let it through.
        rc, out = _run(self._write(tmp_path, "../../../../../skills/uipath-maestro-bpmn/references"))
        assert rc == 1, out
        assert "stage a skill directory" in out

    def test_a_data_dir_inside_a_skill_is_left_alone(self, tmp_path):
        # The bug is guidance in cwd, not the `skills/` prefix. uipath-coded-apps
        # legitimately stages fixture data that lives inside its skill folder, and
        # the first widening of this gate broke it.
        rc, out = _run(self._write(tmp_path, "../../../../../skills/uipath-coded-apps/assets/fixtures"))
        assert rc == 0, out
        assert "stage a skill directory" not in out

    def test_setup_and_fixture_entries_are_left_alone(self, tmp_path):
        rc, out = _run(self._write(tmp_path, "../_setup"))
        assert rc == 0, out
        assert "stage a skill directory" not in out

    def test_a_fixture_dir_named_skills_something_is_not_a_skill(self, tmp_path):
        # `skills/<name>` is the shape; a fixture that merely contains the word is not.
        rc, out = _run(self._write(tmp_path, "fixtures/skills-inventory"))
        assert rc == 0, out
        assert "stage a skill directory" not in out


# The testcase_clone_smoke criterion as #4574 shipped it: `'` is in both the
# quoted-word branch and the catch-all, so each quoted word parses two ways.
PR_4574_CLONE = (
    r"(uip|\$UIP)\s+tm\s+testcases\s+clone\b(?:\x27[^\x27\n]*\x27|\\\n|(?!\s\||\s(?:uip|\$UIP)\s)"
    r"[^\n;&])*?--include(?:[\s\\=]+[\"\x27]?[a-z]+[\"\x27]?)*?[\s\\=]+[\"\x27]?labels\b"
)
# The fix: `'` only opens a quoted word at a word start and is out of the catch-all.
FIXED_CLONE = (
    r"(uip|\$UIP)\s+tm\s+testcases\s+clone\b(?:(?<=[\s=($\x22])\x27[^\x27\n]*\x27|\\\n|"
    r"(?!\s\||\s(?:uip|\$UIP)\s)[^\n;&\x27])*?--include(?:[\s\\=]+[\"\x27]?[a-z]+[\"\x27]?)*?"
    r"[\s\\=]+[\"\x27]?labels\b"
)


def _load_gate():
    spec = importlib.util.spec_from_file_location("check_task_driver_gate4", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBacktrackingGate:
    """Gate 4 — a command_pattern exponential on a failing search hangs grading."""

    def _write(self, tmp_path: Path, pattern: str, description: str = "graded command") -> Path:
        path = tmp_path / "task.yaml"
        path.write_text(
            yaml.safe_dump(
                {
                    "task_id": "fixture-task",
                    "description": "fixture",
                    "initial_prompt": "do a thing",
                    "success_criteria": [
                        {"type": "command_executed", "description": description,
                         "tool_name": "Bash", "command_pattern": pattern, "weight": 1.0}
                    ],
                },
                sort_keys=False,
            )
        )
        return path

    def test_would_have_caught_the_4574_clone_pattern(self, tmp_path):
        rc, out = _run(self._write(tmp_path, PR_4574_CLONE))
        assert rc == 1, out
        assert "backtrack catastrophically" in out
        assert "success_criteria[0]" in out

    def test_the_shipped_fix_passes(self, tmp_path):
        rc, out = _run(self._write(tmp_path, FIXED_CLONE))
        assert rc == 0, out
        assert "finish pumped probes" in out

    def test_line_continuation_overlap_is_caught(self, tmp_path):
        """`\\\\.` also matches `\\\\\\n` under DOTALL: the shape of every allowlisted entry."""
        pattern = r"(?=(?:[^&;|\r\n\\]|\\\r?\n|\\.)*--name\s+\S)uip\s+or\s+folders\s+list\b"
        rc, out = _run(self._write(tmp_path, pattern))
        assert rc == 1, out
        assert "backtrack catastrophically" in out

    def test_command_not_executed_is_probed_too(self, tmp_path):
        path = self._write(tmp_path, PR_4574_CLONE)
        path.write_text(path.read_text().replace("type: command_executed", "type: command_not_executed"))
        rc, out = _run(path)
        assert rc == 1, out

    def test_invalid_pattern_is_left_to_coder_eval(self, tmp_path):
        rc, out = _run(self._write(tmp_path, "uip (unclosed"))
        assert rc == 0, out

    def test_witness_reaches_the_pumped_loop(self):
        """The probe pumps right after the literal lead, where the clone loop starts."""
        leads = {probe.split("'a' ")[0] for probe in _load_gate()._probe_inputs(PR_4574_CLONE) if "'a' " in probe}
        assert "uip tm testcases clone" in leads

    def test_stale_allowlist_entry_fails(self, tmp_path, capsys):
        gate = _load_gate()
        path = self._write(tmp_path, FIXED_CLONE, description="now fixed")
        gate.SLOW_PATTERN_ALLOWLIST = frozenset({(gate._rel(path), "now fixed")})
        rc = gate.main([str(path)])
        out = capsys.readouterr().out
        assert rc == 1, out
        assert "now pass; remove them" in out

    def test_allowlisted_offender_passes(self, tmp_path, capsys):
        gate = _load_gate()
        path = self._write(tmp_path, PR_4574_CLONE, description="known slow")
        gate.SLOW_PATTERN_ALLOWLIST = frozenset({(gate._rel(path), "known slow")})
        rc = gate.main([str(path)])
        assert rc == 0, capsys.readouterr().out

    def test_every_allowlist_entry_names_a_live_criterion(self):
        """A renamed description or moved task must not leave a dead entry behind."""
        gate = _load_gate()
        for rel, description in gate.SLOW_PATTERN_ALLOWLIST:
            doc = yaml.safe_load((REPO_ROOT / rel).read_text())
            descriptions = [c.get("description") for c in doc.get("success_criteria", [])]
            assert descriptions.count(description) == 1, (rel, description)


def test_live_corpus_passes_every_gate():
    rc, out = _run(REPO_ROOT / "tests" / "tasks", REPO_ROOT / "tests" / "experiments")
    assert rc == 0, out
    assert "no task pins `sandbox.driver: tempdir`" in out
    assert "Windows-reachable hook command(s) are single-line" in out
    assert "stage a skill directory" not in out
    assert "finish pumped probes" in out
