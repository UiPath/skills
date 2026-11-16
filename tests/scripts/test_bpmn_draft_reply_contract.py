"""Guard the draft-mode reply rules and the build-after-gate upload criterion.

Run with:
    pytest tests/scripts/test_bpmn_draft_reply_contract.py
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "skills" / "uipath-maestro-bpmn" / "references"
TASK = (
    ROOT
    / "tests"
    / "tasks"
    / "uipath-maestro-bpmn"
    / "interactive"
    / "draft_build_after_gate"
    / "draft_build_after_gate.yaml"
)


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
    assert "When a turn resumes after an interruption" in text


def test_build_it_assumes_open_values_and_reads_the_report_template() -> None:
    text = _outside_flavor_blocks((REFS / "draft-skeleton.md").read_text())
    assert "A value the request leaves open" in text
    assert "name it under `Assumed`" in text
    assert "Read [final-report-template.md](final-report-template.md) in full" in text


def _upload_pattern() -> re.Pattern[str]:
    """The upload criterion's pattern, read without a YAML dependency.

    The guard job installs pytest only, so take the single-quoted scalar on the
    `command_pattern:` line that follows the upload criterion's description.
    """
    text = TASK.read_text()
    block = text.split('description: "The shape and the built process were both uploaded', 1)[1]
    match = re.search(r"^\s*command_pattern: '((?:[^']|'')*)'\s*$", block, flags=re.M)
    assert match, "upload criterion has no single-quoted command_pattern"
    return re.compile(match.group(1).replace("''", "'"))


def test_upload_criterion_counts_uploads_and_studio_web_target_writes_only() -> None:
    pattern = _upload_pattern()
    counted = [
        "uip solution upload ShippingQuoteSolution --output json",
        "uip maestro bpmn merge /tmp/d/edited/Process.bpmn --original .flow-sdk/original/Process.bpmn "
        "--baseline /tmp/d/baseline/Process.bpmn -o Process.bpmn",
        "uip maestro bpmn compile .flow-sdk/Process.bpmn.ts -o Process.bpmn",
        "uip maestro bpmn compile s.bpmn.ts -o /solution/ShippingQuote/Process.bpmn",
    ]
    not_counted = [
        "uip maestro bpmn compile .flow-sdk/Process.bpmn.ts -o /tmp/d/edited/Process.bpmn",
        "uip maestro bpmn compile .flow-sdk/Process.bpmn.ts -o /tmp/d/baseline/Process.bpmn",
        "uip maestro bpmn compile ShippingQuote.bpmn.ts -o ShippingQuoteSolution/ShippingQuote/ShippingQuote.bpmn",
        "uip maestro bpmn compile s.bpmn.ts -o Process.bpmn.bak",
        "uip maestro bpmn validate Process.bpmn --output json",
    ]
    for command in counted:
        assert pattern.search(command), command
    for command in not_counted:
        assert not pattern.search(command), command
