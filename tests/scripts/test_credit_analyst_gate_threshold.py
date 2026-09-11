"""Guard: the >$5M gate check must accept a dollar sign before the digit form.

`tests/tasks/uipath-planner/_shared/check_credit_analyst_gate.py` gates two
planner case tasks (`case_design_loan`, `case_finalize_draft_loan`). Its
threshold pattern carried the optional `$` inside the first alternative only, so
the numeric form could never be preceded by one: "greater than $5,000,000" did
not match while "greater than 5,000,000" did. Designs that named the threshold
the way a credit policy writes it were failed for wording.

Observed in nightly run 2026-09-11_04-17-19 (gpt-5.6-terra,
skill-case-phase-0-loan-origination, 0.89): the SDD carried

    If `requestedAmount` is greater than $5,000,000, assign Complete Credit
    Underwriting to the Credit Analyst; otherwise assign it to the Underwriter.

which names the role, the threshold, the direction and an executable verb in one
clause, and was reported as "no executable high-side Credit Analyst gate".

    python3 -m pytest tests/scripts/test_credit_analyst_gate_threshold.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECKER = (
    REPO
    / "tests"
    / "tasks"
    / "uipath-planner"
    / "_shared"
    / "check_credit_analyst_gate.py"
)

spec = importlib.util.spec_from_file_location("check_credit_analyst_gate", CHECKER)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


def _row(clause: str) -> str:
    """The gate as a Business Rules table row, which is where designs put it."""
    return f"| 1 | Underwriting assignment | {clause} |"


ACCEPTED = [
    "If `requestedAmount` is greater than $5,000,000, assign Complete Credit "
    "Underwriting to the Credit Analyst",
    "If `requestedAmount` > $5,000,000, route underwriting to the Credit Analyst",
    "Loans in excess of $5,000,000 require the Credit Analyst as owner",
    "If `requestedAmount` is greater than 5,000,000, assign the Credit Analyst",
    "Deals over $5M are assigned to the Credit Analyst",
    "Requests above $5 million are routed to the Credit Analyst",
]


def test_every_high_side_phrasing_is_accepted() -> None:
    for clause in ACCEPTED:
        assert gate.has_credit_analyst_gate(_row(clause)), clause


def test_terra_nightly_clause_passes() -> None:
    """The verbatim clause from run 2026-09-11_04-17-19 that was failed."""
    line = _row(
        "If `requestedAmount` is greater than $5,000,000, assign Complete Credit "
        "Underwriting to the Credit Analyst; otherwise assign it to the "
        "Underwriter. A $4M deal is therefore handled by the Underwriter."
    )
    assert gate.has_credit_analyst_gate(line)


def test_low_side_only_is_still_rejected() -> None:
    """Widening the threshold must not weaken the direction requirement."""
    assert not gate.has_credit_analyst_gate(
        _row("Loans at or below $5,000,000 are assigned to the Credit Analyst")
    )


def test_role_without_a_threshold_is_still_rejected() -> None:
    assert not gate.has_credit_analyst_gate(
        _row("Assign Complete Credit Underwriting to the Credit Analyst")
    )


def test_threshold_without_the_role_is_still_rejected() -> None:
    assert not gate.has_credit_analyst_gate(
        _row("If `requestedAmount` is greater than $5,000,000, escalate the deal")
    )
