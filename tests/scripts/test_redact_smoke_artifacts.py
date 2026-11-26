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
ACCESS = "dummy-uipath-access-token-for-tests"
REFRESH = "dummy-uipath-refresh-token-for-tests"
SECRETS = (CODEX, BEDROCK, ACCESS, REFRESH)
SPEC = importlib.util.spec_from_file_location("redact_smoke_artifacts", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def write_auth(home, text=None):
    # The format refresh-auth.sh writes; tenant slugs must survive the scrub.
    if text is None:
        text = (f"UIPATH_ACCESS_TOKEN={ACCESS}\nUIPATH_REFRESH_TOKEN={REFRESH}\n"
                "UIPATH_URL=https://alpha.uipath.com\nUIPATH_TENANT_NAME=DefaultTenant\n")
    (home / ".uipath").mkdir(parents=True, exist_ok=True)
    (home / ".uipath/.auth").write_text(text)
    return home


def run_scrub(root, key=CODEX, home=None):
    if home is None:
        home = write_auth(root.parent / f"{root.name}-home")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root)],
        env={**os.environ, "HOME": str(home), "CODEX_API_KEY": key,
             "AWS_BEARER_TOKEN_BEDROCK": BEDROCK},
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
    output = f"{CODEX} {BEDROCK} {ACCESS} {REFRESH}"
    original = {**metadata, "iterations": [{"output": output}]}
    (task / "task.json").write_text(json.dumps(original))
    for name in ("task.html", "task.log"):
        # An agent that runs `cat /.uipath/.auth` logs both UiPath tokens.
        (task / name).write_text(f"CODEX_API_KEY={CODEX}\n{BEDROCK}\n"
                                 f"UIPATH_ACCESS_TOKEN={ACCESS}\nUIPATH_REFRESH_TOKEN={REFRESH}\n"
                                 "UIPATH_TENANT_NAME=DefaultTenant")
    for name in ("output.txt", "config.env", "no-extension", "payload.bin"):
        (artifacts / name).write_bytes(b"\xff\x00" + CODEX.encode() + b"\x80end")

    result = run_scrub(tmp_path)
    assert result.returncode == 0, result.stdout
    for path in tmp_path.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert not any(secret.encode() in data for secret in SECRETS)
            assert b"***" in data
    reduced = json.loads((task / "task.json").read_text())
    assert {key: reduced[key] for key in metadata} == metadata
    assert reduced["iterations"] == [{"output": "*** *** *** ***"}]
    assert (task / "task.log").read_text().endswith(
        "UIPATH_REFRESH_TOKEN=***\nUIPATH_TENANT_NAME=DefaultTenant")
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
    monkeypatch.setenv("HOME", str(write_auth(tmp_path.parent / f"{tmp_path.name}-home")))

    def unreadable(_):
        raise OSError(CODEX)

    monkeypatch.setattr(Path, "read_bytes", unreadable)
    assert MODULE.main([str(SCRIPT), str(tmp_path)]) == 1
    assert CODEX not in capsys.readouterr().out


def test_verification_rejects_a_write_that_did_not_redact(tmp_path, monkeypatch):
    (tmp_path / "task.log").write_text(CODEX)
    monkeypatch.setenv("CODEX_API_KEY", CODEX)
    monkeypatch.setenv("HOME", str(write_auth(tmp_path.parent / f"{tmp_path.name}-home")))
    monkeypatch.setattr(Path, "write_bytes", lambda *_: 0)
    assert MODULE.main([str(SCRIPT), str(tmp_path)]) == 1


def test_missing_codex_key_blocks_upload(tmp_path):
    (tmp_path / "task.log").write_text(CODEX)
    assert run_scrub(tmp_path, key="").returncode == 1


@pytest.mark.parametrize("auth, message", [
    (None, "missing or unreadable"),
    ("UIPATH_TENANT_NAME=DefaultTenant\n", "has no access token"),
    ("UIPATH_ACCESS_TOKEN=\nUIPATH_REFRESH_TOKEN=null\n", "has no access token"),
    (b"UIPATH_ACCESS_TOKEN=\xff\xfe", "missing or unreadable"),
])
def test_unusable_auth_file_blocks_upload_without_printing_tokens(tmp_path, auth, message):
    root = tmp_path / "runs"
    root.mkdir()
    (root / "task.log").write_text(f"{ACCESS} {REFRESH}")
    home = tmp_path / "home"
    home.mkdir()
    if isinstance(auth, bytes):
        (home / ".uipath").mkdir()
        (home / ".uipath/.auth").write_bytes(auth)
    elif auth is not None:
        write_auth(home, auth)
    result = run_scrub(root, home=home)
    assert result.returncode == 1
    assert result.stdout == f"::error::UiPath auth file ~/.uipath/.auth {message}; upload blocked\n"
    assert result.stderr == ""
    assert (root / "task.log").read_text() == f"{ACCESS} {REFRESH}"


def test_absent_refresh_token_redacts_access_token_and_keeps_null_text(tmp_path):
    root = tmp_path / "runs"
    root.mkdir()
    (root / "task.json").write_text(json.dumps({"output": ACCESS, "score": None}))
    home = write_auth(tmp_path / "home", f"UIPATH_ACCESS_TOKEN={ACCESS}\nUIPATH_REFRESH_TOKEN=null\n")
    assert run_scrub(root, home=home).returncode == 0
    assert json.loads((root / "task.json").read_text()) == {"output": "***", "score": None}


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
    home = write_auth(tmp_path / "home")
    result = subprocess.run(command, shell=True, cwd=ROOT, capture_output=True,
                            env={**os.environ, "HOME": str(home), "CODEX_API_KEY": CODEX})
    assert result.returncode != 0

    # The scrub reads the tokens from the file the mint writes and every sandbox
    # mounts; moving either one must break this test, not leak the tokens.
    mint = next(step for step in steps if "refresh-auth.sh" in step.get("run", ""))
    assert steps.index(mint) < steps.index(scrub)
    assert "AUTH_FILE" not in mint.get("env", {}) and "HOME" not in scrub["env"]
    smoke = yaml.safe_load((ROOT / "tests/experiments/smoke.yaml").read_text())
    assert "~/.uipath:/.uipath:rw" in smoke["defaults"]["sandbox"]["docker"]["extra_mounts"]


def test_ci_runs_this_regression_suite():
    helpers = yaml.safe_load((ROOT / ".github/workflows/test-helpers.yml").read_text())
    steps = helpers["jobs"]["required-checks-contract"]["steps"]
    assert any("tests/scripts/test_redact_smoke_artifacts.py" in step.get("run", "") for step in steps)
