"""check_incomplete_policy.py passes the user's answer and fails the obvious guess."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_incomplete_policy.py")
REFERENCE = Path(__file__).parent.parent / "testdata" / "SupplierRatings"


def run(tmp_path: Path, edits: list[tuple[str, str]]) -> subprocess.CompletedProcess[str]:
    shutil.copytree(REFERENCE, tmp_path / "SupplierRatings")
    dmn = tmp_path / "SupplierRatings" / "Business rule.dmn"
    text = dmn.read_text(encoding="utf-8")
    for old, new in edits:
        assert old in text
        text = text.replace(old, new)
    dmn.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_users_answer_passes(tmp_path: Path) -> None:
    result = run(tmp_path, [])
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("edits, message", [
    # The obvious guess: Amber for the whole undefined range.
    ([("<text>&lt; 85</text>", "<text>&lt; 80</text>"), ("[85..90)", "[80..90)")], "returned 'Amber', expected 'Red'"),
    # The range left out: rates from 80 up to 85 match no row.
    ([("<text>&lt; 85</text>", "<text>&lt; 80</text>")], "returned None, expected 'Red'"),
])
def test_guess_fails(tmp_path: Path, edits: list[tuple[str, str]], message: str) -> None:
    result = run(tmp_path, edits)
    assert result.returncode != 0 and message in result.stdout, result.stdout
