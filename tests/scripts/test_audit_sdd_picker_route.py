"""Guard: a picker entry must not carry a deterministic decision route.

`skills/uipath-planner/scripts/case/audit_sdd.py` is the design lane's gate. The rule
lives here rather than in the SDD template because that lane's reading budget is
saturated: a six-line template bullet landed the repair (skill-case-reject-route
0.385 -> 1.000, run 33501174330) but timed out its sibling
skill-case-picker-pairing at the wall, and a three-line version restored the
sibling while leaving reject-route churning 61 commands without producing an SDD
(run 33503717818). A gate costs the agent no reading and names the defect exactly.

    python3 -m pytest tests/scripts/test_audit_sdd_picker_route.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AUDIT = REPO / "skills" / "uipath-planner" / "scripts" / "case" / "audit_sdd.py"

spec = importlib.util.spec_from_file_location("audit_sdd", AUDIT)
audit_sdd = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(audit_sdd)


DECISION_ACTIONS = """##### Task 1.1: Reviewer Decision (`t01`)

**Actions:**

| Button | Maps To | Behavior |
|--------|---------|----------|
| Approve | reviewDecision = "Approve" | Send the application to Award |
| Reject | reviewDecision = "Reject" | Send the application to the Application Rejected lane |
"""


def _sdd(entry_rule: str) -> str:
    return (
        DECISION_ACTIONS
        + f"""
### Secondary Stage: Application Rejected

**Interrupting:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting |
|------|----|--------------|
| {entry_rule} | — | Yes |
"""
    )


def _picker_findings(text: str) -> list[str]:
    return [f for f in audit_sdd.contract_findings(text, {}) if "picker rule cannot carry" in f]


def test_picker_entry_on_a_decision_routed_lane_is_flagged():
    findings = _picker_findings(_sdd("`user-selected-stage`"))
    assert findings, "a decision-routed lane keyed on the picker must be reported"
    assert "Application Rejected" in findings[0]


def test_decision_keyed_entry_on_the_same_lane_is_clean():
    """The negative control: the correct authoring must not be flagged."""
    entry = '`selected-stage-completed("Eligibility Review")`'
    assert _picker_findings(_sdd(entry)) == []


def test_a_picker_lane_no_decision_routes_to_is_clean():
    """A genuine picker lane — nothing in an Actions table names it — stays clean."""
    text = _sdd("`user-selected-stage`").replace("Application Rejected lane", "Award lane")
    assert _picker_findings(text) == []
