"""Every hand-kept copy of the case task-type set agrees with the CLI's declaration (MST-15834).

The declaration is `uip maestro case task-types list`; `task_types.json` is its
snapshot. A type added to or removed from the CLI fails here until the guide,
the conformance checklist and both `sdd_check.py` gates follow it.

    python3 -m pytest tests/tasks/uipath-maestro-case/_shared/test_task_types.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import task_types  # noqa: E402

REPO = task_types.REPO
CHECKLIST = REPO / "skills" / "uipath-planner" / "references" / "case" / "case-sdd-conformance-checklist.md"
GATES = [
    REPO / "tests" / "tasks" / "uipath-maestro-case" / "_shared" / "sdd_check.py",
    REPO / "tests" / "tasks" / "uipath-planner" / "_shared" / "sdd_check.py",
]
COUNT_WORDS = {
    9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
    16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
}


def _count_word() -> str:
    count = len(task_types.authorable())
    assert count in COUNT_WORDS, f"{count} authorable types: add the word for it to COUNT_WORDS"
    return COUNT_WORDS[count]


def _task_types_section(text: str) -> str:
    start = text.find("### Task types")
    assert start >= 0, f"{task_types.GUIDE.relative_to(REPO)} has no '### Task types' heading"
    end = text.find("\n### ", start + 1)
    return text[start:] if end < 0 else text[start:end]


def test_snapshot_lists_are_disjoint_and_point_at_authorable_types():
    authorable = set(task_types.authorable())
    studio = set(task_types.studio_web_only())
    wrong = task_types.not_task_types()
    assert authorable and wrong  # studio may be empty: every real type authorable
    assert not authorable & studio
    for row in wrong:
        assert row["Spelling"] not in authorable | studio, row
        assert row["PlanType"] in authorable, row


def test_snapshot_matches_the_installed_cli():
    live = task_types.from_cli()
    if live is None:
        pytest.skip(
            "installed CLI has no `uip maestro case task-types list`; the snapshot is checked "
            "against it once @uipath/cli@dev carries the command"
        )
    assert task_types.lists(live) == task_types.lists(task_types.load()), (
        "the CLI's task-type lists differ from task_types.json; run "
        "`python3 tests/tasks/uipath-maestro-case/_shared/task_types.py --refresh` and follow the failures below"
    )
    for key in task_types.VERSIONS:
        assert re.fullmatch(r"\d+\.\d+\.\d+", str(live.get(key, ""))), f"{key} missing or malformed: {live.get(key)!r}"


def test_guide_table_lists_exactly_the_authorable_types():
    section = _task_types_section(task_types.GUIDE.read_text())
    rows = re.findall(r"^\| `([a-z-]+)` \|", section, re.M)
    assert sorted(rows) == sorted(task_types.authorable()), (
        f"{task_types.GUIDE.relative_to(REPO)} § Task types: missing "
        f"{sorted(set(task_types.authorable()) - set(rows))}, not in the declaration "
        f"{sorted(set(rows) - set(task_types.authorable()))}"
    )


def test_guide_states_the_authorable_count():
    section = _task_types_section(task_types.GUIDE.read_text())
    assert f"exactly these {_count_word()} literals" in section


def test_guide_not_authorable_block_is_written_from_the_declaration():
    block = task_types.guide_block(task_types.GUIDE.read_text())
    assert block is not None, "the guide has no task-types block markers"
    assert block == task_types.render_guide_block(), (
        "the guide's not-authorable block is stale; run "
        "`python3 tests/tasks/uipath-maestro-case/_shared/task_types.py --write-guide`"
    )


def test_conformance_checklist_states_the_authorable_count():
    assert f"one of the {_count_word()} literals" in CHECKLIST.read_text()


def _load_gate(gate: Path):
    spec = importlib.util.spec_from_file_location(f"sdd_check_{gate.parts[-3]}", gate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_conformance_checklist_names_a_detail_block_for_every_authorable_type():
    item = re.search(r"and the detail block its type requires(.*?)\n  \d+\.", CHECKLIST.read_text(), re.S)
    assert item, "the checklist's detail-block item moved; update this test"
    named = set(re.findall(r"[a-z]+(?:-[a-z]+)*", item.group(1)))
    missing = sorted(set(task_types.authorable()) - named)
    assert not missing, f"{CHECKLIST.relative_to(REPO)} names no detail block for {missing}"


@pytest.mark.parametrize("gate", GATES, ids=lambda p: p.parts[-3])
def test_sdd_check_gate_checks_a_detail_block_for_every_authorable_type(gate: Path):
    missing = sorted(set(task_types.authorable()) - set(_load_gate(gate).TASK_DETAIL_MARKERS))
    assert not missing, f"{gate.relative_to(REPO)} TASK_DETAIL_MARKERS has no entry for {missing}"


@pytest.mark.parametrize("gate", GATES, ids=lambda p: p.parts[-3])
def test_sdd_check_gate_accepts_exactly_the_authorable_types(gate: Path):
    module = _load_gate(gate)
    assert sorted(module.TASK_TYPES) == sorted(task_types.authorable()), (
        f"{gate.relative_to(REPO)} TASK_TYPES: missing "
        f"{sorted(set(task_types.authorable()) - set(module.TASK_TYPES))}, extra "
        f"{sorted(set(module.TASK_TYPES) - set(task_types.authorable()))}"
    )


def test_guide_block_omits_the_studio_web_paragraph_when_nothing_is_studio_web_only():
    data = {**task_types.load(), "StudioWebOnly": []}
    block = task_types.render_guide_block(data)
    assert "Studio Web:" not in block
    assert "Never write these as a `Type:` either." in block
