"""check_narrow_edit.py passes each narrow edit made with the CLI and fails the edit that went too far."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_narrow_edit.py")
TESTDATA = Path(__file__).parent.parent / "testdata"
FIXTURE = Path(__file__).with_name("fixtures") / "OrderRulesSolution" / "OrderRules"


def run(tmp_path: Path, mode: str, source: Path, edits: list[tuple[str, str]] = (), file: str = "Business rule.dmn") -> subprocess.CompletedProcess[str]:
    shutil.copytree(source, tmp_path / "OrderRules")
    target = tmp_path / "OrderRules" / file
    text = target.read_text(encoding="utf-8")
    for old, new in edits:
        assert old in text
        text = text.replace(old, new)
    target.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER), mode], cwd=tmp_path, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("mode", ["threshold", "remove", "rename"])
def test_cli_made_edit_passes(tmp_path: Path, mode: str) -> None:
    result = run(tmp_path, mode, TESTDATA / f"OrderRules_{mode}")
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("mode, edits, message", [
    # The 1000 in the tier table moved too.
    ("threshold", [("<text>[1000..5000)</text>", "<text>[500..5000)</text>")], "decision_tier changed"),
    # A row of the priority table renamed while its threshold moved.
    ("threshold", [("<text>Large order</text>", "<text>Big order</text>")], "beyond its threshold cells"),
    # The name changed with the label, which breaks every reader of `discount`.
    ("rename", [('name="discount" label="Loyalty discount"', 'name="loyaltyDiscount" label="Loyalty discount"')], "name changed"),
])
def test_edit_that_went_too_far_fails(tmp_path: Path, mode: str, edits: list[tuple[str, str]], message: str) -> None:
    result = run(tmp_path, mode, TESTDATA / f"OrderRules_{mode}", edits)
    assert result.returncode != 0 and message in result.stdout, result.stdout


def test_unedited_rule_fails_every_mode(tmp_path: Path) -> None:
    for mode, message in (("threshold", "returned 'Normal', expected 'Express'"), ("remove", "is still in the rule"),
                          ("rename", "expected 'Loyalty discount'")):
        result = run(tmp_path / mode, mode, FIXTURE)
        assert result.returncode != 0 and message in result.stdout, (mode, result.stdout)


def test_stale_entry_point_fails(tmp_path: Path) -> None:
    shutil.copytree(TESTDATA / "OrderRules_remove", tmp_path / "OrderRules")
    shutil.copy(FIXTURE / "entry-points.json", tmp_path / "OrderRules" / "entry-points.json")
    result = subprocess.run([sys.executable, str(CHECKER), "remove"], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "survives its decision" in result.stdout, result.stdout
