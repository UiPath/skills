"""Regression tests for the two static gates in scripts/check-task-driver.py.

Gate 1 (no `sandbox.driver: tempdir`) predates these tests and was previously
unguarded; it is pinned here alongside the new one.

Gate 2 (Windows-reachable commands must be cmd.exe-safe) exists because of the
2026-09-04 outage: a multi-line POSIX `sh` `pre_run` hook landed in
`tests/experiments/nightly.yaml` (skills #2756, commit 80c757e03) and cmd.exe
rejected it before evaluating anything, taking the whole Windows nightly split
to `7/7 status=ERROR score=0.000 iterations=0`. skills #3116 fixed the hook.
Nothing caught it, because nothing connected "this experiment runs on Windows"
to "therefore its commands must be cmd-safe".

`test_would_have_caught_the_2026_09_04_outage` is the point of this file: it
feeds the real historical command back through the gate and asserts it fails.

Run from repo root:
    pytest tests/scripts/test_check_task_driver.py
"""

import importlib.util
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gate = _load("check_task_driver", REPO_ROOT / "scripts" / "check-task-driver.py")


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

_EXPERIMENT_TEMPLATE = textwrap.dedent(
    """\
    experiment_id: test-experiment
    description: "fixture"
    defaults:
    {hooks}
    variants:
      - variant_id: default
    """
)


def _write_experiment(tmp_path: Path, name: str, hooks: str) -> Path:
    path = tmp_path / name
    path.write_text(_EXPERIMENT_TEMPLATE.format(hooks=textwrap.indent(hooks, "  ")))
    return path


_TASK_TEMPLATE = textwrap.dedent(
    """\
    task_id: {task_id}
    description: "fixture"
    initial_prompt: "do a thing"
    tags: {tags!r}
    {body}
    """
)


def _write_task(tmp_path: Path, name: str, tags: list[str], body: str) -> Path:
    """``body`` is raw YAML appended at the document root (criteria, hooks, ...)."""
    path = tmp_path / name
    path.write_text(
        _TASK_TEMPLATE.format(task_id=f"fixture-{name.replace('.yaml', '')}", tags=tags, body=body)
    )
    return path


_POSIX_CRITERION = textwrap.dedent(
    """\
    success_criteria:
      - type: run_command
        description: "check"
        command: "grep -q 'Foo' out.txt"
        weight: 1.0
    """
)


def _run(*paths: Path) -> tuple[int, str]:
    """Run the gate as the workflow does, returning (exit code, combined output)."""
    proc = subprocess.run(
        ["python3", str(REPO_ROOT / "scripts" / "check-task-driver.py"), *map(str, paths)],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout + proc.stderr


# --------------------------------------------------------------------------
# The regression that motivated the gate
# --------------------------------------------------------------------------


class TestWouldHaveCaughtTheOutage:
    def test_would_have_caught_the_2026_09_04_outage(self, tmp_path):
        """The real broken hook, run through the real gate, must fail it.

        `nightly.yaml` is classified windows-reachable, so a POSIX `pre_run`
        there is exactly the shape that ERRORed all 7 Windows tasks at setup.
        """
        path = _write_experiment(
            tmp_path,
            "nightly.yaml",
            f'pre_run:\n  - command: |-\n{textwrap.indent(BROKEN_HOOK, "      ")}\n    timeout: 30\n',
        )
        rc, out = _run(path)
        assert rc == 1, out
        assert "not cmd.exe-safe" in out
        assert "defaults.pre_run[0].command" in out

    def test_multi_line_is_the_first_reported_reason(self):
        """cmd parses line 1 only, so the block scalar alone condemns the hook."""
        problems = gate.cmd_safety_problems(BROKEN_HOOK)
        assert problems == ["multi-line (cmd parses the first line only)"]

    def test_single_line_variant_still_fails_on_constructs(self):
        """Un-wrapping it is not enough: `[`, `${...}`, `;` and bash all remain."""
        one_line = " ".join(line.strip() for line in BROKEN_HOOK.splitlines())
        problems = gate.cmd_safety_problems(one_line)
        assert problems, "single-line POSIX sh must still be rejected"
        # `${MAESTRO_FLOW_SDK_SETUP:-0}` sits inside cmd double quotes and is
        # therefore masked, exactly as cmd would treat it. What remains unquoted
        # is what actually broke: `[`, `;`, `then`/`fi`, and the `bash` call.
        assert {"test-or-bracket", "semicolon-separator", "sh-keyword", "posix-tool"} <= set(problems)

    def test_the_shipped_fix_passes(self, tmp_path):
        """#3116's `:;`-prefixed one-liner is what the gate is steering authors to."""
        assert gate.cmd_safety_problems(FIXED_HOOK) == []
        path = _write_experiment(
            tmp_path, "nightly.yaml", f"pre_run:\n  - command: {FIXED_HOOK!r}\n    timeout: 30\n"
        )
        rc, out = _run(path)
        assert rc == 0, out

    def test_known_hole_powershell_payload_is_not_inspected(self):
        """Documents what this gate does NOT catch.

        coder_eval_uipath PR #115 translated the hook into PowerShell, which is
        cmd-dispatchable and so passes here. It still would not have worked: the
        payload ends in `bash <script>`, and on the ADO Windows image `bash` is
        the WSL launcher, which exits 1 with "no installed distributions".

        The gate checks cmd *parseability*, not whether the tools inside a
        quoted payload exist on the runner. That is a runtime property no static
        check can see, and pretending otherwise would mean flagging every
        legitimate `pwsh -Command "..."` and `python -c "..."` in the corpus.
        Recorded here so the limitation is a known decision, not a surprise.
        """
        naive = (
            'pwsh -NoProfile -Command "if ($env:MAESTRO_FLOW_SDK_SETUP -eq 1) '
            "{ bash $env:SKILLS_REPO_PATH/tests/scripts/stage-preview-sdk-workspace.sh }\""
        )
        assert gate.cmd_safety_problems(naive) == []

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
        import yaml

        blob = subprocess.run(
            ["git", "show", "80c757e03:tests/experiments/nightly.yaml"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        historical = yaml.safe_load(blob)["defaults"]["pre_run"][0]["command"]
        assert historical == BROKEN_HOOK


# --------------------------------------------------------------------------
# Gate 2 scope and correctness
# --------------------------------------------------------------------------


class TestCmdSafetyScope:
    def test_windows_tagged_task_with_posix_criterion_fails(self, tmp_path):
        path = _write_task(tmp_path, "win.yaml", ["uipath-rpa", "windows"], _POSIX_CRITERION)
        rc, out = _run(path)
        assert rc == 1, out
        assert "success_criteria[0].command" in out

    def test_same_criterion_on_a_linux_task_passes(self, tmp_path):
        """Scope is deliberate: the ~440 POSIX criteria on Linux tasks are fine."""
        path = _write_task(tmp_path, "linux.yaml", ["uipath-rpa"], _POSIX_CRITERION)
        rc, out = _run(path)
        assert rc == 0, out

    def test_task_level_hook_on_a_windows_task_is_checked(self, tmp_path):
        """A task can carry its own post_run alongside the experiment's."""
        body = textwrap.dedent(
            """\
            post_run:
              - command: "rm -rf build"
                timeout: 30
            success_criteria:
              - type: file_exists
                description: "exists"
                path: out.txt
                weight: 1.0
            """
        )
        path = _write_task(tmp_path, "win_hook.yaml", ["uipath-rpa", "windows"], body)
        rc, out = _run(path)
        assert rc == 1, out
        assert "post_run[0].command" in out

    def test_linux_only_experiment_hooks_are_not_checked(self, tmp_path):
        path = _write_experiment(
            tmp_path, "default.yaml", 'post_run:\n  - command: "rm -rf node_modules"\n    timeout: 30\n'
        )
        rc, out = _run(path)
        assert rc == 0, out


class TestQuoteAwareness:
    """cmd has one quote char and treats the quoted run as literal, so a
    `python -c "..."` payload full of sh metacharacters is genuinely safe. All
    four Windows-tagged `run_command` criteria in the live corpus are this
    shape; a naive scan flags every one of them."""

    def test_double_quoted_payload_is_safe(self):
        cmd = (
            'python -c "import sys; s=open(\'Main.xaml\',encoding=\'utf-8\').read(); '
            "sys.exit(0 if 'TryCatch' in s else 1)\""
        )
        assert gate.cmd_safety_problems(cmd) == []

    def test_unquoted_equivalents_are_not_safe(self):
        assert "single-quote" in gate.cmd_safety_problems("python -c 'print(1)'")
        assert "posix-tool" in gate.cmd_safety_problems("grep -q Foo out.txt")
        assert "sh-variable" in gate.cmd_safety_problems("test -d $HOME/x")
        assert "command-substitution" in gate.cmd_safety_problems("WF=$(find . -name x)")
        assert "dev-null" in gate.cmd_safety_problems("uip login status 2>/dev/null")

    def test_and_or_are_portable(self):
        """`&&` and `||` work in cmd; flagging them would be a false positive."""
        assert gate.cmd_safety_problems("uip rpa build && uip rpa validate") == []

    def test_native_powershell_passes(self):
        cmd = 'pwsh -NoLogo -NoProfile -NonInteractive -Command "Remove-Item -Force x"'
        assert gate.cmd_safety_problems(cmd) == []


# --------------------------------------------------------------------------
# Fail-closed properties
# --------------------------------------------------------------------------


class TestFailsClosed:
    def test_unclassified_experiment_fails(self, tmp_path):
        """A new experiment must be classified before it can merge.

        This is the missing link the outage exposed: authoring a hook and
        knowing whether it can reach a Windows runner were unconnected.
        """
        path = _write_experiment(
            tmp_path, "brand-new.yaml", 'post_run:\n  - command: "echo hi"\n    timeout: 30\n'
        )
        rc, out = _run(path)
        assert rc == 1, out
        assert "_EXPERIMENT_PLATFORM" in out

    def test_every_live_experiment_is_classified(self):
        exp = REPO_ROOT / "tests" / "experiments"
        live = {p.name for p in [*exp.glob("*.yaml"), *exp.glob("*.yml")]}
        assert live <= set(gate._EXPERIMENT_PLATFORM), (
            f"unclassified: {sorted(live - set(gate._EXPERIMENT_PLATFORM))}"
        )

    def test_overlay_exemption_is_exact_match(self, tmp_path):
        """Drifting the overlaid command must fail here AND in the overlay.

        prepare_windows_experiment.py raises on `len(matches) != 1`, so a change
        to nightly's cleanup breaks both checks rather than silently aging one
        of them out.
        """
        exact = gate._OVERLAY_TRANSLATED[("nightly.yaml", "defaults.post_run[0].command")]
        assert gate.cmd_safety_problems(exact), "the exempted command is POSIX, hence the exemption"

        drifted = exact.replace("-maxdepth 5", "-maxdepth 6")
        path = _write_experiment(
            tmp_path, "nightly.yaml", f"post_run:\n  - command: {drifted!r}\n    timeout: 30\n"
        )
        rc, out = _run(path)
        assert rc == 1, out

    def test_exemption_still_applies_to_the_live_file(self):
        """The pinned string must stay in sync with nightly.yaml itself."""
        import yaml

        doc = yaml.safe_load((REPO_ROOT / "tests" / "experiments" / "nightly.yaml").read_text())
        live = doc["defaults"]["post_run"][0]["command"]
        assert live == gate._OVERLAY_TRANSLATED[("nightly.yaml", "defaults.post_run[0].command")]


# --------------------------------------------------------------------------
# Gate 1, previously unguarded
# --------------------------------------------------------------------------


class TestDriverGate:
    def test_tempdir_pin_fails(self, tmp_path):
        path = tmp_path / "pinned.yaml"
        path.write_text(
            textwrap.dedent(
                """\
                task_id: fixture-pinned
                description: "fixture"
                initial_prompt: "do a thing"
                sandbox:
                  driver: tempdir
                success_criteria:
                  - type: file_exists
                    description: "exists"
                    path: out.txt
                    weight: 1.0
                """
            )
        )
        rc, out = _run(path)
        assert rc == 1, out
        assert "sandbox.driver: tempdir" in out
        assert f"{path.name}:5" in out or ",line=5" in out

    def test_docker_pin_is_a_note_not_a_failure(self, tmp_path):
        path = tmp_path / "docker.yaml"
        path.write_text(
            textwrap.dedent(
                """\
                task_id: fixture-docker
                description: "fixture"
                initial_prompt: "do a thing"
                sandbox:
                  driver: docker
                success_criteria:
                  - type: file_exists
                    description: "exists"
                    path: out.txt
                    weight: 1.0
                """
            )
        )
        rc, out = _run(path)
        assert rc == 0, out
        assert "redundant with the Linux default" in out


# --------------------------------------------------------------------------
# The live corpus
# --------------------------------------------------------------------------


def test_live_corpus_passes_both_gates():
    rc, out = _run(REPO_ROOT / "tests" / "tasks", REPO_ROOT / "tests" / "experiments")
    assert rc == 0, out
    assert "no task pins `sandbox.driver: tempdir`" in out
    assert "are cmd.exe-safe" in out
