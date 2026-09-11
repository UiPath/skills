import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_boolean_routing import branch_values  # noqa: E402


def test_accepts_equivalent_case_expression_spellings():
    plan = {
        "conditions": [
            {"conditionExpression": "=js:vars.approved === true"},
            {"conditionExpression": "approved == false"},
        ]
    }

    assert branch_values(plan) == {True, False}


def test_does_not_accept_unrelated_boolean_expressions():
    plan = {
        "conditions": [
            {"conditionExpression": "=js:vars.other === true"},
            {"conditionExpression": "=js:vars.approved !== false"},
        ]
    }

    assert branch_values(plan) == set()
