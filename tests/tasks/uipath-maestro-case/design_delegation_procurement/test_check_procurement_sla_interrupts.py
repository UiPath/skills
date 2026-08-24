import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_procurement_sla_interrupts import (
    check_canonical_stage_sla,
    declared_sla_titles,
    sections_by_target,
    sla_references,
    stage_section,
    task_lane,
    task_section,
)


def test_duplicate_task_names_are_resolved_by_stage():
    plan = """
## T01: task "Review"

- stage: Intake
- activation-mode: parallel

## T02: task "Review"

- stage: Decision
- activation-mode: sequential
"""

    assert "activation-mode: parallel" in task_section(plan, "Review", "Intake")
    assert "activation-mode: sequential" in task_section(plan, "Review", "Decision")
    with pytest.raises(SystemExit, match="ambiguous tasks.md T-entry"):
        task_section(plan, "Review")


def test_plain_compact_fields_are_resolved_by_stage():
    plan = """
## T01: task "Review"

stage: Intake
activation-mode: parallel
lane: 1
"""

    assert "stage: Intake" in task_section(plan, "Review", "Intake")
    assert task_lane(plan, "Review") == 1


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


def test_declared_sla_titles_accept_case_sla_title_metadata_label():
    sdd = """
| Case SLA Title | SupplierApplication Case SLA |
| SLA Title | Intake SLA |
"""

    titles = declared_sla_titles(sdd)
    assert "supplierapplication case sla" in titles
    assert "intake sla" in titles
