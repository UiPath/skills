"""Guard for the draft-scoped lineage check.

`sdd_check.py` validates a FINALIZED SDD's render contract, so using it as a
design-task criterion would fail 7 currently-passing runs (6 of
loan-origination's 9 successes) whose drafts legitimately lack finalized shape.
This checker keeps only the part a draft must get right regardless of polish:
every consumed `=vars.<name>` has a producer.

Scope was set by measurement, not taste. An earlier version also checked that
every `=vars` reference had a §Case Variables row; the sweep over 37 collected
drafts caught it firing on a loan-origination draft that scored 0.944 SUCCESS
(direct producer references are legal), so that check was removed. The
lineage-only version is clean on all 21 passing drafts and flags 4 failing ones.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from draft_lineage_check import issues_for  # noqa: E402

HEADER = (
    "### Case Variables\n\n"
    "| Name | Category | Type | sourceTriggers | sourceFields | Default | Description |\n"
    "|---|---|---|---|---|---|---|\n"
)


def sdd(rows: str, body: str) -> str:
    return HEADER + rows + "\n" + body


def test_variable_with_no_producer_is_reported():
    text = sdd(
        "| offerAmount | Variable | string |  |  |  | comp |\n",
        "**Inputs:** =vars.offerAmount\n",
    )
    found = issues_for(text)
    assert found and "offerAmount" in found[0]


def test_a_default_closes_it():
    text = sdd(
        "| offerAmount | Variable | string |  |  | 0 | comp |\n",
        "**Inputs:** =vars.offerAmount\n",
    )
    assert issues_for(text) == []


def test_a_producer_row_closes_it():
    text = sdd(
        "| offerAmount | Variable | string |  |  |  | comp |\n",
        "**Outputs:** amount -> offerAmount\n\n**Inputs:** =vars.offerAmount\n",
    )
    assert issues_for(text) == []


def test_an_In_argument_is_closed_at_case_start():
    text = sdd(
        "| offerAmount | In | string |  |  |  | comp |\n",
        "**Inputs:** =vars.offerAmount\n",
    )
    assert issues_for(text) == []


def test_a_trigger_source_closes_it():
    text = sdd(
        "| offerAmount | Variable | string | T02 | body.amount |  | comp |\n",
        "**Inputs:** =vars.offerAmount\n",
    )
    assert issues_for(text) == []


def test_no_variables_table_is_silent_not_a_lineage_finding():
    """A draft with no data contract is a shape question, not a lineage one."""
    assert issues_for("# just prose, no table\n") == []


def test_a_direct_producer_reference_is_not_flagged():
    """The removed mapping check fired on a 0.944 SUCCESS draft; stay silent here."""
    text = sdd(
        "| known | Variable | string |  |  | x | declared |\n",
        '**Inputs:** `<- "Offer"."Send Letter".envelopeId`\n**IF:** =js:vars.$xref("Offer","Send Letter","envelopeId")\n',
    )
    assert issues_for(text) == []
