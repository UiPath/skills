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


def test_gate_reply_rules() -> None:
    text = _outside_flavor_blocks((REFS / "gate-reply-template.md").read_text())
    assert "for every box's `.task()` id" in text
    assert "each changed box's `name` attribute, decoded" in text
    assert "carries no new user instruction and only resumes" in text
    assert "ending in `which one?`" in text


def test_draft_skeleton_rules() -> None:
    text = _outside_flavor_blocks((REFS / "draft-skeleton.md").read_text())
    assert "A value the request leaves open" in text
    assert "read as [SKILL.md](../SKILL.md#workflow) step 9 says" in text
    assert "search the target for each box's `id=" in text
    assert "whose only job is to receive, read or capture it" in text


def test_skill_step_9_rules() -> None:
    text = _outside_flavor_blocks((REFS.parent / "SKILL.md").read_text())
    assert "read it in full once `validate` passes" in text
    assert "Resume only:" in text


def test_studio_web_flavor_rules() -> None:
    sw = ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn"
    assert "The baseline is the compile of `.flow-sdk/original/<Name>.bpmn`" in (sw / "SKILL.md").read_text()
    assert "the block's `cd` and `mkdir` lines" in (sw / "references" / "draft-skeleton.md").read_text()
    assert "rebuild the baseline as the [Validation loop]" in (sw / "references" / "gate-reply-template.md").read_text()


def test_final_report_rules() -> None:
    text = _outside_flavor_blocks((REFS / "final-report-template.md").read_text())
    assert "carries no new user instruction and only resumes" in text


def test_path_line_is_bare() -> None:
    sw = ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-bpmn" / "references"
    for name in ("gate-reply-template.md", "final-report-template.md"):
        for path in (REFS / name, sw / name):
            assert "never a link or in backticks" in path.read_text(), path
