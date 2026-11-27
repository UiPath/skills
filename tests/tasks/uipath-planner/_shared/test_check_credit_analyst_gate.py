import os
import sys


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_credit_analyst_gate import has_credit_analyst_gate


def test_accepts_documented_role_token_in_executable_gate():
    assert has_credit_analyst_gate(
        'Recipient: Expression:=js:vars.loanAmount > 5000000 ? '
        '"Role:CreditAnalyst" : "Role:Underwriter"'
    )


def test_rejects_persona_only_credit_analyst_statement():
    assert not has_credit_analyst_gate(
        "Credit Analyst reviews loans above $5M; the Underwriter handles the rest."
    )


def test_accepts_the_rule_written_from_the_low_side():
    assert has_credit_analyst_gate(
        'Recipient: Expression:=js:vars.loanAmount <= 5000000 ? "Role:Underwriter" : "Role:CreditAnalyst"'
    )
    assert has_credit_analyst_gate(
        "**Assignment rule:** if `loanAmount` is at or below $5M, assign to the Underwriter, otherwise assign to the Credit Analyst."
    )


def test_accepts_underscored_and_decimal_amounts():
    assert has_credit_analyst_gate('Recipient: =js:vars.loanAmount > 5_000_000 ? "Role:CreditAnalyst" : "Role:Underwriter"')
    assert has_credit_analyst_gate('Recipient: =js:vars.loanAmount > 5000000.00 ? "Role:CreditAnalyst" : "Role:Underwriter"')


def test_rejects_the_low_side_rule_inverted():
    assert not has_credit_analyst_gate(
        'Recipient: =js:vars.loanAmount <= 5000000 ? "Role:CreditAnalyst" : "Role:Underwriter"'
    )
