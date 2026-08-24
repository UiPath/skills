"""Guard: the sdd_check.py twins in the two eval suites stay byte-identical.

``sdd_check.py`` is deliberately duplicated per-suite (per-suite ``_shared``
scoping — see ``tests/pytest.ini``): the planner suite grades design-lane
SDDs with it, the maestro-case suite grades fixture SDDs. This test fails the
moment the copies drift, so a change either lands in both or the duplication
is collapsed on purpose.

Runs with no model and no tenant:

    python3 -m pytest tests/tasks/uipath-planner/_shared/test_shared_twins.py
"""

from __future__ import annotations

from pathlib import Path

TASKS_ROOT = Path(__file__).resolve().parents[2]


def test_sdd_check_twins_are_identical() -> None:
    case_copy = TASKS_ROOT / "uipath-maestro-case" / "_shared" / "sdd_check.py"
    planner_copy = TASKS_ROOT / "uipath-planner" / "_shared" / "sdd_check.py"
    assert case_copy.is_file(), f"missing twin: {case_copy}"
    assert planner_copy.is_file(), f"missing twin: {planner_copy}"
    assert case_copy.read_bytes() == planner_copy.read_bytes(), (
        "sdd_check.py twins have drifted — apply the change to BOTH copies "
        "(tests/tasks/uipath-maestro-case/_shared/ and "
        "tests/tasks/uipath-planner/_shared/) or collapse the duplication"
    )
