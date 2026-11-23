"""scrub-run-artifacts.py: tokens never survive in anything that gets published."""

from __future__ import annotations

import gzip
import importlib.util
import io
import pathlib
import tarfile
import zipfile

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "scrub", pathlib.Path(__file__).resolve().parents[2] / ".github/scripts/scrub-run-artifacts.py"
)
scrub_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(scrub_mod)

TOKEN = "eyJsynthetic.token.value-0123456789abcdef"


def _env(tmp_path, monkeypatch, issued=(TOKEN,)):
    runner = tmp_path / "runner"
    runner.mkdir()
    (runner / "issued-tokens").write_text("\n".join(issued), encoding="utf-8")
    monkeypatch.setenv("RUNNER_TEMP", str(runner))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    run = tmp_path / "runs"
    run.mkdir()
    return run


def test_plain_and_utf16_and_extensionless_are_redacted(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    (run / "notes.txt").write_text(f"dump {TOKEN}", encoding="utf-8")
    (run / "envdump").write_bytes(b"\xff\xfe" + TOKEN.encode("utf-16-le"))
    (run / "bad.log").write_bytes(b"\xff" + TOKEN.encode() + b"\xff")  # not UTF-8: withheld
    assert scrub_mod.main(["x", str(run)]) == 0
    assert sorted(p.name for p in run.iterdir()) == ["envdump", "notes.txt"]
    assert all(TOKEN.encode() not in p.read_bytes() for p in run.iterdir())


@pytest.mark.parametrize("skew", [0, 1, 2])
def test_base64_forms_are_redacted(tmp_path, monkeypatch, skew):
    import base64

    run = _env(tmp_path, monkeypatch)
    blob = base64.b64encode(b"a" * skew + TOKEN.encode()).decode()
    (run / "auth.txt").write_text(f"Authorization: Basic {blob}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    text = (run / "auth.txt").read_text(encoding="utf-8")
    assert blob not in text and "***" in text


def test_binary_and_unknown_formats_are_withheld(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    import zlib

    (run / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n" + TOKEN.encode() + b"\x00\x01")
    (run / "stream.bin").write_bytes(zlib.compress(TOKEN.encode()))
    (run / "ok.md").write_text("fine", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert [p.name for p in run.iterdir()] == ["ok.md"]


def test_token_inside_compressed_report_is_withheld(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch)
    with zipfile.ZipFile(run / "report.zip", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("log.txt", TOKEN)
    (run / "report.json.gz").write_bytes(gzip.compress(TOKEN.encode()))
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        info = tarfile.TarInfo("a.txt")
        info.size = len(TOKEN)
        t.addfile(info, io.BytesIO(TOKEN.encode()))
    (run / "x.bin").write_bytes(buf.getvalue())
    (run / "keep.json").write_text("{}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert [p.name for p in run.iterdir()] == ["keep.json"]


def test_every_issued_token_is_scrubbed(tmp_path, monkeypatch):
    old = "eyJolder.rotated.token-0123456789abcdefghij"
    run = _env(tmp_path, monkeypatch, issued=(old, TOKEN))
    (run / "a.log").write_text(f"{old} then {TOKEN}", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    text = (run / "a.log").read_text(encoding="utf-8")
    assert old not in text and TOKEN not in text


def test_failure_wipes_the_run_dir_and_prints_a_fixed_message(tmp_path, monkeypatch, capsys):
    run = _env(tmp_path, monkeypatch)
    (run / "task.json").write_text(f"{TOKEN}", encoding="utf-8")

    def boom(*_a, **_k):
        raise OSError("disk")

    monkeypatch.setattr(scrub_mod, "scrub", boom)
    assert scrub_mod.main(["x", str(run)]) == 1
    assert list(run.iterdir()) == []
    out = capsys.readouterr().out
    assert TOKEN not in out and "withheld" in out


def test_no_secrets_leaves_files_alone(tmp_path, monkeypatch):
    run = _env(tmp_path, monkeypatch, issued=())
    (run / "a.txt").write_text("hello", encoding="utf-8")
    assert scrub_mod.main(["x", str(run)]) == 0
    assert (run / "a.txt").read_text(encoding="utf-8") == "hello"
