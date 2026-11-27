"""check_shape_judgement.py passes each reference rule and fails it with the shape trap taken."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_shape_judgement.py")
TESTDATA = Path(__file__).parent.parent / "testdata"
MODES = {"single": "ShippingRules", "shared": "ClaimsRules", "model": "MemberPrices"}

SPLIT_DECISION = """  <decision id="decision_oversized" name="oversized" label="oversized">
    <variable id="variable_oversized" name="oversized" typeRef="boolean" />
    <literalExpression id="le_oversized" typeRef="boolean">
      <text>weightKg &gt; 30</text>
    </literalExpression>
  </decision>
  <inputData id="inputData_weightKg\""""


def run(tmp_path: Path, mode: str, old: str = "", new: str = "", graph: bool = False) -> subprocess.CompletedProcess[str]:
    project = MODES[mode]
    shutil.copytree(TESTDATA / project, tmp_path / project)
    dmn = tmp_path / project / "Business rule.dmn"
    text = dmn.read_text(encoding="utf-8")
    assert old in text
    text = text.replace(old, new)
    if graph:
        # A rule of several decisions declares the canvas surface; without it the surface check fails first.
        text = text.replace('surface="decision-table"', 'surface="decision-graph"', 1)
    dmn.write_text(text, encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER), mode], cwd=tmp_path, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("mode", sorted(MODES))
def test_reference_rule_passes(tmp_path: Path, mode: str) -> None:
    result = run(tmp_path, mode)
    assert result.returncode == 0, result.stdout


@pytest.mark.parametrize("mode, old, new, message", [
    # One answer split across two decisions.
    ("single", '  <inputData id="inputData_weightKg"', SPLIT_DECISION, "holds 2 decisions"),
    # Routing reads the claim amount itself instead of the shared tier decision.
    ("shared", '<requiredDecision href="#decision_tier" />\n    </informationRequirement>\n    <decisionTable id="dt_routing"',
     '<requiredInput href="#inputData_claimAmount" />\n    </informationRequirement>\n    <decisionTable id="dt_routing"',
     "require no common decision"),
    # The delivery fee inlines the calculation the model holds.
    ("model", "<text>memberPrice(deliveryFee)</text>", "<text>decimal(deliveryFee * 0.9, 2)</text>",
     "computes the discount itself"),
    # A wrong value on a correct shape.
    ("single", "<text>&quot;Courier&quot;</text>", "<text>&quot;Post&quot;</text>", "expected 'Courier'"),
])
def test_trap_fails(tmp_path: Path, mode: str, old: str, new: str, message: str) -> None:
    result = run(tmp_path, mode, old, new, graph=new is SPLIT_DECISION)
    assert result.returncode != 0 and message in result.stdout, result.stdout
