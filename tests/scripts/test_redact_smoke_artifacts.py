"""Replay the smoke publication failure with dummy credentials only."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / ".github/scripts/redact-smoke-artifacts.py"
WORKFLOW = ROOT / ".github/workflows/smoke-skills.yml"
CODEX = "dummy-codex-credential-for-tests"
BEDROCK = "dummy-bedrock-credential-for-tests"
AUTH = "dummy-uipath-credential-for-tests"
SPEC = importlib.util.spec_from_file_location("redact_smoke_artifacts", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def run_scrub(root, key=CODEX):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        env={**os.environ, "CODEX_API_KEY": key,
             "AWS_BEARER_TOKEN_BEDROCK": BEDROCK, "UIPATH_CLI_AUTH_TOKEN": AUTH},
        capture_output=True, text=True,
    )


def test_scrubs_reports_and_arbitrary_artifact_bytes_preserving_gate_fields(tmp_path):
    task = tmp_path / "default/task/00"
    artifacts = task / "artifacts"
    artifacts.mkdir(parents=True)
    metadata = {
        "task_id": "task", "final_status": "ERROR", "iteration_count": 0,
        "llm_review": {"score": 0.6, "issues": "Needs a recheck"},
        "pre_run_results": [{"exit_code": 1, "stderr": "TENANT NOT READY"}],
        "success_criteria_results": [{"score": 0, "pass_threshold": 1}],
    }
    original = {**metadata, "iterations": [{"output": f"{CODEX} {BEDROCK} {AUTH}"}]}
    (task / "task.json").write_text(json.dumps(original))
    for name in ("task.html", "task.log"):
        (task / name).write_text(f"CODEX_API_KEY={CODEX}\n{BEDROCK}\n{AUTH}")
    for name in ("output.txt", "config.env", "no-extension", "payload.bin"):
        (artifacts / name).write_bytes(b"\xff\x00" + CODEX.encode() + b"\x80end")

    result = run_scrub(tmp_path)
    assert result.returncode == 0, result.stdout
    for path in tmp_path.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert not any(secret.encode() in data for secret in (CODEX, BEDROCK, AUTH))
            assert b"***" in data
    reduced = json.loads((task / "task.json").read_text())
    assert {key: reduced[key] for key in metadata} == metadata
    assert reduced["iterations"] == [{"output": "*** *** ***"}]
    assert (artifacts / "payload.bin").read_bytes() == b"\xff\x00***\x80end"


@pytest.mark.parametrize("kind", ["file-link", "directory-link", "fifo", "secret-name"])
def test_unsafe_paths_block_publication_without_printing_the_key(tmp_path, kind):
    root = tmp_path / "runs"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "secret.txt"
    target.write_text(CODEX)
    if kind == "file-link":
        (root / "link").symlink_to(target)
    elif kind == "directory-link":
        (root / "link").symlink_to(outside, target_is_directory=True)
    elif kind == "fifo":
        os.mkfifo(root / "pipe")
    else:
        (root / CODEX).write_text("ordinary text")
    result = run_scrub(root)
    assert result.returncode == 1
    assert result.stdout == "::error::Smoke artifact redaction failed; upload blocked\n"
    assert result.stderr == ""
    assert target.read_text() == CODEX


def test_read_error_fails_closed(tmp_path, monkeypatch, capsys):
    (tmp_path / "task.json").write_text("{}")
    monkeypatch.setenv("CODEX_API_KEY", CODEX)

    def unreadable(_):
        raise OSError(CODEX)

    monkeypatch.setattr(Path, "read_bytes", unreadable)
    assert MODULE.main([str(SCRIPT), str(tmp_path)]) == 1
    assert CODEX not in capsys.readouterr().out


def test_verification_rejects_a_write_that_did_not_redact(tmp_path, monkeypatch):
    (tmp_path / "task.log").write_text(CODEX)
    monkeypatch.setenv("CODEX_API_KEY", CODEX)
    monkeypatch.setattr(Path, "write_bytes", lambda *_: 0)
    assert MODULE.main([str(SCRIPT), str(tmp_path)]) == 1


def test_missing_codex_key_blocks_upload(tmp_path):
    (tmp_path / "task.log").write_text(CODEX)
    assert run_scrub(tmp_path, key="").returncode == 1


def test_workflow_only_uploads_after_successful_full_tree_scrub(tmp_path):
    steps = yaml.safe_load(WORKFLOW.read_text())["jobs"]["e2e"]["steps"]
    scrub = next(step for step in steps if step.get("id") == "scrub")
    uploads = [step for step in steps if "actions/upload-artifact@" in step.get("uses", "")]
    assert uploads
    assert scrub["env"]["CODEX_API_KEY"] == "${{ secrets.CODEX_API_KEY }}"
    assert scrub["env"]["AWS_BEARER_TOKEN_BEDROCK"] == "${{ secrets.AWS_BEARER_TOKEN_BEDROCK }}"
    assert not scrub.get("continue-on-error", False)
    assert scrub["run"] == "python3 .github/scripts/redact-smoke-artifacts.py /tmp/runs"
    for upload in uploads:
        assert steps.index(scrub) < steps.index(upload)
        assert upload["if"] == "always() && steps.scrub.outcome == 'success'"
        assert all(path.startswith("/tmp/runs/") for path in upload["with"]["path"].splitlines())

    # Execute the workflow's command with a failing input; its outcome cannot
    # satisfy the upload condition, even though the upload uses always().
    command = scrub["run"].replace("/tmp/runs", str(tmp_path / "missing"))
    result = subprocess.run(command, shell=True, cwd=ROOT,
                            env={**os.environ, "CODEX_API_KEY": CODEX}, capture_output=True)
    assert result.returncode != 0


def test_ci_runs_this_regression_suite():
    helpers = yaml.safe_load((ROOT / ".github/workflows/test-helpers.yml").read_text())
    steps = helpers["jobs"]["required-checks-contract"]["steps"]
    assert any("tests/scripts/test_redact_smoke_artifacts.py" in step.get("run", "") for step in steps)
