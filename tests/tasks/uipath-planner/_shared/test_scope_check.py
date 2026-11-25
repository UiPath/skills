"""scope-check.mjs: on Automation Suite older than 2.2510.2 the Blocked by platform line names Maestro.

Run: pytest tests/tasks/uipath-planner/_shared/test_scope_check.py -v
"""

import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCRIPT = REPO / "skills" / "uipath-planner" / "scripts" / "scope-check.mjs"

SDD = """# Purchase Request Approval — Solution Design Document

## Decisions Made

| # | Decision | Choice | Why |
|---|---|---|---|
| 1 | **Platform constraints** (Constraint Gate) | {delivery} | Customer platform |

## Recommended Scope

**Recommendation:** Single-product RPA
**Delivery model:** {delivery}
**Blocked by platform:** {blocked}
"""


@pytest.fixture
def check(tmp_path):
    def run(delivery, blocked):
        path = tmp_path / "x-sdd.md"
        path.write_text(SDD.format(delivery=delivery, blocked=blocked), encoding="utf-8")
        done = subprocess.run(["node", str(SCRIPT), str(path)], capture_output=True, text=True, encoding="utf-8", check=False)
        return done.returncode, done.stdout
    return run


@pytest.mark.parametrize("version", ["2024.10", "2023.10.4", "2.2410.1", "2.2510.1"])
def test_old_automation_suite_without_maestro_fails(check, version):
    rc, out = check(f"automation-suite {version}", "Coded Apps → existing dashboard (matrix)")
    assert rc == 1
    assert "does not name Maestro" in out


def test_old_automation_suite_naming_maestro_passes(check):
    rc, out = check("automation-suite 2024.10", "Coded Apps → existing dashboard; Maestro Flow / BPMN / Case → RPA queues (matrix)")
    assert rc == 0, out
    assert out.startswith("OK:")


@pytest.mark.parametrize("delivery", ["automation-suite 2.2510.2", "automation-suite 2.2610.0", "cloud", "automation-suite", "unspecified — assumed cloud [SME REVIEW]"])
def test_maestro_capable_or_unknown_platform_passes(check, delivery):
    rc, out = check(delivery, "none")
    assert rc == 0, out


def test_an_sdd_without_a_recommended_scope_passes(check, tmp_path):
    path = tmp_path / "plain-sdd.md"
    path.write_text("# SDD — Case\n\n## Section 1: Case Definition\n", encoding="utf-8")
    done = subprocess.run(["node", str(SCRIPT), str(path)], capture_output=True, text=True, encoding="utf-8", check=False)
    assert done.returncode == 0, done.stdout
