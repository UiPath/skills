"""Guard the Case draft-mode reply contract: skill templates, flavors and the evals that grade them.

Run with:
    pytest tests/tasks/uipath-maestro-case/_shared/test_draft_reply_contract.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SKILL = ROOT / "skills" / "uipath-maestro-case"
REFS = SKILL / "references"
SW_REFS = ROOT / "skill-flavors" / "studioweb" / "uipath-maestro-case" / "references"
TASKS = ROOT / "tests" / "tasks" / "uipath-maestro-case" / "draft"

GATE_TASKS = ("draft_skeleton", "draft_skeleton_timer", "draft_request_is_gate", "draft_build_after_gate")
REPORT_TASKS = ("auto_build_final_report", "draft_build_after_gate")
DRAFT_TASKS = (*GATE_TASKS[:3], "draft_word_is_not_gate", *REPORT_TASKS)

STATUSES = (
    "`<resource> in <folder>`",
    "`<A> in <folder> or <B> in <folder>, which one? Build it takes the first`",
    "`none yet, create it or name one`",
    "`not checked`",
    "`no resource needed`",
)
OPTIONS = (
    "Is this the case you want?",
    "1. **Build it**: make every task work.",
    "2. **Change it**: tell me what to add, remove, or move.",
    "3. **Keep it**: stop here with this outline.",
)


def _flat(text: str) -> str:
    """The text every flavor block resolves to, with the block markers dropped."""
    return re.sub(r"<!--skill-flavor:[a-z0-9-]+:(?:start|end)-->\n?", "", text)


def _outside_flavor_blocks(text: str) -> str:
    return re.sub(r"<!--skill-flavor:([a-z0-9-]+):start-->.*?<!--skill-flavor:\1:end-->", "", text, flags=re.S)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _task(name: str) -> str:
    return _read(TASKS / name / f"{name}.yaml")


def test_skill_routes_a_draft_request() -> None:
    text = _read(SKILL / "SKILL.md")
    assert "## Draft first" in text
    for ref in ("draft-skeleton.md", "gate-reply-template.md", "final-report-template.md"):
        assert f"references/{ref}" in text, ref
    assert "The [Stop rule](#workflow) wins over a draft." in text
    assert "A [draft](#draft-first) skips this step." in text


def test_skeleton_is_blank_boxes_with_no_registry_and_no_sdd() -> None:
    text = _outside_flavor_blocks(_read(REFS / "draft-skeleton.md"))
    assert "`.task('<Action> [<Kind>]', (t) => t.unresolved('<kind>'))`" in text
    assert "**Make no registry calls.**" in text
    assert "Do not invoke the planner and write no `sdd.md`" in text
    assert "Route on a case variable or an input, never on a box." in text
    assert "one `TASK_NOT_CONFIGURED` warning per box" in text


def test_every_unresolved_kind_in_the_table_is_one_the_sdk_accepts() -> None:
    kinds = set(re.findall(r"\| `'([a-z-]+)'` \|", _read(REFS / "draft-skeleton.md")))
    assert kinds, "Box kinds table not found"
    assert kinds <= {
        "process", "agent", "rpa", "api-workflow", "case-management", "function",
        "action", "connector", "wait-for-connector",
    }, kinds


def test_gate_reply_shape() -> None:
    text = _flat(_read(REFS / "gate-reply-template.md"))
    assert "<Name>: outline ready<, uploaded> (draft mode)." in text
    assert "<stage name> / <box label exactly as its .task() name spells it>: <status>" in text
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
    assert "not the trigger, a stage on its own, a rule or the case's completion" in text


def test_studio_web_gate_reply() -> None:
    text = _flat(_read(SW_REFS / "gate-reply-template.md"))
    assert "<Name>: outline ready (draft mode)." in text
    assert ", uploaded" not in text
    assert '"The outline is on the canvas." when the target is the open plan' in text
    assert '"Open <Project> from the Explorer to see the outline."' in text


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
    assert "<Name>: built, validated<, run> (<draft|auto> mode)." in text
    assert "/solution/<Project>/<Plan>" in text
    assert "never run `uip solution upload`" in text


def test_path_line_is_bare() -> None:
    for path in (REFS / "final-report-template.md", SW_REFS / "final-report-template.md"):
        assert "never a link or in backticks" in _read(path), path


def test_studio_web_overrides_only_name_canonical_blocks() -> None:
    marker = re.compile(r"<!--skill-flavor:([a-z0-9-]+):start-->")
    for name in ("draft-skeleton.md", "gate-reply-template.md", "final-report-template.md"):
        canonical = set(marker.findall(_read(REFS / name)))
        override = set(marker.findall(_read(SW_REFS / name)))
        assert override <= canonical, (name, override - canonical)


@pytest.mark.parametrize("name", DRAFT_TASKS)
def test_draft_task_exists_with_required_tags(name: str) -> None:
    text = _task(name)
    assert re.search(r"^tags: \[uipath-maestro-case, (smoke|e2e),", text, re.M)
    assert '"mode:build"' in text
    assert '"lifecycle:generate"' in text


@pytest.mark.parametrize("name", GATE_TASKS)
def test_gate_task_judges_pin_the_contract(name: str) -> None:
    text = _task(name)
    assert "Is this the case you want?" in text
    assert "outline ready" in text


@pytest.mark.parametrize("name", REPORT_TASKS)
def test_final_report_task_judges_pin_the_contract(name: str) -> None:
    text = _task(name)
    assert ": built, validated" in text
    assert ("(auto mode)" if name.startswith("auto") else "mode).`") in text
    assert "A sixth such line fails this item." in text


def test_task_judges_accept_both_studio_web_path_lines() -> None:
    for name in ("draft_skeleton", "draft_skeleton_timer", "draft_build_after_gate"):
        text = _task(name)
        assert "The outline is on the canvas." in text
        assert "from the" in text and "Explorer to see the outline." in text
