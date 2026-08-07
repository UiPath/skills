import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from check_procurement_sla_interrupts import (
    check_canonical_stage_sla,
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
