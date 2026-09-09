"""Doc-vs-gate consistency: the repair case-design-lane-guide.md prescribes must satisfy BOTH gates.

`§ Resumption` step 3(b) tells finalization how to convert a picker-entered lane into a
decision-routed one. That repair has to clear two independent gates at once — the task's
`check_reject_route.py`, and `audit_sdd.py`, which the skill runs before the `ready` flip.
Nothing tied the two together, and they disagreed: the auditor's own finding says to "give
the origin the matching Marks Stage Complete: No diverting exit", while `§ Lifecycle gates`
allows `Marks Complete: No` ONLY with `selected-tasks-completed` / `wait-for-connector` —
so the obvious `required-tasks-completed | No` row satisfies the grader and is rejected by
the auditor as a schema error. An agent following the prose landed between them.

This test pins the shape that clears both, so a future edit to either side fails here
rather than in a 20-minute eval run.

    python3 -m pytest tests/tasks/uipath-planner/case/case_finalize_draft_reject/test_reject_route_repair_shape.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
DRAFT = HERE / "fixtures" / "sdd.draft.md"
CHECKER = HERE / "check_reject_route.py"
AUDIT = REPO / "skills" / "uipath-planner" / "scripts" / "case" / "audit_sdd.py"

PICKER_ROW = "| `user-selected-stage` | — | Yes |"
KEYED_ROW = (
    '| `selected-stage-completed("Eligibility Review")` '
    '| `=js:(vars.reviewDecision === "Reject")` | Yes |'
)
UNGATED_COMPLETION = "| `required-tasks-completed` | — | exit-only | Yes |"
COMPLEMENT_COMPLETION = (
    '| `required-tasks-completed` | `=js:(vars.reviewDecision !== "Reject")` | exit-only | Yes |'
)
# The legal diverting WHEN. `required-tasks-completed` here is the trap this test exists for.
DIVERTING = (
    '| `selected-tasks-completed("Reviewer Decision")` '
    '| `=js:(vars.reviewDecision === "Reject")` | exit-only | No |'
)


def repaired(diverting_row: str = DIVERTING) -> str:
    """The draft with step 3(b)'s four edits applied, and nothing else."""
    text = DRAFT.read_text(encoding="utf-8")
    assert text.count(PICKER_ROW) == 1
    text = text.replace(PICKER_ROW, KEYED_ROW)
    head, sep, rest = text.partition("### Stage 1: Eligibility Review")
    block, sep2, tail = rest.partition("### Stage 2: Award")
    assert block.count(UNGATED_COMPLETION) == 1
    block = block.replace(UNGATED_COMPLETION, COMPLEMENT_COMPLETION + "\n" + diverting_row)
    return head + sep + block + sep2 + tail


def audit(path: Path) -> set[str]:
    out = subprocess.run(
        [sys.executable, str(AUDIT), str(path)], capture_output=True, text=True
    )
    return {line.strip().lstrip("0123456789. ") for line in (out.stdout + out.stderr).splitlines()
            if line.strip().startswith(tuple("0123456789"))}


def grade(tmp_path: Path, scope: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECKER), "--scope", scope],
        cwd=tmp_path, capture_output=True, text=True,
    )


def test_prescribed_repair_passes_the_lane_grader(tmp_path):
    (tmp_path / "sdd.md").write_text(repaired(), encoding="utf-8")
    result = grade(tmp_path, "lane")
    assert result.returncode == 0, result.stdout + result.stderr


def test_prescribed_repair_passes_the_origin_grader(tmp_path):
    """The advisory scope: diverting and completion exits are mutually exclusive."""
    (tmp_path / "sdd.md").write_text(repaired(), encoding="utf-8")
    result = grade(tmp_path, "all")
    assert result.returncode == 0, result.stdout + result.stderr


def test_prescribed_repair_introduces_no_audit_finding(tmp_path):
    """The repair must not trade a grader failure for a gate failure."""
    base = tmp_path / "base.md"
    base.write_text(DRAFT.read_text(encoding="utf-8"), encoding="utf-8")
    fixed = tmp_path / "sdd.md"
    fixed.write_text(repaired(), encoding="utf-8")
    introduced = audit(fixed) - audit(base)
    assert not introduced, f"repair introduced audit findings: {sorted(introduced)}"


def test_prescribed_repair_clears_the_picker_route_finding(tmp_path):
    """audit_sdd.py names this defect; the repair must actually silence it."""
    base = tmp_path / "base.md"
    base.write_text(DRAFT.read_text(encoding="utf-8"), encoding="utf-8")
    fixed = tmp_path / "sdd.md"
    fixed.write_text(repaired(), encoding="utf-8")
    cleared = audit(base) - audit(fixed)
    assert any("picker rule cannot carry a deterministic route" in f for f in cleared), sorted(cleared)


def test_required_tasks_completed_diverting_row_is_rejected_by_the_gate(tmp_path):
    """The trap: it satisfies the grader, so only audit_sdd.py catches it."""
    trap = '| `required-tasks-completed` | `=js:(vars.reviewDecision === "Reject")` | exit-only | No |'
    base = tmp_path / "base.md"
    base.write_text(DRAFT.read_text(encoding="utf-8"), encoding="utf-8")
    fixed = tmp_path / "sdd.md"
    fixed.write_text(repaired(trap), encoding="utf-8")
    assert grade(tmp_path, "all").returncode == 0, "grader is expected to accept the trap row"
    introduced = audit(fixed) - audit(base)
    assert any("illegal" in f for f in introduced), f"gate should reject the trap row: {sorted(introduced)}"


def test_guide_names_the_legal_diverting_when():
    """Step 3(b) must name selected-tasks-completed, not the illegal required-tasks-completed."""
    guide = (REPO / "skills" / "uipath-planner" / "references" / "case"
             / "case-design-lane-guide.md").read_text(encoding="utf-8")
    start = guide.index("**Origin diverting exit**")
    clause = guide[start:guide.index("\n", start)]
    assert "selected-tasks-completed" in clause
    assert "required-tasks-completed | No" in clause  # named as the schema error
