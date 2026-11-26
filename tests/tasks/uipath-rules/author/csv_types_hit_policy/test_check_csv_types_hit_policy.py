"""check_csv_types_hit_policy.py passes the reference LeaveRules and fails each seeded fault."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_csv_types_hit_policy.py")
REFERENCE = Path(__file__).parent.parent / "testdata" / "LeaveRules"


def run(tmp_path: Path, old: str = "", new: str = "", file: str = "Business rule.dmn") -> subprocess.CompletedProcess[str]:
    shutil.copytree(REFERENCE, tmp_path / "LeaveRules")
    target = tmp_path / "LeaveRules" / file
    text = target.read_text(encoding="utf-8")
    assert old in text
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_reference_rule_passes(tmp_path: Path) -> None:
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("old, new, message", [
    ('hitPolicy="COLLECT"', 'hitPolicy="FIRST"', "expected COLLECT"),
    ('id="dt_approval" hitPolicy="UNIQUE"', 'id="dt_approval" hitPolicy="FIRST"', "expected UNIQUE"),
    ("<text>approval.approver</text>", "<text>approver</text>", "expected 'approval.approver'"),
    ('name="startDate" typeRef="date"', 'name="startDate" typeRef="string"', "not typed date"),
    ("&lt; date(&quot;2027-01-01&quot;)", "&lt;= date(&quot;2027-01-01&quot;)", "matches 2 rows of a UNIQUE table"),
])
def test_seeded_fault_fails(tmp_path: Path, old: str, new: str, message: str) -> None:
    result = run(tmp_path, old, new)
    assert result.returncode != 0 and message in result.stdout, result.stdout


def test_stale_contract_fails(tmp_path: Path) -> None:
    result = run(tmp_path, '"format": "date",', "", file="entry-points.json")
    assert result.returncode != 0 and "types input startDate" in result.stdout, result.stdout
