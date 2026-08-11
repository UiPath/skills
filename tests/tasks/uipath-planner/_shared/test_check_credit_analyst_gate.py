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
