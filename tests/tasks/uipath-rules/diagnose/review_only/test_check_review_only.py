"""check_review_only.py passes a review naming real faults and fails one naming none, or a fixed rule."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_review_only.py")
FIXTURE = Path(__file__).with_name("fixtures")
RIGHT = {"gaps": [{"annualSpend": 5000, "riskLevel": "High"}], "overlaps": [{"annualSpend": 90000, "riskLevel": "Medium"}]}


def run(tmp_path: Path, review: object) -> subprocess.CompletedProcess[str]:
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    if review is not None:
        (tmp_path / "review.json").write_text(json.dumps(review), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_review_naming_both_faults_passes(tmp_path: Path) -> None:
    result = run(tmp_path, RIGHT)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("review, message", [
    (None, "review.json is missing"),
    ({**RIGHT, "gaps": []}, "lists no gaps"),
    # Inputs the caller never sends match no row, but they are not a gap in the table.
    ({**RIGHT, "gaps": [{"annualSpend": 5000, "riskLevel": "Unknown"}]}, "has riskLevel 'Unknown'"),
    # A covered input listed as a gap.
    ({**RIGHT, "gaps": [{"annualSpend": 30000, "riskLevel": "High"}]}, "matches 1 rows"),
    # A single-row input listed as an overlap.
    ({**RIGHT, "overlaps": [{"annualSpend": 50000, "riskLevel": "Medium"}]}, "matches 1 rows"),
])
def test_wrong_review_fails(tmp_path: Path, review: object, message: str) -> None:
    result = run(tmp_path, review)
    assert result.returncode != 0 and message in result.stdout, result.stdout


def test_fixed_rule_fails(tmp_path: Path) -> None:
    shutil.copytree(FIXTURE, tmp_path, dirs_exist_ok=True)
    dmn = tmp_path / "SupplierChecksSolution" / "SupplierChecks" / "Business rule.dmn"
    dmn.write_text(dmn.read_text(encoding="utf-8").replace("&gt;= 80000", "&gt;= 100000"), encoding="utf-8")
    (tmp_path / "review.json").write_text(json.dumps(RIGHT), encoding="utf-8")
    result = subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "the request was a review, not a fix" in result.stdout, result.stdout
