"""Guard: the § SLA Response Map authors both statuses for every (Scope, SLA).

`skills/uipath-planner/scripts/case/audit_sdd.py` is the design lane's gate, and the map is
"THE single authored source of SLA responses". Absent a stated response a status is still
authored as `notify-only` with Target and Interrupting `—` — an omitted row is an unauthored
response, not a way to write "nothing happens".

The rule lives in the gate because prose alone did not carry it: run 2026-09-08_05-15-45
(skill-case-sla-sdd-response-map) authored the Triage SLA's At-Risk row only, left an HTML
comment justifying the omission, passed the gate with `AUDIT OK`, and then failed the graded
contract. The prose rule read at SLA level ("Source states no response -> both statuses
notify-only"), so an SLA with a stated at-risk response looked exempt; the gate reads it at
status level, where the contract actually lives.

Calibrated against every SDD fixture under tests/tasks: fires on zero of them. The two that
carry a response map (uipath-maestro-case sla_from_sdd, timer_connector_from_sdd) already
author both statuses, including `Breached | notify-only | — | —` rows whose rationale is
"No work on breach is described" — the convention this check pins.

    python3 -m pytest tests/scripts/test_audit_sdd_sla_row_closure.py
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


MAP = """\
### SLA Response Map

| Scope | SLA | Status | Response | Target | Interrupting | Rationale |
|-------|-----|--------|----------|--------|--------------|-----------|
{rows}

### Case Triggers
"""

CASE_BOTH = (
    "| case | Case SLA | At-Risk | notify-only | — | — | Heads-up only. |\n"
    "| case | Case SLA | Breached | notify-only | — | — | No work on breach is described. |"
)


def gaps(rows: str) -> list[str]:
    return audit_sdd.sla_map_status_gaps(MAP.format(rows=rows))


def test_missing_breached_row_is_flagged():
    found = gaps("| stage: Triage | Triage SLA | At-Risk | notify-only | — | — | Email at 80%. |")
    assert len(found) == 1
    assert "stage: Triage / Triage SLA authors no Breached row" in found[0]


def test_missing_at_risk_row_is_flagged():
    found = gaps("| stage: Assess | Assess SLA | Breached | start-task | Senior Assessor Check | — | Local follow-up. |")
    assert len(found) == 1
    assert "authors no At-Risk row" in found[0]


def test_both_statuses_authored_is_clean():
    assert gaps(CASE_BOTH) == []


def test_a_stated_response_on_one_status_does_not_exempt_the_other():
    """The 2026-09-08 defect: at-risk was stated, breached was "not asked for", row omitted."""
    rows = (
        "| stage: Triage | Triage SLA | At-Risk | notify-only | — | — | Email the triage team at 80%. |\n"
        "| stage: Assess | Assess SLA | At-Risk | notify-only | — | — | Defaulted. |\n"
        "| stage: Assess | Assess SLA | Breached | start-task | Senior Assessor Check | — | Local follow-up. |"
    )
    found = gaps(rows)
    assert len(found) == 1
    assert "Triage SLA authors no Breached row" in found[0]


def test_slug_qualifier_does_not_split_a_pair():
    """`stage: Triage (`triage`)` and `stage: Triage` name the same scope."""
    rows = (
        "| stage: Triage (`triage`) | Triage SLA | At-Risk | notify-only | — | — | Email at 80%. |\n"
        "| stage: Triage | Triage SLA | Breached | notify-only | — | — | Nothing further asked. |"
    )
    assert gaps(rows) == []


def test_template_placeholder_row_is_ignored():
    placeholder = (
        "| <case \\| stage: <StageName>> | <that target's SLA Title> | <At-Risk \\| Breached> "
        "| <notify-only \\| start-task> | <—> | <—> | <why> |"
    )
    assert gaps(placeholder) == []


def test_absent_section_is_clean():
    """A case with no SLA at all legitimately omits the section."""
    assert audit_sdd.sla_map_status_gaps("# SDD — Something\n\n### Case Triggers\n") == []


def test_four_hash_heading_is_still_parsed():
    section = MAP.replace("### SLA Response Map", "#### SLA Response Map")
    found = audit_sdd.sla_map_status_gaps(
        section.format(rows="| case | Case SLA | At-Risk | notify-only | — | — | Heads-up. |")
    )
    assert len(found) == 1
