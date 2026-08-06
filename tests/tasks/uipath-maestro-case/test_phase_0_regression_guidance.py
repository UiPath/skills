from pathlib import Path


PHASE_0_GUIDE = (
    Path(__file__).resolve().parents[3]
    / "skills/uipath-maestro-case/references/phase-0-interview.md"
)
SKILL = Path(__file__).resolve().parents[3] / "skills/uipath-maestro-case/SKILL.md"


def test_direct_finalization_separates_manual_picker_from_automatic_decision_routes():
    guide = PHASE_0_GUIDE.read_text(encoding="utf-8")

    assert "**Manual picker repair (only for a person-selected lane):**" in guide
    assert "**Automatic decision-route repair (never use a picker):**" in guide
    assert "Do not apply the manual-picker completion rule to an automatic decision route." in guide


def test_direct_finalization_requires_literal_inventory_and_executable_role_gate():
    guide = PHASE_0_GUIDE.read_text(encoding="utf-8")

    assert "display names are immutable literal tokens" in guide
    assert "`QA/QC` must remain `QA/QC`" in guide
    assert '`**Recipient:** =js:vars.loanAmount > 5000000 ? "Role:Credit Analyst" : "Role:Underwriter"`' in guide


def test_compact_plan_requires_a_separate_literal_lane_line_for_each_sequential_task():
    guide = PHASE_0_GUIDE.read_text(encoding="utf-8")

    assert "each T-entry must contain its own literal `- lane: <n>` line" in guide


def test_critical_rules_make_automatic_routes_and_threshold_assignments_non_optional():
    skill = SKILL.read_text(encoding="utf-8")

    assert "Automatic decision lanes use a decision-keyed entry" in skill
    assert "actual task block must carry a guarded owner/recipient/assignment" in skill


def test_compact_no_build_contract_preserves_requirement_literals_and_at_risk_escalations():
    guide = PHASE_0_GUIDE.read_text(encoding="utf-8")

    assert "literal requirements inventory" in guide
    assert "never rename or paraphrase a requirement-provided stage or task name" in guide
    assert "at-risk escalation notification" in guide
