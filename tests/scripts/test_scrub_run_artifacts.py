"""scrub-run-artifacts.py publishes only allow-listed, token-free, structured results."""

from __future__ import annotations

import gzip
import importlib.util
import json
import os
import pathlib
import zipfile

import pytest

SPEC = importlib.util.spec_from_file_location(
    "scrub", pathlib.Path(__file__).resolve().parents[2] / ".github/scripts/scrub-run-artifacts.py"
)
scrub_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scrub_mod)

TOKEN = "eyJsynthetic.token.value-0123456789abcdefgh"
NASTY = 'cred"<&>\\/-0123456789abcdefghijklmnop'  # needs JSON and HTML escaping


def _task(task_id="t", status="SUCCESS", **extra):
    base = {
        "task_id": task_id, "variant_id": "default", "final_status": status, "weighted_score": 1.0,
        "duration_seconds": 3.5, "iteration_count": 1,
        "success_criteria_results": [
            {"result_kind": "x", "criterion_type": "run_command", "description": "checks <b>it</b>", "score": 1.0,
             "details": f"stdout: {NASTY}", "error": NASTY, "evaluation_status": "ok", "pass_threshold": 1.0, "gating": True}
        ],
        "iterations": [{"agent_output": NASTY, "messages": [{"text": NASTY}]}],
        "pre_run_results": [{"stdout": NASTY}],
        "error_message": NASTY,
    }
    base.update(extra)
    return base


def _env(tmp_path, monkeypatch, issued=(TOKEN,)):
    runner = tmp_path / "runner"
    runner.mkdir()
    (runner / "issued-tokens").write_text("\n".join(issued), encoding="utf-8")
    monkeypatch.setenv("RUNNER_TEMP", str(runner))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    run = tmp_path / "runs"
    run.mkdir()
    return run


def _put_task(run, name="t", rep="00", **kw):
    d = run / "default" / name / rep
    d.mkdir(parents=True)
    (d / "task.json").write_text(json.dumps(_task(name, **kw)), encoding="utf-8")
    (d / "task.html").write_text(f"<pre>{NASTY}</pre>", encoding="utf-8")
    (d / "task.log").write_text("log", encoding="utf-8")
    return d


def _names(run):
    return sorted(p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file())


def test_only_the_allow_list_survives(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    task = _put_task(run)
    for rel in ("run.json", "run.md", "experiment.json", "default/variant.json"):
        (run / rel).write_text("{}", encoding="utf-8")
    (task / "artifacts").mkdir()
    (task / "artifacts" / "task.json").write_text("{}", encoding="utf-8")
    (task / "artifacts" / "env.txt").write_text(TOKEN, encoding="utf-8")
    (task / "transcript.jsonl").write_text("{}", encoding="utf-8")
    (task.parent / "xx").mkdir()
    (task.parent / "xx" / "task.json").write_text("{}", encoding="utf-8")  # non-numeric replicate
    (run / "default" / "x").mkdir()
    (run / "default" / "x" / "task.json").write_text("{}", encoding="utf-8")  # wrong depth
    (run / "notes.txt").write_text("x", encoding="utf-8")
    assert scrub_mod.main(["x", str(run), "--expect-tasks", "1"]) == 0
    assert _names(run) == sorted(
        ["run.json", "run.md", "experiment.json", "default/variant.json"]
        + [f"default/t/00/{n}" for n in ("task.json", "task.log", "task.html")]
    )


def test_task_reports_are_rebuilt_from_structured_fields(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    task = _put_task(run)
    assert scrub_mod.main(["x", str(run)]) == 0
    published = json.loads((task / "task.json").read_text(encoding="utf-8"))
    page = (task / "task.html").read_text(encoding="utf-8")
    assert published["final_status"] == "SUCCESS" and published["success_criteria_results"][0]["score"] == 1.0
    assert set(published["success_criteria_results"][0]) == set(scrub_mod._CRITERION_FIELDS)
    for forbidden in ("iterations", "pre_run_results", "error_message"):
        assert forbidden not in published
    blob = json.dumps(published) + page
    for form in (NASTY, json.dumps(NASTY)[1:-1], __import__("html").escape(NASTY)):
        assert form not in blob
    assert "&lt;b&gt;it&lt;/b&gt;" in page and "checks <b>" not in page  # rendered escaped


def test_issued_and_env_secrets_are_replaced_in_kept_files(tmp_path, monkeypatch):
    old = "eyJolder.rotated.token-0123456789abcdefghij"
    run = _env(tmp_path, monkeypatch, issued=(old, TOKEN))
    monkeypatch.setenv("UIPATH_BOT_PASSWORD", "hunter2-password")
    (run / "run.md").write_text(f"{old} {TOKEN} hunter2-password", encoding="utf-8")
    task = _put_task(run, description_token=1)
    (task / "task.log").write_text(f"{TOKEN}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert (run / "run.md").read_text(encoding="utf-8") == "*** *** ***"
    assert (task / "task.log").read_text(encoding="utf-8") == "***"


def test_token_only_in_the_auth_file_is_replaced(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch, issued=("a" * 30,))
    auth = tmp_path / "home" / ".uipath"
    auth.mkdir(parents=True)
    refresh = "refresh-token-0123456789abcdefghijklmnop"
    (auth / ".auth").write_text(f"UIPATH_ACCESS_TOKEN={TOKEN}\nUIPATH_REFRESH_TOKEN={refresh}\n", encoding="utf-8")
    (run / "run.md").write_text(f"{TOKEN} {refresh}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert (run / "run.md").read_text(encoding="utf-8") == "*** ***"


def test_non_text_optional_files_are_withheld(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    with zipfile.ZipFile(run / "experiment.html", "w") as z:
        z.writestr("a", TOKEN)
    (run / "run.md").write_bytes(b"\xff" + TOKEN.encode())
    (run / "experiment.md").write_bytes(b"\xff\xfe" + TOKEN.encode("utf-16-le"))
    (run / "experiment.log").write_bytes(gzip.compress(TOKEN.encode()))
    assert scrub_mod.main(["x", str(run)]) == 0
    assert _names(run) == []


@pytest.mark.parametrize("name", ["run.json", "task.json"])
def test_unreadable_required_result_makes_the_run_incomplete(tmp_path, monkeypatch, name):
    run = _env(tmp_path, monkeypatch)
    task = _put_task(run)
    (run / "run.json").write_text("{}", encoding="utf-8")
    victim = run / name if name == "run.json" else task / name
    victim.write_bytes(gzip.compress(b"{}"))
    assert scrub_mod.main(["x", str(run), "--expect-tasks", "1"]) == 1
    assert _names(run) == []


def test_task_count_must_match_the_expected_count(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    _put_task(run, "a")
    assert scrub_mod.main(["x", str(run), "--expect-tasks", "2"]) == 1
    assert _names(run) == []
    second = tmp_path / "second"
    second.mkdir()
    run = _env(second, monkeypatch)
    _put_task(run, "a")
    _put_task(run, "b")
    assert scrub_mod.main(["x", str(run), "--expect-tasks", "2"]) == 0


def test_incomplete_task_record_fails_closed(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    task = _put_task(run)
    (task / "task.json").write_text("{}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 1


def test_symlinks_and_fifos_are_removed_unopened(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (tmp_path / "outside").mkdir()
    (run / "run.json").symlink_to(tmp_path / "outside")
    (run / "run.md").symlink_to(tmp_path / "nowhere")
    os.mkfifo(run / "experiment.json")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert _names(run) == [] and (tmp_path / "outside").is_dir() and not (run / "experiment.json").exists()


def test_error_wipes_everything_with_a_fixed_message(tmp_path, monkeypatch, capsys):
    run = _env(tmp_path, monkeypatch)
    (run / "run.json").write_text(TOKEN, encoding="utf-8")
    monkeypatch.setattr(scrub_mod, "scrub", lambda *_a: (_ for _ in ()).throw(OSError("disk /secret/path")))
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []
    out = capsys.readouterr().out
    assert TOKEN not in out and "/secret/path" not in out and "withheld" in out


def test_wipe_is_best_effort_and_still_prints_the_fixed_message(tmp_path, monkeypatch, capsys):
    run = _env(tmp_path, monkeypatch)
    (run / "run.json").write_text(TOKEN, encoding="utf-8")
    monkeypatch.setattr(scrub_mod, "scrub", lambda *_a: (_ for _ in ()).throw(OSError("x")))
    real = pathlib.Path.unlink

    def deny(self, *a, **k):
        raise PermissionError(str(self))

    monkeypatch.setattr(pathlib.Path, "unlink", deny)
    assert scrub_mod.main(["x", str(run)]) == 1
    monkeypatch.setattr(pathlib.Path, "unlink", real)
    assert "withheld" in capsys.readouterr().out


def test_survivor_is_caught_by_the_verify_pass(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (run / "run.md").write_text(TOKEN, encoding="utf-8")
    monkeypatch.setattr(pathlib.Path, "write_bytes", lambda self, data: len(data))
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []


@pytest.mark.parametrize("issued", [None, "", "\n"])
def test_ci_without_an_issued_token_fails_closed(tmp_path, monkeypatch, issued):
    run = _env(tmp_path, monkeypatch, issued=())
    record = pathlib.Path(os.environ["RUNNER_TEMP"]) / "issued-tokens"
    record.unlink() if issued is None else record.write_text(issued, encoding="utf-8")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    (run / "run.md").write_text("x", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []


def test_publication_disabled_flag_fails_closed(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    (pathlib.Path(os.environ["RUNNER_TEMP"]) / "publication-disabled").write_text("", encoding="utf-8")
    (run / "run.md").write_text("x", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []
