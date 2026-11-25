"""case-sdd-check.mjs: a sound case SDD prints OK; each mechanical defect the graders fail prints its FAIL line.

Run: pytest tests/tasks/uipath-planner/_shared/test_case_sdd_check.py -v
"""

import re
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
SCRIPT = REPO / "skills" / "uipath-planner" / "scripts" / "case-sdd-check.mjs"
SOUND = REPO / "tests" / "tasks" / "uipath-maestro-case" / "sla_from_sdd" / "fixtures" / "sdd.md"
START_TASK = "| stage: Intake | Intake SLA | Breached | start-task | Chase Missing Paperwork | — |"


@pytest.fixture
def check(tmp_path):
    def run(text):
        path = tmp_path / "sdd.md"
        path.write_text(text, encoding="utf-8")
        done = subprocess.run(["node", str(SCRIPT), str(path)], capture_output=True, text=True, encoding="utf-8", check=False)
        return done.returncode, done.stdout
    return run


@pytest.fixture
def sound():
    return SOUND.read_text(encoding="utf-8")


def test_a_sound_case_sdd_prints_ok(check, sound):
    rc, out = check(sound)
    assert rc == 0, out
    assert out.startswith("OK:")


def test_a_start_task_row_marked_interrupting_no_fails(check, sound):
    assert START_TASK in sound
    rc, out = check(sound.replace(START_TASK, START_TASK.replace("| — |", "| No |")))
    assert rc == 1
    assert "start-task takes Interrupting —" in out


def test_a_placeholder_row_for_a_scope_without_an_sla_fails(check, sound):
    row = "| stage: Settlement | Settlement SLA | Breached | notify-only | — | — | No work on breach is described. |"
    assert row in sound
    rc, out = check(sound.replace(row, row + "\n| stage: Payout | — | — | — | — | — | Payout has no SLA. |"))
    assert rc == 1
    assert "a scope with no SLA gets no row" in out


def test_a_notify_only_row_naming_a_target_fails(check, sound):
    row = "| stage: Assessment | Assessment SLA | At-Risk | notify-only | — | — |"
    rc, out = check(sound.replace(row, row.replace("notify-only | — |", "notify-only | Claims Handlers |")))
    assert rc == 1
    assert "notify-only takes Target —" in out


def test_a_renamed_map_column_fails(check, sound):
    rc, out = check(sound.replace("| Target | Interrupting | Rationale |", "| Target | Interrupts active work? | Rationale |", 1))
    assert rc == 1
    assert "SLA Response Map header is" in out


def test_a_task_without_its_envelope_fails(check, sound):
    rc, out = check(sound.replace("**Task envelope**", "**Envelope**", 1))
    assert rc == 1
    assert "task 'Validate Claim Details': missing **Task envelope**" in out


def test_a_stage_without_its_design_rationale_fails(check, sound):
    first_stage = re.search(r"^### Stage 1:[\s\S]*?(?=^### )", sound, re.M)[0]
    assert "**Design Rationale:**" in first_stage
    rc, out = check(sound.replace(first_stage, first_stage.replace("**Design Rationale:**", "**Why:**"), 1))  # the grader reads the stage block whole
    assert rc == 1
    assert "missing **Design Rationale:**" in out


def test_a_type_outside_the_task_types_fails(check, sound):
    rc, out = check(sound.replace("**Type:** Stage", "**Type:** Secondary", 1))
    assert rc == 1
    assert "**Type:** Secondary is not 'Stage' or one of the 17 task types" in out


def test_a_backticked_task_type_fails_with_the_bare_form(check, sound):
    rc, out = check(sound.replace("**Type:** api-workflow", "**Type:** `api-workflow`", 1))
    assert rc == 1
    assert "write it bare: **Type:** api-workflow" in out


def test_a_human_task_with_a_persona_and_no_recipient_fails(check, sound):
    rc, out = check(sound.replace("**Recipient:** Role: Claims Handlers", "**Recipient:** —", 1))
    assert rc == 1
    assert "Recipient — (write **Recipient:** Role:" in out


def test_a_missing_first_heading_fails(check, sound):
    rc, out = check(sound.split("\n", 1)[1])
    assert rc == 1
    assert "first line is not '# SDD — <Case Name>'" in out


def test_an_sla_status_change_without_its_map_row_fails(check, sound):
    rc, out = check(sound.replace(START_TASK, START_TASK.replace("Intake SLA", "Intake Window"), 1))
    assert rc == 1
    assert "no start-task / enter-stage SLA Response Map row has SLA 'Intake SLA'" in out


DRAFTS = sorted((REPO / "tests" / "tasks" / "uipath-planner" / "case").glob("*/fixtures/sdd.draft.md"))


@pytest.mark.parametrize("draft", DRAFTS, ids=lambda p: p.parent.parent.name)
def test_a_template_draft_passes_draft_mode(draft):
    done = subprocess.run(["node", str(SCRIPT), "--draft", str(draft)], capture_output=True, text=True, encoding="utf-8", check=False)
    assert done.returncode == 0, done.stdout
    assert done.stdout.startswith("OK (draft):")


def test_a_draft_off_the_template_fails_draft_mode(tmp_path):
    draft = tmp_path / "sdd.draft.md"
    draft.write_text("# Sample — Solution Design Draft\n\n## Stages & Tasks\n\n### 1. Intake\n\n### 2. Review\n", encoding="utf-8")
    done = subprocess.run(["node", str(SCRIPT), "--draft", str(draft)], capture_output=True, text=True, encoding="utf-8", check=False)
    assert done.returncode == 1
    for line in ("first line is not '# SDD — <Case Name>'", "missing heading '## Section 2: Stages & Tasks'",
                 "no '### Stage <N>: <Name>' block", "a stage heading reads '### <N>. <Name>'"):
        assert line in done.stdout
