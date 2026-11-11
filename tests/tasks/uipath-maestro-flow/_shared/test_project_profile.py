"""Unit tests for ``project_profile.py``'s flow lookup."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from project_profile import find_flow  # noqa: E402


def _write(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{}", encoding="utf-8")


def test_finds_the_cli_named_flow(tmp_path, monkeypatch):
    _write(tmp_path / "ShipmentTracker" / "ShipmentTracker" / "ShipmentTracker.flow")
    monkeypatch.chdir(tmp_path)

    assert [p.name for p in find_flow("ShipmentTracker")] == ["ShipmentTracker.flow"]


def test_finds_studio_web_new_flow_in_the_named_project(tmp_path, monkeypatch):
    _write(tmp_path / "ShipmentTracker" / "ShipmentTracker" / "new.flow")
    _write(tmp_path / "Other" / "Other" / "new.flow")
    monkeypatch.chdir(tmp_path)

    assert [str(p) for p in find_flow("ShipmentTracker")] == ["ShipmentTracker/ShipmentTracker/new.flow"]
