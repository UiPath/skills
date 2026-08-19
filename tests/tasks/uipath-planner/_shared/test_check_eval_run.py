"""Guards for scripts/check-eval-run.py — the run-is-evidence gate.

The gate exists because a coder-eval run can finish with plausible scores while
measuring nothing. These tests build synthetic run directories for each failure
mode, so the gate is verified in both directions without needing a real run.

The signal choices encoded here were learned the hard way:

* Execution is measured by **output tokens**, not turn count. `codex` reports
  `total_assistant_turns == 1` on fully successful runs and `2` on runs that died
  on a provider error, so a turn threshold is near-inverted for it.
* `--regrade` drops the agent assertions, because `coder-eval evaluate` runs no
  agent — asserting plugins/tokens there would fail every re-grade, which is the
  cheapest and most useful path.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
GATE = REPO / "scripts" / "check-eval-run.py"

GOOD_USAGE = {"output_tokens": 12882, "input_tokens": 2010930}


def write_run(root: Path, *, task: dict, experiment: str | None = "skill-tests-default") -> Path:
    run = root / "run"
    rep = run / "default" / "some-task" / "00"
    rep.mkdir(parents=True)
    (rep / "task.json").write_text(json.dumps(task), encoding="utf-8")
    if experiment is not None:
        (run / "experiment.md").write_text(
            f"# Experiment Report: {experiment}\n", encoding="utf-8"
        )
    return run


def gate(run: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), str(run), *extra], capture_output=True, text=True
    )


def base_task(**over) -> dict:
    task = {
        "agent_type": "codex",
        "final_status": "SUCCESS",
        "total_assistant_turns": 1,  # healthy for codex — deliberately low
        "agent_config": {"plugins": [{"type": "local", "path": "$SKILLS_REPO_PATH"}]},
        "total_token_usage": dict(GOOD_USAGE),
        "success_criteria_results": [{"score": 1.0, "details": "ok"}],
    }
    task.update(over)
    return task


def test_gate_exists():
    assert GATE.is_file(), f"missing {GATE}"


def test_healthy_run_passes_even_with_one_turn(tmp_path: Path):
    """A codex run with a single assistant turn is normal, not broken."""
    run = write_run(tmp_path, task=base_task())
    r = gate(run, "--expect-experiment", "skill-tests-default")
    assert r.returncode == 0, f"healthy run rejected:\n{r.stdout}\n{r.stderr}"


def test_missing_plugin_fails(tmp_path: Path):
    run = write_run(tmp_path, task=base_task(agent_config={"plugins": None}))
    r = gate(run)
    assert r.returncode != 0
    assert "no plugin loaded" in (r.stdout + r.stderr)


def test_no_output_tokens_fails(tmp_path: Path):
    """The provider-error shape: task.json exists, usage is empty."""
    run = write_run(tmp_path, task=base_task(total_token_usage={}, total_assistant_turns=2))
    r = gate(run)
    assert r.returncode != 0
    assert "produced no output" in (r.stdout + r.stderr)


def test_wrong_experiment_fails(tmp_path: Path):
    run = write_run(tmp_path, task=base_task(), experiment="default")
    r = gate(run, "--expect-experiment", "skill-tests-default")
    assert r.returncode != 0
    assert "expected" in (r.stdout + r.stderr)


def test_unconfigured_judge_fails(tmp_path: Path):
    run = write_run(tmp_path, task=base_task(
        success_criteria_results=[{"score": 0.0, "details": "(judge transport unconfigured)"}]
    ))
    r = gate(run)
    assert r.returncode != 0
    assert "judge transport" in (r.stdout + r.stderr)


def test_regrade_mode_ignores_agent_assertions(tmp_path: Path):
    """`coder-eval evaluate` produces no plugin, no tokens and no experiment.md.
    Those are expected in that mode, so --regrade must not flag them."""
    run = write_run(
        tmp_path,
        task={"success_criteria_results": [{"score": 1.0, "details": "ok"}]},
        experiment=None,
    )
    r = gate(run, "--regrade")
    assert r.returncode == 0, f"--regrade flagged a normal re-grade:\n{r.stdout}\n{r.stderr}"


def test_regrade_mode_still_catches_the_judge(tmp_path: Path):
    """--regrade relaxes the agent checks but must keep the judge check, or the
    cheap path becomes the one where a transport gap hides."""
    run = write_run(
        tmp_path,
        task={"success_criteria_results": [
            {"score": 0.0, "details": "(judge transport unconfigured)"}
        ]},
        experiment=None,
    )
    r = gate(run, "--regrade")
    assert r.returncode != 0
    assert "judge transport" in (r.stdout + r.stderr)


def test_empty_run_dir_fails(tmp_path: Path):
    run = tmp_path / "empty"
    run.mkdir()
    r = gate(run)
    assert r.returncode != 0
    assert "no task.json" in (r.stdout + r.stderr)
