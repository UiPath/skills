"""Guard the uipath-planner SDD signals a calling skill's host reads.

A caller (a business-analysis skill in another repository) hands `design` a
request and registers the SDD it gets back. It reads only the signals listed in
caller-request-guide.md § SDD Signals a Caller's Host May Read, so a template
that drops or moves one breaks that host without any error here. These checks
hold every template to that list.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLANNER = ROOT / "skills" / "uipath-planner"
TEMPLATES = sorted((PLANNER / "assets" / "templates").glob("*-sdd-template.md"))
CALLER_GUIDE = PLANNER / "references" / "design" / "caller-request-guide.md"

HANDOFF_MARKER = "<!-- planner-handoff:v1 -->"
HANDOFF_HEADING = "## Planner Handoff"
BODY_MARKER = "<!-- planner-sdd-body:v1 -->"
STATUS_ROW = re.compile(r"^\|\s*\*\*Status\*\*\s*\|", re.M)
VALIDATION_ROW = re.compile(r"^\|\s*\*\*Template validation\*\*\s*\|", re.M)
NUMBERED_H2 = re.compile(r"^##\s+(?:Section\s+)?\d", re.I)


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def test_every_sdd_template_is_covered() -> None:
    assert len(TEMPLATES) >= 7, [t.name for t in TEMPLATES]


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.name)
def test_template_carries_the_handoff_signals(template: Path) -> None:
    text = template.read_text(encoding="utf-8")
    assert text.count(HANDOFF_MARKER) == 1
    assert sum(line.strip() == HANDOFF_HEADING for line in text.splitlines()) == 1
    assert len(STATUS_ROW.findall(text)) == 1
    assert len(VALIDATION_ROW.findall(text)) == 1


@pytest.mark.parametrize("template", TEMPLATES, ids=lambda p: p.name)
def test_body_marker_separates_front_matter_from_the_body(template: Path) -> None:
    lines = _lines(template)
    marker_lines = [i for i, line in enumerate(lines) if BODY_MARKER in line]
    assert len(marker_lines) == 1, "exactly one body marker"
    marker = marker_lines[0]
    assert lines[marker].strip() == BODY_MARKER, "the marker sits on a line of its own"

    above = [line for line in lines[:marker] if line.startswith("## ")]
    assert "## Table of Contents" in above, "the table of contents is front matter"
    assert HANDOFF_HEADING in above, "the handoff header is front matter"
    assert not [h for h in above if NUMBERED_H2.match(h)], "no numbered body section above the marker"

    following = next(line for line in lines[marker + 1 :] if line.strip())
    assert NUMBERED_H2.match(following), f"the first body section follows the marker, got {following!r}"


def test_caller_guide_declares_every_signal_the_templates_carry() -> None:
    guide = CALLER_GUIDE.read_text(encoding="utf-8")
    for signal in ("planner-design-request: v1", "planner-design-result: v1", HANDOFF_MARKER, BODY_MARKER):
        assert signal in guide, signal
    assert "**Template validation**" in guide and "**Status**" in guide


def test_caller_guide_documents_every_request_key_it_shows() -> None:
    guide = CALLER_GUIDE.read_text(encoding="utf-8")
    block = re.search(r"```text\nplanner-design-request: v1\n(.*?)```", guide, re.S)
    assert block, "the request example block"
    keys = {line.split(":", 1)[0] for line in block.group(1).splitlines() if line.strip()}
    documented = set(re.findall(r"^\| `([a-z-]+)`(?:, `([a-z-]+)`)? \|", guide, re.M))
    table_keys = {k for pair in documented for k in pair if k}
    assert keys == table_keys, (keys - table_keys, table_keys - keys)
