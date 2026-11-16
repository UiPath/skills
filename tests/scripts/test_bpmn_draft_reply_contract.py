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
    assert "only after `validate` reported `Status: Valid` on the target" in text
    assert "When a turn resumes after an interruption that came after you wrote this reply" in text


def test_build_it_assumes_open_values_and_reads_the_report_template() -> None:
    text = _outside_flavor_blocks((REFS / "draft-skeleton.md").read_text())
    assert "A value the request leaves open" in text
    assert "name it under `Assumed`" in text
    assert "Read [final-report-template.md](final-report-template.md) in full" in text
