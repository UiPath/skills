"""scrub-run-artifacts.py publishes only allow-listed, token-free result files."""

from __future__ import annotations

import gzip
import os
import pathlib
import importlib.util
import zipfile

SPEC = importlib.util.spec_from_file_location(
    "scrub", pathlib.Path(__file__).resolve().parents[2] / ".github/scripts/scrub-run-artifacts.py"
)
scrub_mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scrub_mod)

TOKEN = "eyJsynthetic.token.value-0123456789abcdefgh"


def _env(tmp_path, monkeypatch, issued=(TOKEN,)):
    runner = tmp_path / "runner"
    runner.mkdir()
    (runner / "issued-tokens").write_text("\n".join(issued), encoding="utf-8")
    monkeypatch.setenv("RUNNER_TEMP", str(runner))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    run = tmp_path / "runs"
    (run / "variant" / "task" / "01" / "artifacts").mkdir(parents=True)
    return run


def _names(run):
    return sorted(p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file())


def test_only_the_allow_list_survives(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    task = run / "variant" / "task" / "01"
    for rel in ("run.json", "run.md", "experiment.json", "variant/variant.json"):
        (run / rel).write_text("{}", encoding="utf-8")
    for name in ("task.json", "task.log", "task.html"):
        (task / name).write_text("ok", encoding="utf-8")
    (task / "artifacts" / "env.txt").write_text(f"dump {TOKEN}", encoding="utf-8")
    (task / "transcript.jsonl").write_text("{}", encoding="utf-8")
    (run / "notes.txt").write_text("x", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert _names(run) == sorted(
        ["run.json", "run.md", "experiment.json", "variant/variant.json"]
        + [f"variant/task/01/{n}" for n in ("task.json", "task.log", "task.html")]
    )


def test_issued_and_env_secrets_are_replaced_in_kept_files(tmp_path, monkeypatch):
    old = "eyJolder.rotated.token-0123456789abcdefghij"
    run = _env(tmp_path, monkeypatch, issued=(old, TOKEN))
    monkeypatch.setenv("UIPATH_BOT_PASSWORD", "hunter2-password")
    (run / "run.md").write_text(f"{old} {TOKEN} hunter2-password", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert (run / "run.md").read_text(encoding="utf-8") == "*** *** ***"


def test_token_only_in_the_auth_file_is_replaced(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch, issued=("a" * 30,))
    auth = tmp_path / "home" / ".uipath"
    auth.mkdir(parents=True)
    refresh = "refresh-token-0123456789abcdefghijklmnop"
    (auth / ".auth").write_text(f"UIPATH_ACCESS_TOKEN={TOKEN}\nUIPATH_REFRESH_TOKEN={refresh}\n", encoding="utf-8")
    (run / "run.md").write_text(f"{TOKEN} {refresh}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert (run / "run.md").read_text(encoding="utf-8") == "*** ***"


def test_non_text_allowed_names_are_withheld(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (run / "run.json").write_bytes(gzip.compress(TOKEN.encode()))
    with zipfile.ZipFile(run / "experiment.html", "w") as z:
        z.writestr("a", TOKEN)
    (run / "run.md").write_bytes(b"\xff" + TOKEN.encode())
    (run / "experiment.md").write_bytes(b"\xff\xfe" + TOKEN.encode("utf-16-le"))
    assert scrub_mod.main(["x", str(run)]) == 0
    assert _names(run) == []


def test_symlinks_are_withheld(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (tmp_path / "outside").mkdir()
    (run / "run.json").symlink_to(tmp_path / "outside")
    (run / "run.md").symlink_to(tmp_path / "nowhere")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert _names(run) == [] and (tmp_path / "outside").is_dir()


def test_error_wipes_everything_with_a_fixed_message(tmp_path, monkeypatch, capsys):
    run = _env(tmp_path, monkeypatch)
    (run / "run.json").write_text(TOKEN, encoding="utf-8")
    monkeypatch.setattr(scrub_mod, "scrub", lambda *_a: (_ for _ in ()).throw(OSError("disk")))
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []
    out = capsys.readouterr().out
    assert TOKEN not in out and "withheld" in out


def test_survivor_is_caught_by_the_verify_pass(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (run / "run.json").write_text(TOKEN, encoding="utf-8")
    monkeypatch.setattr(pathlib.Path, "write_bytes", lambda self, data: len(data))
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []


def test_ci_without_an_issued_tokens_record_fails_closed(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (pathlib.Path(os.environ["RUNNER_TEMP"]) / "issued-tokens").unlink()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    (run / "run.json").write_text("{}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []


def test_empty_issued_tokens_record_fails_closed_in_ci(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch, issued=())
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert scrub_mod.main(["x", str(run)]) == 1


def test_fifo_is_removed_not_opened(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    os.mkfifo(run / "run.json")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert _names(run) == [] and not (run / "run.json").exists()
