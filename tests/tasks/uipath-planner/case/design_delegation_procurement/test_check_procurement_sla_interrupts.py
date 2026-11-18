import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_procurement_sla_interrupts import (
    check_canonical_stage_sla,
    check_withdrawn_entry,
    declared_sla_titles,
    sdd_task_activation,
    sections_by_target,
    sla_references,
    stage_section,
)


def test_duplicate_task_names_are_resolved_by_stage():
    """Same task name in two stages keys on (stage, task), never on name alone."""
    sdd = """
### Stage 1: Intake

##### Task 1.1: Review

**Activation Mode:** parallel

**Entry Condition:**

| WHEN | IF |
|---|---|
| current-stage-entered | — |

### Stage 2: Decision

##### Task 2.1: Review

**Activation Mode:** sequential

**Entry Condition:**

| WHEN | IF |
|---|---|
| runs-sequentially | — |
"""

    contracts = sdd_task_activation(sdd)
    assert contracts[("Intake", "Review")] == ("parallel", "current-stage-entered")
    assert contracts[("Decision", "Review")] == ("sequential", "runs-sequentially")


def test_sla_table_title_does_not_replace_canonical_stage_sla_field():
    shorthand = """
#### Stage SLA
| SLA | At-Risk Display Name |
|---|---|
| 2 d | Intake SLA |
"""

    with pytest.raises(SystemExit, match="must declare exactly"):
        check_canonical_stage_sla(shorthand, "Intake")


def test_sla_references_skip_prose_shorthand_without_quoted_args():
    sdd = """
| S2 | SLA Escalation | sla-status-change for any primary-stage breach |
| S3 | Case SLA Review | sla-status-change(root, SupplierApplication Case SLA) |
| sla-status-change("Intake","Intake SLA") | — | Intake SLA breach |
"""

    references = sla_references(sdd)
    assert references == [(4, ["Intake", "Intake SLA"])]


def test_sla_references_count_every_call_on_a_line():
    """A rollup row naming two SLAs yields both, not only the first."""
    sdd = '| S2 | sla-status-change("Intake","Intake SLA"), sla-status-change("Close","Close SLA") |\n'

    assert sla_references(sdd) == [
        (1, ["Intake", "Intake SLA"]),
        (1, ["Close", "Close SLA"]),
    ]


def test_sla_references_reject_or_joined_when_cell():
    """One trigger per WHEN cell: an OR-joined cell is named, not half-counted."""
    sdd = (
        '| sla-status-change("Intake","Intake SLA") OR '
        'sla-status-change("Close","Close SLA") | — | Yes | Any phase breach |\n'
    )

    with pytest.raises(SystemExit, match="OR-joins several sla-status-change"):
        sla_references(sdd)


def test_stage_heading_variants_are_recognized():
    sdd = """
### Primary Stage 1: Intake

**SLA Title:** Intake SLA

### Secondary Stage S1: Withdrawn

body

### Secondary Stage: SLA Escalation

body
"""

    sections = sections_by_target(sdd)
    assert {"root", "intake", "withdrawn", "sla escalation"} <= set(sections)
    assert "SLA Title" in sections["intake"]
    assert "body" in stage_section(sdd, "Withdrawn")


WITHDRAWN_TEMPLATE = """
### Business Events

| Name | Description | Payload Schema |
|---|---|---|
| Supplier Withdrawn | Supplier withdraws through the supplier portal. | — |

### Secondary Stage: Withdrawn (`withdrawn`)

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|---|---|---|---|
| {when} | — | Yes | Supplier withdrawal received |
"""


@pytest.mark.parametrize(
    "when", ['api-event("Supplier Withdrawn")', "wait-for-connector"]
)
def test_withdrawn_entry_accepts_business_event_or_connector(when):
    check_withdrawn_entry(WITHDRAWN_TEMPLATE.format(when=when))


def test_withdrawn_entry_rejects_non_event_rule():
    with pytest.raises(SystemExit, match="not entered by the global"):
        check_withdrawn_entry(WITHDRAWN_TEMPLATE.format(when="user-selected-stage"))


def test_declared_sla_titles_accept_case_sla_title_metadata_label():
    sdd = """
| Case SLA Title | SupplierApplication Case SLA |
| SLA Title | Intake SLA |
"""

    titles = declared_sla_titles(sdd)
    assert "supplierapplication case sla" in titles
    assert "intake sla" in titles
