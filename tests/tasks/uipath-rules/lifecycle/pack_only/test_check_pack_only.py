"""check_pack_only.py passes the package `uip solution pack` writes and fails a missing, stale or edited one."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

CHECKER = Path(__file__).with_name("check_pack_only.py")
FIXTURE = Path(__file__).parents[2] / "_fixtures" / "solution_with_rule" / "Logistics"


def sandbox(tmp_path: Path, dmn: bytes | None = None) -> Path:
    """The fixture, plus the zip `uip solution pack` writes; `dmn` replaces the packed rule's `.dmn`."""
    shutil.copytree(FIXTURE, tmp_path / "Logistics")
    project = tmp_path / "Logistics" / "ShippingRules"
    rule_id = json.loads((tmp_path / "Logistics" / "Logistics.uipx").read_text(encoding="utf-8"))["Projects"][0]["Id"]
    rule = io.BytesIO()
    with zipfile.ZipFile(rule, "w") as z:
        z.writestr("entry-points.json", (project / "entry-points.json").read_bytes())
        z.writestr("Business rule.dmn", dmn if dmn is not None else (project / "Business rule.dmn").read_bytes())
    (tmp_path / "out").mkdir()
    with zipfile.ZipFile(tmp_path / "out" / "Logistics_1.0.0.zip", "w") as z:
        z.writestr("packageInfo.json", '{"version": "v1", "type": "unified"}')
        z.writestr(f"files/{rule_id}/ShippingRules-1.0.0.uirule", rule.getvalue())
    return tmp_path


def run(sandbox_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(CHECKER)], cwd=sandbox_dir, capture_output=True, text=True, check=False)


def test_package_passes(tmp_path: Path) -> None:
    result = run(sandbox(tmp_path))
    assert result.returncode == 0, result.stdout


def test_no_package_fails(tmp_path: Path) -> None:
    shutil.copytree(FIXTURE, tmp_path / "Logistics")
    result = run(tmp_path)
    assert result.returncode != 0 and "no solution package" in result.stdout


def test_stale_package_fails(tmp_path: Path) -> None:
    result = run(sandbox(tmp_path, dmn=b"<definitions/>"))
    assert result.returncode != 0 and "packs a Business rule.dmn that is not the project's" in result.stdout


def test_edited_project_fails(tmp_path: Path) -> None:
    sandbox(tmp_path)
    dmn = tmp_path / "Logistics" / "ShippingRules" / "Business rule.dmn"
    dmn.write_text(dmn.read_text(encoding="utf-8").replace("Freight", "Pallet"), encoding="utf-8")
    result = run(tmp_path)
    assert result.returncode != 0 and "packing must not edit the rule" in result.stdout
