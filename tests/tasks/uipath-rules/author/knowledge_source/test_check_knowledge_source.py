"""check_knowledge_source.py passes a cited policy and fails a missing, unwired or miswired one."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_knowledge_source.py")
REFERENCE = Path(__file__).parent.parent / "testdata" / "SpendRules"
CITATION = re.compile(r"\s*<authorityRequirement id=\"authorityRequirement_approval_policy\">.*?</authorityRequirement>", re.S)


def run(tmp_path: Path, change=None) -> subprocess.CompletedProcess[str]:
    shutil.copytree(REFERENCE, tmp_path / "SpendRules")
    dmn = tmp_path / "SpendRules" / "Business rule.dmn"
    if change is not None:
        text = dmn.read_text(encoding="utf-8")
        assert change(text) != text, change.__name__
        dmn.write_text(change(text), encoding="utf-8")
    return subprocess.run([sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True, check=False)


def test_cited_policy_passes(tmp_path: Path) -> None:
    result = run(tmp_path)
    assert result.returncode == 0, result.stdout


def no_source(text: str) -> str:
    text = re.sub(r"\s*<knowledgeSource .*?</knowledgeSource>", "", text, flags=re.S)
    return re.sub(r"\s*<dmndi:DMNShape [^>]*dmnElementRef=\"knowledgeSource_procurementPolicy\".*?</dmndi:DMNShape>", "", CITATION.sub("", text), flags=re.S)


def uncited(text: str) -> str:
    return CITATION.sub("", text)


def miswired(text: str) -> str:
    """The policy wired as an input to the decision instead of cited as its authority."""
    return CITATION.sub('\n    <informationRequirement id="ir_policy">\n      <requiredDecision href="#knowledgeSource_procurementPolicy" />\n    </informationRequirement>', text)


def unplaced(text: str) -> str:
    return re.sub(r"\s*<dmndi:DMNShape [^>]*dmnElementRef=\"knowledgeSource_procurementPolicy\".*?</dmndi:DMNShape>", "", text, flags=re.S)


@pytest.mark.parametrize("change, message", [
    (no_source, "found 0"),
    (uncited, "does not cite"),
    (miswired, "points at a knowledge source with requiredDecision"),
    (unplaced, "run 'uip rules format'"),
])
def test_wrong_policy_fails(tmp_path: Path, change, message: str) -> None:
    result = run(tmp_path, change)
    assert result.returncode != 0 and message in result.stdout, result.stdout
