"""check_draft_word_build.py and _shared/check_no_mock_nodes.py, with `flow validate` stubbed out."""

from __future__ import annotations

import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import check_draft_word_build as cdw  # noqa: E402
from _shared import check_no_mock_nodes as cnm  # noqa: E402
from _shared import draft_fixtures as fx  # noqa: E402


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cdw, "validate", lambda path: 0)
    return lambda doc: fx.write_project(tmp_path, doc)


def test_built_flow_passes_both(sandbox):
    sandbox(fx.built(fx.SKELETON))
    assert cdw.main() == 0
    assert cnm.main() == 0


def test_skeleton_fails_both(sandbox, capsys):
    sandbox(fx.SKELETON)
    assert cdw.main() == 1
    assert "only mock boxes" in capsys.readouterr().err
    assert cnm.main() == 1
    assert "still has mock boxes" in capsys.readouterr().err


def test_partly_built_flow_passes_word_build_but_not_no_mock(sandbox, capsys):
    doc = fx.built(fx.SKELETON)
    doc["nodes"][1] = fx.box("record", "Record invoice [Data Fabric]")
    sandbox(doc)
    assert cdw.main() == 0
    assert cnm.main() == 1
    assert "record" in capsys.readouterr().err


def test_kind_suffix_left_on_built_node_fails(sandbox, capsys):
    doc = fx.built(fx.SKELETON)
    doc["nodes"][1]["display"]["label"] = "Record invoice [Data Fabric]"
    sandbox(doc)
    assert cnm.main() == 1
    assert "[Kind] outline suffix" in capsys.readouterr().err


def test_validate_failure_propagates(sandbox, monkeypatch):
    sandbox(fx.built(fx.SKELETON))
    monkeypatch.setattr(cdw, "validate", lambda path: 1)
    assert cdw.main() == 1


def test_kind_before_variable_suffix_fails(sandbox, capsys):
    doc = fx.built(fx.SKELETON)
    doc["nodes"][1]["display"]["label"] = "Record invoice [Data Fabric] \u2192 invoiceId"
    sandbox(doc)
    assert cnm.main() == 1
    assert "[Kind] outline suffix" in capsys.readouterr().err


def test_no_outline_mocks_flag(sandbox, capsys):
    doc = fx.built(fx.SKELETON)
    doc["nodes"][1] = fx.box("record", "Record invoice [Data Fabric]")
    sandbox(doc)
    assert cdw.main([]) == 0
    assert cdw.main(["--no-outline-mocks"]) == 1
    assert "mock outline boxes" in capsys.readouterr().err


def test_no_outline_mocks_passes_a_built_flow(sandbox):
    sandbox(fx.built(fx.SKELETON))
    assert cdw.main(["--no-outline-mocks"]) == 0
