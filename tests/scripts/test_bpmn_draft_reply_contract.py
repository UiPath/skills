"""Guard the draft-mode reply rules every flavor inherits.

Run with:
    pytest tests/scripts/test_bpmn_draft_reply_contract.py
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "skills" / "uipath-maestro-bpmn" / "references"


def _outside_flavor_blocks(text: str) -> str:
    """Text every flavor inherits: drop each named flavor block."""
    return re.sub(
        r"<!--skill-flavor:([a-z0-9-]+):start-->.*?<!--skill-flavor:\1:end-->",
        "",
        text,
        flags=re.S,
    )


def test_gate_reply_waits_for_a_validated_target_and_survives_a_resume() -> None:
    text = _outside_flavor_blocks((REFS / "gate-reply-template.md").read_text())
    assert "`validate` reported `Status: Valid` on the target `.bpmn` and the target contains" in text
    assert "When a turn resumes after an interruption that came after you wrote this reply" in text
    assert "the two candidates ending in `which one?`" in text
    assert "the target contains `<bpmn:task id=\"<id>\"` for every box's `.task()` id; `merge`'s counts cannot show this" in text
    assert "On a *Change it* round, also find each changed box's new `name`." in text


def test_build_it_assumes_open_values_and_reads_the_report_template() -> None:
    text = _outside_flavor_blocks((REFS / "draft-skeleton.md").read_text())
    assert "A value the request leaves open" in text
    assert "name it under `Assumed`" in text
    assert "End the turn with the [final report](final-report-template.md), read as [SKILL.md](../SKILL.md#workflow) step 9 says" in text
    assert "search the target for each box's `<bpmn:task id=\"<id>\"`" in text


def test_skill_step_9_reads_the_report_template() -> None:
    text = _outside_flavor_blocks((REFS.parent / "SKILL.md").read_text())
    assert "read it in full once `validate` passes or fails only that way, before any upload" in text
    assert "A turn that resumes after an interruption that came after the report or a gate reply was written resends that message unchanged and whole" in text


def test_studio_web_merges_against_the_seeded_baseline() -> None:
    text = (ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn" / "SKILL.md").read_text()
    assert "**The baseline is step 1's compile of the unedited source, never a copy of the target or the edited file.**" in text
    assert "When the gate's outline search finds a box\n  missing, rebuild the baseline the same way and run steps 3 and 4 again." in text
    sw = (ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn" / "references" / "draft-skeleton.md").read_text()
    assert "the block's `cd` and `mkdir` lines and all of step 1's lines in one command, before you write the skeleton" in sw
    gate = (ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn" / "references" / "gate-reply-template.md").read_text()
    assert "rebuild the baseline as the [Validation loop](../SKILL.md#validation-loop) says, run its steps 3 and 4 once more" in gate


def test_final_report_survives_a_resume() -> None:
    text = _outside_flavor_blocks((REFS / "final-report-template.md").read_text())
    assert "When a turn resumes after an interruption that came after you wrote this report" in text
