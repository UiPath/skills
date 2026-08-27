"""Contract guard: the activation-mode vocabulary has one owner, and the
build-lane audit actually gates on it.

Three places name the task activation modes — `scripts/audit_plan.py`, the
activation-mode / rule-type table in
`references/plugins/conditions/task-entry-conditions/planning.md`, and the §4.6
field list in `references/planning.md`. They drifted once already: the table
carried six of the seven modes while the auditor accepted all seven, so an agent
reading the table would treat `parallel-after-predecessor` as illegal. These
tests fail on the next divergence instead of letting it reach a run.

The lane tests pin the behaviour the Phase 1 plan-shape gate depends on:
`--lane build` must flag a wrong `activation-mode` / `entry-rule` pair on a
build-lane plan (which legitimately carries `taskTypeId`, `isRequired`, and
`runOnlyOnce`) and must stay silent on a correct one.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[4] / "skills" / "uipath-maestro-case"
AUDIT = SKILL / "scripts" / "audit_plan.py"
PLANNING = SKILL / "references" / "planning.md"
TABLE_DOC = (
    SKILL / "references" / "plugins" / "conditions" / "task-entry-conditions" / "planning.md"
)

PAIRING_TABLE = re.compile(
    r"\| activation-mode \| Allowed rule-type \|\n\|---\|---\|\n((?:\|.*\n)+)"
)


def _script_constant(name: str) -> str:
    body = re.search(rf"{name} = \{{(.*?)^\}}", AUDIT.read_text(encoding="utf-8"), re.S | re.M)
    assert body, f"{name} not found in {AUDIT.name}"
    return body.group(1)


def script_modes() -> set[str]:
    return set(re.findall(r'"([a-z][a-z-]*)"', _script_constant("ACTIVATION_MODES")))


def script_rule_modes() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for line in _script_constant("ENTRY_RULE_MODES").splitlines():
        match = re.match(r'\s*"([a-z-]+)":\s*\{(.*?)\},', line)
        if match:
            out[match.group(1)] = set(re.findall(r'"([a-z-]+)"', match.group(2)))
    return out


def table_rows() -> dict[str, str]:
    match = PAIRING_TABLE.search(TABLE_DOC.read_text(encoding="utf-8"))
    assert match, "activation-mode / rule-type table not found — did its header change?"
    rows: dict[str, str] = {}
    for line in match.group(1).splitlines():
        cells = [c.strip() for c in line.strip("|").split("|")]
        mode = re.match(r"`([a-z][a-z-]*)`", cells[0])
        assert mode, f"table row does not start with a backticked mode: {line!r}"
        rows[mode.group(1)] = cells[1]
    return rows


def test_table_lists_every_mode_the_auditor_accepts():
    assert table_rows().keys() == script_modes()


def test_planning_field_list_names_every_mode_the_auditor_accepts():
    line = next(
        l for l in PLANNING.read_text(encoding="utf-8").splitlines()
        if l.startswith("- **activation-mode**")
    )
    assert set(re.findall(r"`([a-z][a-z-]*)`", line)) >= script_modes()


@pytest.mark.parametrize("rule,modes", sorted(script_rule_modes().items()))
def test_every_paired_mode_names_its_rule_in_the_table(rule, modes):
    rows = table_rows()
    for mode in modes:
        assert mode in rows, f"{mode} pairs with {rule} in the auditor but has no table row"
        assert rule in rows[mode], f"table row for {mode} does not name {rule}"


BUILD_TASK = """# tasks.md

## T08: Add process task "StageATask1" to "StageA"
- taskTypeId: 3d48f889-d4d3-4dde-82d2-68725901641e
- activation-mode: {mode}
- entry-rule: current-stage-entered
- lane: 0
- isRequired: true
- runOnlyOnce: false
"""


def _audit(tmp_path: Path, text: str, lane: str) -> tuple[int, str]:
    plan = tmp_path / "tasks.md"
    plan.write_text(text, encoding="utf-8")
    done = subprocess.run(
        [sys.executable, str(AUDIT), str(plan), "--lane", lane],
        capture_output=True, text=True,
    )
    return done.returncode, done.stdout + done.stderr


def test_build_lane_flags_a_wrong_pair(tmp_path):
    code, out = _audit(tmp_path, BUILD_TASK.format(mode="sequential"), "build")
    assert code == 1
    assert "cannot carry `entry-rule: current-stage-entered`" in out


def test_build_lane_flags_a_mode_outside_the_vocabulary(tmp_path):
    code, out = _audit(tmp_path, BUILD_TASK.format(mode="conditional"), "build")
    assert code == 1
    assert "is not a task mode" in out


def test_build_lane_passes_a_correct_pair(tmp_path):
    code, out = _audit(tmp_path, BUILD_TASK.format(mode="parallel"), "build")
    assert code == 0, out


def test_build_lane_allows_resolved_registry_keys(tmp_path):
    """`taskTypeId` is forbidden on the plan lane and required on the build lane."""
    plan_code, plan_out = _audit(tmp_path, BUILD_TASK.format(mode="parallel"), "plan")
    assert plan_code == 1
    assert "forbidden key 'taskTypeId'" in plan_out


def test_build_lane_ignores_condition_entries(tmp_path):
    """§4.7 condition entries carry `rule-type:`, not `entry-rule:` — auditing
    them as tasks reported a missing `entry-rule:` line on every correct plan."""
    text = BUILD_TASK.format(mode="parallel") + """
## T22: Add task-entry condition for "StageATask1" in "StageA" — current-stage-entered (Entry Rule 1)
- activation-mode: parallel
- rule-type: current-stage-entered
"""
    code, out = _audit(tmp_path, text, "build")
    assert code == 0, out
