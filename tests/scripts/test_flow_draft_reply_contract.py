"""Guard the draft-mode reply contract: skill templates, flavors and the evals that grade them.

Run with:
    pytest tests/scripts/test_flow_draft_reply_contract.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "skills" / "uipath-maestro-flow" / "references"
SW_REFS = ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-flow" / "references"
TASKS = ROOT / "tests" / "tasks" / "uipath-maestro-flow"

DRAFT_TASKS = [
    TASKS / "smoke" / "draft_skeleton.yaml",
    TASKS / "smoke" / "draft_skeleton_scheduled.yaml",
    TASKS / "smoke" / "draft_request_is_gate.yaml",
    TASKS / "smoke" / "draft_word_is_not_gate.yaml",
    TASKS / "smoke" / "auto_build_final_report.yaml",
    TASKS / "interactive" / "draft_build_after_gate" / "draft_build_after_gate.yaml",
]

STATUSES = (
    "`<resource> in <folder>`",
    "`<A> in <folder> or <B> in <folder>, which one? Build it takes the first`",
    "`none yet, create it or name one`",
    "`not checked`",
    "`no resource needed`",
)
OPTIONS = (
    "Is this the flow you want?",
    "1. **Build it**: make every step work.",
    "2. **Change it**: tell me what to add, remove, or move.",
    "3. **Keep it**: stop here with this outline.",
)


def _flat(text: str) -> str:
    """The text every flavor block resolves to, with the block markers dropped."""
    return re.sub(r"<!--skill-flavor:[a-z0-9-]+:(?:start|end)-->\n?", "", text)


def _outside_flavor_blocks(text: str) -> str:
    return re.sub(
        r"<!--skill-flavor:([a-z0-9-]+):start-->.*?<!--skill-flavor:\1:end-->",
        "",
        text,
        flags=re.S,
    )


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_gate_reply_shape() -> None:
    text = _flat(_read(REFS / "gate-reply-template.md"))
    assert "<Name>: outline ready<, uploaded> (draft mode)." in text
    assert "<box label exactly as its .step() label spells it>: <status>" in text
    for line in OPTIONS:
        assert line in text, line
    for status in STATUSES:
        assert status in text, status


def test_gate_reply_bans_links_and_questions() -> None:
    text = _outside_flavor_blocks(_read(REFS / "gate-reply-template.md"))
    assert "never a link or in backticks" in _flat(_read(REFS / "gate-reply-template.md"))
    assert "not with a pick-list or question tool" in text
    assert "Write nothing before that line" in text
    assert "When the request forbids upload, the one sentence never mentions the upload" in text


def test_gate_box_lines_skip_control_nodes() -> None:
    text = _outside_flavor_blocks(_read(REFS / "gate-reply-template.md"))
    assert "not the trigger, a branch, a switch, a loop, a parallel or the end" in text


def test_studio_web_gate_reply() -> None:
    text = _flat(_read(SW_REFS / "gate-reply-template.md"))
    assert "<Name>: outline ready (draft mode)." in text
    assert ", uploaded" not in text
    assert '"The outline is on the canvas." when the target is the open flow' in text
    assert '"Open <Name>.flow from the Explorer to see the outline."' in text


def test_final_report_shape() -> None:
    text = _flat(_read(REFS / "final-report-template.md"))
    assert "<Name>: built, validated<, uploaded><, run> (<draft|auto> mode)." in text
    assert "at most 5 lines" in text
    for label in ("Needs:", "Assumed:", "Unverified:"):
        assert label in text, label
    assert "`not runnable yet` in place of `validated`" in text


def test_final_report_mode_rules() -> None:
    text = _outside_flavor_blocks(_read(REFS / "final-report-template.md"))
    assert "Write `(draft mode)` for any run that stopped at a draft gate" in text
    assert "Write `(auto mode)` only in a run that never stopped at a gate." in text
    assert "Never write `(auto mode)` after a draft gate." in text
    assert "Write at most five change lines." in text


def test_studio_web_final_report() -> None:
    text = _flat(_read(SW_REFS / "final-report-template.md"))
    assert "<Name>: built, <validated|not validated><, run> (<draft|auto> mode)." in text
    assert "/solution/<Project>/<Name>.flow" in text


def test_path_line_is_bare() -> None:
    for path in (REFS / "final-report-template.md", SW_REFS / "final-report-template.md"):
        assert "never a link or in backticks" in _read(path), path


@pytest.mark.parametrize("path", DRAFT_TASKS, ids=lambda p: p.stem)
def test_draft_task_exists_with_required_tags(path: Path) -> None:
    text = _read(path)
    assert re.search(r"^tags: \[uipath-maestro-flow, (smoke|e2e),", text, re.M)
    assert '"mode:build"' in text


@pytest.mark.parametrize("path", [p for p in DRAFT_TASKS if "gate" in p.stem or "skeleton" in p.stem], ids=lambda p: p.stem)
def test_gate_task_judges_pin_the_contract(path: Path) -> None:
    text = _read(path)
    assert "Is this the flow you want?" in text
    assert "outline ready" in text


@pytest.mark.parametrize("name", ["auto_build_final_report", "draft_build_after_gate"])
def test_final_report_task_judges_pin_the_contract(name: str) -> None:
    path = next(p for p in DRAFT_TASKS if p.stem == name)
    text = _read(path)
    assert ": built, validated" in text
    assert ("(auto mode)" if name.startswith("auto") else "(draft mode)") in text
    assert "at most five" in text


def test_task_judges_accept_both_studio_web_path_lines() -> None:
    for name in ("draft_skeleton", "draft_skeleton_scheduled"):
        text = _read(TASKS / "smoke" / f"{name}.yaml")
        assert "The outline is on the canvas." in text
        assert "from the Explorer to" in text
    text = _read(DRAFT_TASKS[-1])
    assert "The outline is on the canvas." in text
    assert "from the Explorer to" in text
