"""Every full XML skeleton in the maestro-bpmn skill must parse.

Agents copy these verbatim, and the failures this catches are invisible to
`uip maestro bpmn validate` -- a duplicated attribute or an unbound prefix
fails at `ET.parse`, which is what the task checkers and two task prompts run.
Both have shipped here: `xmlns:xsi` went missing when an example moved, and
then was declared twice when it was restored.

Scoped to blocks that open with an XML declaration. Fragments elsewhere in the
docs are illustrative and legitimately do not resolve their prefixes alone.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "uipath-maestro-bpmn"


def _full_documents() -> list[tuple[str, str]]:
    found = []
    for path in sorted(SKILL.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for block in re.findall(r"```xml\n(.*?)\n```", text, re.DOTALL):
            if block.lstrip().startswith("<?xml"):
                found.append((str(path.relative_to(ROOT)), block))
    return found


def test_the_skill_ships_full_skeletons() -> None:
    """Guards the guard: a rename must not silently empty this suite."""

    assert _full_documents(), "no full XML skeleton found to check"


@pytest.mark.parametrize(
    "relative_path,document",
    _full_documents(),
    ids=[f"{p}#{i}" for i, (p, _d) in enumerate(_full_documents())],
)
def test_full_skeleton_is_well_formed(relative_path: str, document: str) -> None:
    try:
        ET.fromstring(document)
    except ET.ParseError as error:
        pytest.fail(f"{relative_path}: {error}")


def _prefixes_used(text: str) -> set[str]:
    """Namespace prefixes appearing on elements or attributes in XML blocks."""

    used: set[str] = set()
    for block in re.findall(r"```xml\n(.*?)\n```", text, re.DOTALL):
        used |= set(re.findall(r"<([A-Za-z][\w.-]*):", block))
        used |= set(re.findall(r"\s([A-Za-z][\w.-]*):[\w.-]+=", block))
    return {p for p in used if p not in {"xml", "xmlns"}}


@pytest.mark.parametrize(
    "path",
    [p for p in sorted(SKILL.rglob("*.md")) if "```xml" in p.read_text(encoding="utf-8")],
    ids=lambda p: str(p.name),
)
def test_skeleton_declares_every_prefix_its_fragments_use(path: Path) -> None:
    """An agent pastes this file's fragments into this file's skeleton.

    The skeleton lost `xmlns:xsi` when an example moved; the file still used
    `xsi:type` in four fragments, so anyone following the docs produced
    `unbound prefix`. `validate` does not catch it -- `ET.parse` does.
    """

    text = path.read_text(encoding="utf-8")
    skeletons = [
        b for b in re.findall(r"```xml\n(.*?)\n```", text, re.DOTALL)
        if b.lstrip().startswith("<?xml")
    ]
    if not skeletons:
        pytest.skip("no full skeleton in this file")
    declared = set(re.findall(r"xmlns:([\w.-]+)=", " ".join(skeletons)))
    missing = sorted(_prefixes_used(text) - declared)
    assert not missing, (
        f"{path.name}: fragments use prefixes the skeleton never declares: "
        f"{missing} -- pasting them yields 'unbound prefix'"
    )
