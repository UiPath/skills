"""run-coder-eval.yml: nothing reads or publishes the run dir unless the scrub succeeded."""

from __future__ import annotations

import pathlib
import re
import subprocess

import yaml

WORKFLOW = pathlib.Path(__file__).resolve().parents[2] / ".github/workflows/run-coder-eval.yml"
# Steps after the scrub that touch no run data (only timestamps from the refresher log).
UNGATED = {"Report auth refresher status"}


def _linux_steps():
    jobs = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]
    for job in jobs.values():
        steps = job.get("steps", [])
        if any(s.get("id") == "scrub" for s in steps):
            return steps
    raise AssertionError("no job has a step with id: scrub")


def _after_scrub():
    steps = _linux_steps()
    index = next(i for i, s in enumerate(steps) if s.get("id") == "scrub")
    return steps[index], steps[index + 1 :]


def test_every_always_step_after_the_scrub_requires_its_success():
    _, after = _after_scrub()
    assert after, "expected publishing steps after the scrub"
    for step in after:
        condition = str(step.get("if", ""))
        if step.get("name") in UNGATED or not re.search(r"always\(\)|failure\(\)|cancelled\(\)", condition):
            continue  # no status function: GitHub adds success(), so it skips after a failed scrub
        gated = "steps.scrub.outcome == 'success'" in condition
        # The verdict step must run (to fail the job) but reads the dir only after checking the outcome.
        checks_outcome = step.get("env", {}).get("SCRUB_OUTCOME") == "${{ steps.scrub.outcome }}" and (
            '"$SCRUB_OUTCOME" != "success"' in step.get("run", "")
        )
        assert gated or checks_outcome, f"{step.get('name')!r} runs after the scrub without requiring its success"


def test_the_verdict_step_emits_a_fixed_message_when_the_scrub_failed():
    _, after = _after_scrub()
    (verdict,) = [s for s in after if s.get("name") == "Plaintext summary + verdict"]
    run = verdict["run"]
    guard = run.index('if [ "$SCRUB_OUTCOME" != "success" ]')
    assert guard < run.index("python"), "the outcome check must precede anything that reads /tmp/runs"
    assert "withheld" in run[guard : guard + 200] and "exit 1" in run[guard : guard + 200]
    assert "rows and ok == len(rows)" in run  # coverage of every scheduled task is the scrub's job
    assert "TASK_COUNT" not in run and ">=" not in run


def test_the_scrub_stops_the_refresher_and_checks_the_task_identities():
    scrub, _ = _after_scrub()
    run = scrub["run"]
    assert run.index("auth-refresher.pid") < run.index("scrub-run-artifacts.py")
    assert 'kill -- "-$pid"' in run  # the whole refresher group, including an in-flight rotation
    assert '--expect-ids "$TASK_IDS"' in run


def test_the_eval_does_not_stream_verbose_output_to_the_live_log():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.search(r'args\+=\(-j "\$j" --model "\$model"\)', text)
    assert not re.search(r'args\+=\(-j "\$j" -v\b', text)


def test_the_scrub_step_survives_a_missing_refresher_pid_file(tmp_path):
    """GitHub runs steps as `bash -e`; no setsid means no pid file, and the scrub must still run."""
    scrub, _ = _after_scrub()
    prelude = scrub["run"].split("python3 ")[0] + "echo reached-scrub\n"
    result = subprocess.run(
        ["bash", "-e", "-c", prelude], env={"RUNNER_TEMP": str(tmp_path), "PATH": "/usr/bin:/bin"},
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0 and "reached-scrub" in result.stdout, result.stderr


def test_the_refresher_exits_when_its_lease_is_gone(tmp_path):
    import os
    import subprocess
    import time

    run = next(s["run"] for s in _linux_steps() if "auth-refresher.sh" in s.get("run", "") and "REFRESH" in s.get("run", ""))
    body = run.split("<<'REFRESH'\n", 1)[1].split("\nREFRESH", 1)[0]
    script = tmp_path / "refresher.sh"
    script.write_text(body)
    (tmp_path / ".github/scripts").mkdir(parents=True)
    (tmp_path / ".github/scripts/rotate-auth.sh").write_text(f"touch {tmp_path}/rotated\n")
    env = {**os.environ, "RUNNER_TEMP": str(tmp_path), "AUTH_REFRESH_INTERVAL_S": "1"}
    proc = subprocess.Popen(["bash", str(script)], cwd=tmp_path, env=env)
    try:
        pid_file = tmp_path / "auth-refresher.pid"
        for _ in range(50):
            if pid_file.exists():
                break
            time.sleep(0.1)
        assert pid_file.read_text().strip() == str(proc.pid)
        pid_file.unlink()
        assert proc.wait(timeout=10) == 0, "refresher must exit once its pid-file lease is gone"
        assert not (tmp_path / "rotated").exists(), "refresher must not rotate after losing its lease"
    finally:
        proc.kill()
        proc.wait()


def test_the_partition_resolves_result_ids_with_the_dataset_expander():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'expected-task-ids.py "${LINUX[@]}"' in text
    assert "id*" not in text
