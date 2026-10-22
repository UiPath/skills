"""
Tests for scripts/refresh-cli-declarations.py (MST-16782).

Each test builds a throwaway declaration in tmp_path: a module whose from_cli()
returns what the "CLI" declares, a snapshot, and a test standing in for the
hand-kept copies. So the refresh, the significance check, the test run and the
report are exercised end to end with no `uip` installed.

Run from repo root:
    pytest tests/scripts/test_refresh_cli_declarations.py
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolve string annotations through it
    spec.loader.exec_module(module)
    return module


refresh = _load("refresh_cli_declarations", REPO_ROOT / "scripts" / "refresh-cli-declarations.py")

SNAPSHOT_DATA = {"Version": "1.0", "Kinds": [{"Type": "a"}, {"Type": "b"}]}

MODULE = '''
import json
from pathlib import Path
SNAPSHOT = Path(__file__).with_name("snap.json")
LIVE = {live!r}
def load():
    return json.loads(SNAPSHOT.read_text())["Data"]
def lists(data):
    return {{"Kinds": data["Kinds"]}}
def from_cli():
    return LIVE
'''

# Stands in for the hand-kept copy: it says exactly types a and b exist.
COPY_TEST = '''
import json
from pathlib import Path
def test_copy_lists_a_and_b():
    data = json.loads(Path(__file__).with_name("snap.json").read_text())["Data"]
    assert [k["Type"] for k in data["Kinds"]] == ["a", "b"]
'''


def make_decl(tmp_path, live):
    (tmp_path / "decl_mod.py").write_text(MODULE.format(live=live))
    (tmp_path / "snap.json").write_text(json.dumps({"Code": "X", "Data": SNAPSHOT_DATA}, indent=2) + "\n")
    (tmp_path / "test_copy.py").write_text(COPY_TEST)
    return refresh.Declaration(
        name="fake kinds",
        command="uip fake kinds list --output json",
        module=tmp_path / "decl_mod.py",
        significant="lists",
        snapshot=tmp_path / "snap.json",
        tests=(str(tmp_path / "test_copy.py"),),
        copies=("docs/fake-guide.md (§ Kinds table)",),
    )


def test_a_version_only_change_is_not_drift_and_writes_nothing(tmp_path):
    decl = make_decl(tmp_path, {**SNAPSHOT_DATA, "Version": "2.0"})
    before = decl.snapshot.read_text()
    result = refresh.refresh(decl, write=True)
    assert result["changed"] is False
    assert decl.snapshot.read_text() == before


def test_a_missing_command_is_an_error_and_writes_nothing(tmp_path):
    decl = make_decl(tmp_path, None)
    before = decl.snapshot.read_text()
    result = refresh.refresh(decl, write=True)
    assert "error" in result and "uip fake kinds list" in result["error"]
    assert decl.snapshot.read_text() == before


def test_check_mode_reports_drift_but_writes_nothing(tmp_path):
    decl = make_decl(tmp_path, {**SNAPSHOT_DATA, "Kinds": [{"Type": "a"}]})
    before = decl.snapshot.read_text()
    result = refresh.refresh(decl, write=False)
    assert result["changed"] is True
    assert decl.snapshot.read_text() == before
    assert "passed" not in result


def test_drift_the_copies_still_match_says_so(tmp_path):
    # The snapshot had an extra field the copy does not care about; the lists agree after.
    decl = make_decl(tmp_path, {**SNAPSHOT_DATA, "Kinds": [{"Type": "a"}, {"Type": "b"}, {"Type": "c"}]})
    (tmp_path / "test_copy.py").write_text("def test_nothing_restated():\n    pass\n")
    result = refresh.refresh(decl, write=True)
    assert result["changed"] and result["passed"]
    assert json.loads(decl.snapshot.read_text())["Data"]["Kinds"][-1] == {"Type": "c"}
    body = refresh.report([result], "1.0.0-dev.1")
    assert "Every hand-kept copy still matches" in body
    assert "Do not merge" not in body


def test_drift_that_breaks_a_copy_names_the_move_the_copy_and_the_test(tmp_path):
    decl = make_decl(tmp_path, {**SNAPSHOT_DATA, "Kinds": [{"Type": "a"}, {"Type": "c"}]})
    result = refresh.refresh(decl, write=True)
    assert result["changed"] and not result["passed"]
    body = refresh.report([result], "1.0.0-dev.1")
    assert "Moved: fake kinds." in body
    assert '`Kinds`: added `{"Type": "c"}`; removed `{"Type": "b"}`' in body
    assert "- docs/fake-guide.md (§ Kinds table)" in body
    assert "test_copy_lists_a_and_b" in body
    assert "Do not merge with failing tests" in body


def test_the_snapshot_keeps_its_envelope(tmp_path):
    decl = make_decl(tmp_path, {**SNAPSHOT_DATA, "Kinds": [{"Type": "a"}]})
    refresh.refresh(decl, write=True)
    payload = json.loads(decl.snapshot.read_text())
    assert payload["Code"] == "X"
    assert payload["Data"]["Kinds"] == [{"Type": "a"}]


def test_main_exits_1_when_a_declaration_cannot_be_read(tmp_path, monkeypatch):
    monkeypatch.setattr(refresh, "DECLARATIONS", (make_decl(tmp_path, None),))
    monkeypatch.setattr(refresh, "cli_version", lambda: "x")
    out = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert refresh.main(["--report", str(tmp_path / "r.md")]) == 1
    assert "changed=false" in out.read_text()
    assert "Could not read fake kinds" in (tmp_path / "r.md").read_text()


def test_main_sets_changed_true_on_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(refresh, "DECLARATIONS", (make_decl(tmp_path, {**SNAPSHOT_DATA, "Kinds": []}),))
    out = tmp_path / "github_output"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    assert refresh.main(["--check"]) == 0
    assert "changed=true" in out.read_text()


@pytest.mark.parametrize("decl", refresh.DECLARATIONS, ids=lambda d: d.name)
def test_every_registered_declaration_resolves(decl):
    """The registry points at files that exist and a module with the three hooks."""
    for path in (decl.module, decl.snapshot, *map(Path, decl.tests)):
        assert path.exists(), path
    module = refresh.load_module(decl.module)
    for hook in ("from_cli", "load", decl.significant):
        assert callable(getattr(module, hook, None)), hook
    # The significant part of the committed snapshot is computable.
    assert getattr(module, decl.significant)(module.load())
    for copy in decl.copies:
        assert (REPO_ROOT / copy.split(" ", 1)[0]).exists(), copy
