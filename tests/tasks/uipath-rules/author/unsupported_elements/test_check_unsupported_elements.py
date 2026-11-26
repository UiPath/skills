"""check_unsupported_elements.py passes a plain table and fails each element the skill declines."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_unsupported_elements.py")
REFERENCE = Path(__file__).parent.parent / "testdata" / "SupplierRules"
ANCHOR = '  <inputData id="inputData_onboarded"'
NESTED_CONTEXT = """  <businessKnowledgeModel id="bkm_limit" name="limit">
    <variable id="variable_bkm_limit" name="limit" />
    <encapsulatedLogic id="el_limit">
      <context id="context_limit" />
    </encapsulatedLogic>
  </businessKnowledgeModel>
"""


def run(tmp_path: Path, insert: str = "") -> subprocess.CompletedProcess[str]:
    shutil.copytree(REFERENCE, tmp_path / "SupplierRules")
    dmn = tmp_path / "SupplierRules" / "Business rule.dmn"
    text = dmn.read_text(encoding="utf-8")
    assert ANCHOR in text
    dmn.write_text(text.replace(ANCHOR, insert + ANCHOR), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_plain_table_passes(tmp_path: Path) -> None:
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("insert, message", [
    ('  <knowledgeSource id="ks_policy" name="Procurement Policy 2026" />\n', "declares a knowledgeSource"),
    ('  <decisionService id="ds_approval" name="approvalService" />\n', "declares a decisionService"),
    ('  <import namespace="http://example.com/supplier-types" name="SupplierTypes" '
     'importType="https://www.omg.org/spec/DMN/20230324/MODEL/" />\n', "<import> element"),
    (NESTED_CONTEXT, "<context> element"),
])
def test_declined_element_fails(tmp_path: Path, insert: str, message: str) -> None:
    result = run(tmp_path, insert)
    assert result.returncode != 0 and message in result.stdout, result.stdout
