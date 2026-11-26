#!/usr/bin/env python3
"""Which staged fixtures are sound and which are broken on purpose.

Read by `test_fixtures_are_well_formed.py` (the offline checks) and by
`validate_fixtures.py` (the CLI's own verdict, on the smoke runner). One list,
because a fixture repaired or added has to move in both places at once.
"""

from __future__ import annotations

from pathlib import Path

SUITE = Path(__file__).resolve().parent.parent

# Fixtures that are broken on purpose: the task is to repair them, so `uip rules validate` and
# the graders' own profile check are expected to refuse them. Listed rather than matched on the
# path, so a new broken fixture has to be declared here instead of passing by naming itself
# "repair".
DELIBERATELY_BROKEN = {
    # DMN 1.3 rather than 1.5, an output name with a space, a malformed FEEL cell, and an
    # entry-points.json out of step with the .dmn. Moving it to 1.5 is part of the repair.
    "smoke/repair_invalid/fixtures/RiskRules",
    "smoke/graph_repair/fixtures/LoanRules",  # dangling requirement, requirement cycle
}


def projects() -> list[Path]:
    """Every staged BusinessRules project in the suite."""
    return sorted(p.parent for p in SUITE.rglob("project.uiproj") if "__pycache__" not in p.parts)


def rel(project: Path) -> str:
    return project.relative_to(SUITE).as_posix()


def is_sound(project: Path) -> bool:
    return rel(project) not in DELIBERATELY_BROKEN
