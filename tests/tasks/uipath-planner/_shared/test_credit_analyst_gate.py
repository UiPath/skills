import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_credit_analyst_gate import has_credit_analyst_gate


@pytest.mark.parametrize(
    "text",
    (
        "Assign Credit Analyst for loans >$5M; Underwriter otherwise",
        'underwritingOwner = loanAmount > 5000000 ? "Credit Analyst" : "Underwriter"',
        "Above $5 million, route the review to a Credit Analyst",
        "Loans in excess of $5M require Credit Analyst review",
        "Underwriter handles loans at or below $5M, while above $5M assign Credit Analyst",
        "Above $5M assign Credit Analyst, not Underwriter",
        "Assign Credit Analyst instead of Underwriter for loans over $5M",
    ),
)
def test_high_side_gate_is_accepted_in_either_phrase_order(text):
    assert has_credit_analyst_gate(text)


@pytest.mark.parametrize(
    "text",
    (
        "Credit Analyst handles loans at or below $5M; Underwriter above $5M",
        'loanAmount <= 5000000 ? "Credit Analyst" : "Underwriter"',
        "Credit Analyst persona; Underwriter handles loans >$5M",
        "Loans >$5M go to Underwriter; loans <=$5M go to Credit Analyst",
        "Underwriter handles loans above $5M; Credit Analyst handles the rest",
        "| Credit Analyst | Underwriting (loans >$5M only) | Reviews credit analysis |",
        "Credit Analyst must not handle loans over $5M",
        "Do not assign loans >$5M to Credit Analyst",
        "Above $5M, Credit Analyst must not be assigned",
        "Credit Analyst reviews every loan",
    ),
)
def test_inverted_or_descriptive_gate_is_rejected(text):
    assert not has_credit_analyst_gate(text)
