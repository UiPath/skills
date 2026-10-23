"""Every hand-kept copy of the per-slot rule types stays inside the CLI's declaration (MST-16782).

The declaration is `uip maestro case rule-types list`; `rule_types.json` is its
snapshot. A copy may allow FEWER rules than a slot can hold (planner policy),
never more: a rule outside the declaration is one the platform does not place
in that slot, and for exit and completion slots `case validate` would not say so.

Held here: the planner's § Lifecycle gates table (rules and Marks complete) and
the gate sets of both `sdd_check.py` copies. Not yet held: the case skill's
condition plugin references and case-schema.md, which restate the slots in
prose.

    python3 -m pytest tests/tasks/uipath-maestro-case/_shared/test_rule_types.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rule_types  # noqa: E402

REPO = Path(__file__).resolve().parents[4]
GATES = [
    REPO / "tests" / "tasks" / "uipath-maestro-case" / "_shared" / "sdd_check.py",
    REPO / "tests" / "tasks" / "uipath-planner" / "_shared" / "sdd_check.py",
]

# The sdd_check constant for each declared scope.
GATE_SETS = {
    "TASK_ENTRY": "task-entry",
    "STAGE_ENTRY": "stage-entry",
    "STAGE_EXIT": "stage-exit",
    "STAGE_COMPLETION": "stage-completion",
    "RETURN_TO_ORIGIN_COMPLETION": "stage-completion",
    "CASE_EXIT": "case-exit",
    "CASE_COMPLETION": "case-completion",
}
MARKS = {"Yes": True, "No": False, "—": None}


def test_snapshot_matches_the_installed_cli():
    live = rule_types.from_cli()
    if live is None:
        pytest.skip(f"`{' '.join(rule_types.COMMAND)}` is not in the installed CLI")
    assert rule_types.scopes(live) == rule_types.scopes(rule_types.load()), (
        "rule_types.json is stale; run `python3 scripts/refresh-cli-declarations.py`"
    )


def test_every_declared_scope_has_a_guide_row():
    assert set(rule_types.GUIDE_ROWS.values()) == set(rule_types.by_scope())
    assert set(rule_types.lifecycle_rows()) == set(rule_types.GUIDE_ROWS), "§ Lifecycle gates rows do not match the six slots"


@pytest.mark.parametrize("gate", rule_types.GUIDE_ROWS, ids=rule_types.GUIDE_ROWS.get)
def test_guide_gate_allows_only_rules_the_slot_holds(gate: str):
    _, rules = rule_types.lifecycle_rows()[gate]
    scope = rule_types.GUIDE_ROWS[gate]
    extra = rules - rule_types.by_scope()[scope]
    assert not extra, f"§ Lifecycle gates '{gate}' allows {sorted(extra)}, which `{scope}` cannot hold"


@pytest.mark.parametrize("gate", rule_types.GUIDE_ROWS, ids=rule_types.GUIDE_ROWS.get)
def test_guide_marks_complete_matches_the_slot(gate: str):
    marks, _ = rule_types.lifecycle_rows()[gate]
    scope = rule_types.GUIDE_ROWS[gate]
    assert MARKS.get(marks, "?") == rule_types.marks_complete()[scope], (
        f"§ Lifecycle gates '{gate}' says Marks complete {marks}; `{scope}` declares {rule_types.marks_complete()[scope]}"
    )


def _gate_module(path: Path):
    spec = importlib.util.spec_from_file_location(f"sdd_check_{path.parts[-3]}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("gate", GATES, ids=lambda p: p.parts[-3])
@pytest.mark.parametrize("name", GATE_SETS)
def test_sdd_check_gate_allows_only_rules_the_slot_holds(gate: Path, name: str):
    rules = getattr(_gate_module(gate), name)
    scope = GATE_SETS[name]
    extra = set(rules) - rule_types.by_scope()[scope]
    assert not extra, f"{gate.relative_to(REPO)} {name} allows {sorted(extra)}, which `{scope}` cannot hold"

