"""Build each low-code scenario fixture and check it with the real CLI.

Mirrors the reviewer's own sequence: refresh, validate, review. Skipped when
`uip` is not on PATH.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SUITE = Path(__file__).resolve().parents[1]
SCENARIOS = sorted((SUITE / "agents").glob("lowcode_scenario_*/scenario.json"))
UIP = os.environ.get("UIP") or shutil.which("uip")

pytestmark = pytest.mark.skipif(not UIP, reason="uip not on PATH")


def _uip(*argv: str, cwd: Path) -> dict:
    proc = subprocess.run([UIP, *argv, "--output", "json"], cwd=cwd, capture_output=True, text=True, timeout=180)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"`uip {' '.join(argv)}` returned non-JSON (exit {proc.returncode}): {proc.stderr[-400:]}")


@pytest.mark.parametrize("spec_path", SCENARIOS, ids=[p.parent.name for p in SCENARIOS])
def test_scenario_fixture(spec_path: Path, tmp_path: Path) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    setup = tmp_path / "_setup"
    shutil.copytree(SUITE / "_setup", setup)
    shutil.copytree(spec_path.parent / "_setup", setup, dirs_exist_ok=True)
    subprocess.run([sys.executable, f"_setup/{spec['inject']}"], cwd=tmp_path, check=True, timeout=60)

    project = spec["project"]
    refresh = _uip("agent", "refresh", project, cwd=tmp_path)
    validate = _uip("agent", "validate", project, cwd=tmp_path)
    if spec.get("validate_must_pass", True):
        assert refresh.get("Result") == "Success", refresh
        assert validate.get("Result") == "Success", validate

    review = _uip("agent", "review", project, cwd=tmp_path)
    assert review.get("Result") == "Success", review
    emitted = {i["RuleId"] for i in review["Data"].get("Issues", [])}
    missing = set(spec.get("cli_expected", [])) - emitted
    assert not missing, f"CLI no longer emits {sorted(missing)}; emitted {sorted(emitted)}"
    if spec.get("cli_only_expected"):
        extra = emitted - set(spec.get("cli_expected", []))
        assert not extra, f"CLI emits unplanned {sorted(extra)}"
