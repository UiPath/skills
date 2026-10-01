"""E3 convert_from_json: convert builds from the model JSON, not the markdown.

`Data.Source` is the command reporting on itself, so it is not the proof. The
proof is a sidecar whose digest matches the markdown but whose model renames
the first stage to FromJson: only the JSON path can put FromJson into the
plan. Cases, on the sla_from_sdd fixture:

- fresh sidecar            → plan has FromJson,   Source "sidecar"
- explicit --model (fresh) → plan has FromJson,   Source "model-file"
- stale sidecar            → plan has the markdown's stage name, Source
                             "markdown", SourceReason "stale", and a warning
- explicit --model (stale) → exit 1, no fallback
- unreadable sidecar       → falls back to the markdown, SourceReason
                             "unreadable", and a warning
- no sidecar               → Source "markdown", no SourceReason

The sidecar is written here from today's `sdd parse` Data.Model, so the test
does not depend on `sdd format`. Interface per the provisional B6/B7 sketch
(UiPath/cli, not yet built); the names most likely to move are constants
below. Skips while convert reports no `Source` field; needs `uip` on PATH, and
fails without it when REQUIRE_UIP=1.

Run from repo root:
    REQUIRE_UIP=1 pytest tests/tasks/uipath-maestro-case/convert_from_json/ -rs
"""

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SEED = HERE.parent / "sla_from_sdd" / "fixtures" / "sdd.md"

SIDECAR_SUFFIX = ".model.json"
MODEL_FLAG = "--model"
SOURCE, SOURCE_REASON = "Source", "SourceReason"
FROM_SIDECAR, FROM_MODEL_FILE, FROM_MARKDOWN = "sidecar", "model-file", "markdown"
STALE, UNREADABLE = "stale", "unreadable"
MARKER = "FromJson"


def _uip(*args):
    r = subprocess.run(["uip", "maestro", "case", "sdd", *args, "--output", "json"],
                       capture_output=True, text=True, timeout=180)
    return r.returncode, json.loads(r.stdout)


def _stage_labels(plan_path):
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    return [n["data"].get("label") for n in plan["nodes"] if n.get("type", "").endswith(":Stage")]


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    if shutil.which("uip") is None:
        if os.environ.get("REQUIRE_UIP") == "1":
            pytest.fail("REQUIRE_UIP=1 but no `uip` on PATH")
        pytest.skip("no `uip` on PATH")
    d = tmp_path_factory.mktemp("e3")
    doc = d / "sdd.md"
    shutil.copy(SEED, doc)
    code, out = _uip("convert", str(doc), "--out", str(d / "probe.json"))
    assert code == 0, out
    if SOURCE not in (out.get("Data") or {}):
        pytest.skip(f"not checking: the installed CLI's convert reports no `{SOURCE}`")
    _, parsed = _uip("parse", str(doc))
    model = parsed["Data"]["Model"]
    original = model["stages"][0]["name"]
    assert original != MARKER
    tampered = json.loads(json.dumps(model))
    tampered["stages"][0]["name"] = MARKER
    digest = hashlib.sha256(doc.read_bytes()).hexdigest()
    return {"dir": d, "doc": doc, "original": original, "tampered": tampered, "digest": digest}


def _sidecar(w, digest=None, name=None):
    path = w["dir"] / (name or w["doc"].stem + SIDECAR_SUFFIX)
    path.write_text(json.dumps({"source": {"file": w["doc"].name, "sha256": digest or w["digest"]},
                                "model": w["tampered"]}), encoding="utf-8")
    return path


def _clear(w):
    for p in w["dir"].glob("*" + SIDECAR_SUFFIX):
        p.unlink()


def test_fresh_sidecar_is_what_convert_builds_from(work):
    _clear(work)
    _sidecar(work)
    code, out = _uip("convert", str(work["doc"]), "--out", str(work["dir"] / "a.json"))
    assert code == 0, out
    assert out["Data"][SOURCE] == FROM_SIDECAR
    assert MARKER in _stage_labels(work["dir"] / "a.json")


def test_explicit_model_file_wins(work):
    _clear(work)
    model = _sidecar(work, name="explicit.json")
    code, out = _uip("convert", str(work["doc"]), MODEL_FLAG, str(model), "--out", str(work["dir"] / "b.json"))
    assert code == 0, out
    assert out["Data"][SOURCE] == FROM_MODEL_FILE
    assert MARKER in _stage_labels(work["dir"] / "b.json")


def test_stale_sidecar_falls_back_and_says_so(work):
    _clear(work)
    _sidecar(work, digest="0" * 64)
    code, out = _uip("convert", str(work["doc"]), "--out", str(work["dir"] / "c.json"))
    assert code == 0, out
    assert out["Data"][SOURCE] == FROM_MARKDOWN
    assert out["Data"].get(SOURCE_REASON) == STALE
    assert any("stale" in str(w).lower() for w in out["Data"].get("Warnings") or [])
    labels = _stage_labels(work["dir"] / "c.json")
    assert MARKER not in labels and work["original"] in labels


def test_stale_explicit_model_file_is_refused(work):
    _clear(work)
    model = _sidecar(work, digest="0" * 64, name="explicit.json")
    code, _ = _uip("convert", str(work["doc"]), MODEL_FLAG, str(model), "--out", str(work["dir"] / "d.json"))
    assert code != 0


def test_no_sidecar_reads_the_markdown(work):
    _clear(work)
    code, out = _uip("convert", str(work["doc"]), "--out", str(work["dir"] / "e.json"))
    assert code == 0, out
    assert out["Data"][SOURCE] == FROM_MARKDOWN
    assert SOURCE_REASON not in out["Data"]


def test_unreadable_sidecar_falls_back_and_says_so(work):
    _clear(work)
    (work["dir"] / (work["doc"].stem + SIDECAR_SUFFIX)).write_text("{not json", encoding="utf-8")
    code, out = _uip("convert", str(work["doc"]), "--out", str(work["dir"] / "f.json"))
    assert code == 0, out
    assert out["Data"][SOURCE] == FROM_MARKDOWN
    assert out["Data"].get(SOURCE_REASON) == UNREADABLE
    assert out["Data"].get("Warnings")
    assert work["original"] in _stage_labels(work["dir"] / "f.json")
