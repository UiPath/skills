"""Integrity guard for the degraded SDD corpus.

The degraded_sdd_conformance eval asserts the SDD gate names each defect's
recorded line, so the manifest has to stay true to the fixtures: every fixture
is listed, every recorded line holds the degraded text, and the defect named
is actually present there. This does not test the gate; it tests that the
corpus is what the manifest claims.

Run from repo root:
    pytest tests/tasks/uipath-maestro-case/degraded_sdd_conformance/
"""

import hashlib
import json
import re
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
MANIFEST = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
DEFECTS = MANIFEST["defects"]


def _lines(path):
    return path.read_text(encoding="utf-8").split("\n")


def _git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _norm(name):
    return re.sub(r"\s*\([^)]*\)\s*$", "", name).strip().lower()


def test_manifest_lists_every_fixture():
    on_disk = {p.parent.name for p in (HERE / "fixtures").glob("*/sdd.md")}
    listed = {Path(d["fixture"]).parent.name for d in DEFECTS}
    assert on_disk == listed


@pytest.mark.parametrize("d", DEFECTS, ids=lambda d: d["defect_class"])
def test_recorded_line_holds_the_defect(d):
    path = HERE / d["fixture"]
    if d["line"] is None:
        assert d["defect_class"] == "empty-document"
        assert path.stat().st_size == 0
        return
    lines = _lines(path)
    got = lines[d["line"] - 1]
    assert got == d["degraded"]
    assert got != d["original"]
    cls = d["defect_class"]
    if cls == "table-row-missing-leading-pipe":
        assert d["original"].startswith("|") and not got.startswith("|")
        assert lines[d["line"] - 2].startswith("|"), "defect must sit mid-table"
    elif cls == "curly-quotes-in-expression-cell":
        assert re.search("[“”]", got) and not re.search("[“”]", d["original"])
        assert "=js:" in got
    elif cls == "section-heading-renamed":
        assert d["original"] == "### Case Variables"
        assert "### Case Variables" not in lines
    elif cls == "norm-parenthetical-collision":
        prev = lines[d["line"] - 2].split("|")[1]
        new = got.split("|")[1]
        assert prev.strip() != new.strip() and _norm(prev) == _norm(new)
    else:
        pytest.fail(f"no integrity rule for defect class {cls}")


@pytest.mark.parametrize("d", [d for d in DEFECTS if d["seed"]], ids=lambda d: d["defect_class"])
def test_fixture_is_seed_plus_one_line(d):
    seed = REPO_ROOT / d["seed"]
    if _git_blob(seed) != d["seed_blob"]:
        pytest.skip("seed fixture has since changed; manifest seed_blob is the provenance")
    a, b = _lines(seed), _lines(HERE / d["fixture"])
    n = d["line"] - 1
    if d["original"] is None:
        assert b[:n] + b[n + 1:] == a
    else:
        assert a[n] == d["original"] and a[:n] + a[n + 1:] == b[:n] + b[n + 1:]
