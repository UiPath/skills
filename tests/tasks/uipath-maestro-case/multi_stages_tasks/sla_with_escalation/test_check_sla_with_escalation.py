"""Regression tests for the exact conditional-SLA expression matcher."""

from check_sla_with_escalation import _matches_priority_expression


def test_priority_expression_accepts_only_the_requested_equality():
    assert _matches_priority_expression(
        '=js:vars.priority === "Urgent"', "Urgent"
    )
    assert _matches_priority_expression(
        "=js: vars.priority === 'Standard' ", "Standard"
    )


def test_priority_expression_rejects_lookalike_predicates():
    assert not _matches_priority_expression(
        '=js:vars.otherPriority === "Urgent"', "Urgent"
    )
    assert not _matches_priority_expression(
        '=js:vars.priority !== "Urgent" && "==="', "Urgent"
    )
    assert not _matches_priority_expression(
        '=js:vars.priority === "Urgent" || true', "Urgent"
    )
