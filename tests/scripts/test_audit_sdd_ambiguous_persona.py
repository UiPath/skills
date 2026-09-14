"""Guard: a task persona names exactly one role, never "A or B".

`skills/uipath-planner/scripts/case/audit_sdd.py` is the design lane's gate. An
either/or persona is a routing rule the author stated but never modelled — the
reader cannot tell who owns the task and no guard picks between the roles at run
time. The loan-origination judge names this defect directly: "a stated business
rule is not genuinely modeled as a guarded task or gate. The draft describes the
>$5M ownership threshold in prose/persona scope while the underwriting task
itself has no guard or conditional routing."

The rule lives in the gate rather than the prose for the reason recorded in
test_audit_sdd_picker_route.py: this lane's reading budget is saturated, and a
gate costs the agent no reading while naming the defect exactly.

Calibrated against 144 collected SDD artifacts: fires on 3, all of them failing
loan-origination drafts (judge 0.52, 0.50, 0.55) across BOTH harnesses, and on
zero passing artifacts. Four earlier structural hypotheses were rejected because
they fired on drafts scoring up to 0.99.

    python3 -m pytest tests/scripts/test_audit_sdd_ambiguous_persona.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "skills" / "uipath-planner" / "scripts" / "case" / "audit_sdd.py"

spec = importlib.util.spec_from_file_location("audit_sdd", AUDIT)
assert spec and spec.loader
audit_sdd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_sdd)


TASK_TABLE = """\
#### Tasks

| # | Task Name | Type | Activation Mode | Starts When | Required | Run Only Once | Persona | SLA |
|---|---|---|---|---|---|---|---|---|
| 1 | Run Credit Check | execute-connector-activity | sequential | stage enters | Yes | Yes | system | — |
| 2 | Complete Underwriting | action | sequential | after Run Credit Check | Yes | Yes | {persona} | — |
"""


def test_either_or_persona_is_flagged():
    found = audit_sdd.ambiguous_personas(
        TASK_TABLE.format(persona="Underwriter or Credit Analyst")
    )
    assert found == ["Underwriter or Credit Analyst"]


def test_single_persona_is_clean():
    assert audit_sdd.ambiguous_personas(TASK_TABLE.format(persona="Underwriter")) == []


def test_system_persona_is_clean():
    assert audit_sdd.ambiguous_personas(TASK_TABLE.format(persona="system")) == []


def test_task_name_containing_or_is_not_flagged():
    """Only the Persona column is inspected — task names legitimately say "or".

    "Await Signed Offer or Decline" and "Resume or Close Out Case" are real task
    names from passing drafts; scanning every cell flagged them and cost the
    check its precision.
    """
    table = TASK_TABLE.replace("Complete Underwriting", "Await Signed Offer or Decline")
    assert audit_sdd.ambiguous_personas(table.format(persona="Recruiter")) == []


def test_persona_column_found_under_alternate_headers():
    for header in ("Assignee", "Owner", "Role", "Responsible"):
        table = TASK_TABLE.replace("| Persona |", f"| {header} |")
        found = audit_sdd.ambiguous_personas(
            table.format(persona="Underwriter or Credit Analyst")
        )
        assert found == ["Underwriter or Credit Analyst"], header


def test_no_table_is_clean():
    assert audit_sdd.ambiguous_personas("# SDD — Something\n\nProse only.\n") == []
