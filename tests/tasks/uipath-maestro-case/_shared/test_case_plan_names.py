"""The shared graders accept every name Studio Web gives a case plan."""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import case_check  # noqa: E402


def write(path, nodes=2):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump({"nodes": [{"id": str(i)} for i in range(nodes)]}, fh)


@pytest.mark.parametrize("name", case_check.CASE_PLAN_NAMES)
def test_each_plan_name_is_found(tmp_path, monkeypatch, name):
    write(str(tmp_path / "Sol" / "Case" / name))
    monkeypatch.chdir(tmp_path)
    assert case_check.find_caseplan().endswith(name)


def test_the_newest_name_wins_in_one_directory(tmp_path, monkeypatch):
    write(str(tmp_path / "Sol" / "Case" / "caseplan.json"))
    write(str(tmp_path / "Sol" / "Case" / "caseplan.case"), nodes=3)
    monkeypatch.chdir(tmp_path)
    assert case_check.find_caseplan().endswith("caseplan.case")


def test_an_explicit_caseplan_json_path_also_accepts_the_case_name(tmp_path, monkeypatch):
    write(str(tmp_path / "Sol" / "Case" / "caseplan.case"))
    monkeypatch.chdir(tmp_path)
    assert case_check.find_caseplan("Sol/Case/caseplan.json").endswith("caseplan.case")
