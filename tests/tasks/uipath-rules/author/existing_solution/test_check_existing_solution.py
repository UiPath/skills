"""check_existing_solution.py passes work done inside Logistics and fails work beside it or over it."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_existing_solution.py")
FIXTURE = Path(__file__).parents[2] / "_fixtures" / "solution_with_rule" / "Logistics"
RETURNS = Path(__file__).parent.parent / "testdata" / "ReturnsRules"


def sandbox(tmp_path: Path, returns_at: str | None = None, register: bool = True) -> Path:
    """The fixture, plus ReturnsRules copied to `returns_at` and listed in Logistics.uipx when asked."""
    shutil.copytree(FIXTURE, tmp_path / "Logistics")
    if returns_at:
        shutil.copytree(RETURNS, tmp_path / returns_at)
    if register:
        manifest = tmp_path / "Logistics" / "Logistics.uipx"
        body = json.loads(manifest.read_text(encoding="utf-8"))
        body["Projects"].append({"Type": "BusinessRules", "ProjectRelativePath": "ReturnsRules/project.uiproj", "Id": "id"})
        manifest.write_text(json.dumps(body), encoding="utf-8")
    return tmp_path


def run(sandbox_dir: Path, mode: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECKER), mode], cwd=sandbox_dir, capture_output=True, text=True, check=False)


def test_new_project_in_the_solution_passes(tmp_path: Path) -> None:
    result = run(sandbox(tmp_path, "Logistics/ReturnsRules"), "new")
    assert result.returncode == 0, result.stdout


def test_untouched_existing_project_passes(tmp_path: Path) -> None:
    result = run(sandbox(tmp_path, register=False), "existing")
    assert result.returncode == 0, result.stdout


def test_new_project_in_its_own_solution_fails(tmp_path: Path) -> None:
    sandbox(tmp_path, "ReturnsRulesSolution/ReturnsRules", register=False)
    (tmp_path / "ReturnsRulesSolution" / "ReturnsRulesSolution.uipx").write_text('{"Projects": []}', encoding="utf-8")
    result = run(tmp_path, "new")
    assert result.returncode != 0 and "2 .uipx files" in result.stdout


def test_unregistered_project_fails(tmp_path: Path) -> None:
    result = run(sandbox(tmp_path, "Logistics/ReturnsRules", register=False), "new")
    assert result.returncode != 0 and "does not list ReturnsRules" in result.stdout


@pytest.mark.parametrize("mode", ["new", "existing"])
def test_overwritten_existing_rule_fails(tmp_path: Path, mode: str) -> None:
    sandbox(tmp_path, "Logistics/ReturnsRules")
    dmn = tmp_path / "Logistics" / "ShippingRules" / "Business rule.dmn"
    dmn.write_text(dmn.read_text(encoding="utf-8").replace("Freight", "Pallet"), encoding="utf-8")
    result = run(tmp_path, mode)
    assert result.returncode != 0 and "ShippingRules/Business rule.dmn changed" in result.stdout
