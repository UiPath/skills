"""Shared loader for the doc examples the maestro-bpmn contract guards assert.

The guards in this directory pin examples agents copy verbatim. Loading them
in one place keeps them from drifting apart on which section is canonical or
on how the XML block is extracted. `minimal_example` is the canonical
`## A complete minimal file`; `section_blocks` serves guards bound to a
different section, whose fragments need the namespace wrapper.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    ROOT
    / "skills"
    / "uipath-maestro-bpmn"
    / "references"
    / "structural-bpmn.md"
)
SECTION = "## A complete minimal file"
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "uipath": "http://uipath.org/schema/bpmn",
}


def minimal_example() -> ET.Element:
    """Parse the single XML block under the canonical section."""

    content = REFERENCE.read_text(encoding="utf-8")
    _, heading, remainder = content.partition(SECTION)
    assert heading, f"structural-bpmn.md is missing its {SECTION!r} section"
    section = remainder.partition("\n## ")[0]

    blocks = []
    for xml in re.findall(r"```xml\n(.*?)\n```", section, re.DOTALL):
        try:
            blocks.append(ET.fromstring(xml))
        except ET.ParseError:
            continue
    assert len(blocks) == 1, (
        f"expected exactly one parseable XML block under {SECTION!r}, "
        f"found {len(blocks)}"
    )
    return blocks[0]


REGISTRY_REFERENCE = (
    ROOT
    / "skills"
    / "uipath-maestro-bpmn"
    / "references"
    / "registry-workflow.md"
)


def section_blocks(reference: Path, section: str) -> list[ET.Element]:
    """Every XML block under one heading, wrapped so fragments resolve.

    A block that will not parse even wrapped is a defect in the doc: agents
    copy these verbatim, and an unescaped `<placeholder>` in an attribute
    makes the file not well-formed.
    """

    content = reference.read_text(encoding="utf-8")
    _, heading, remainder = content.partition(section)
    assert heading, f"{reference.name} is missing its {section!r} section"
    body = remainder.partition("\n## ")[0]

    blocks, broken = [], []
    for xml in re.findall(r"```xml\n(.*?)\n```", body, re.DOTALL):
        wrapped = f'<doc xmlns:uipath="{NS["uipath"]}" xmlns:bpmn="{NS["bpmn"]}">{xml}</doc>'
        try:
            blocks.append(ET.fromstring(wrapped))
        except ET.ParseError as error:
            broken.append((xml.splitlines()[0][:80], str(error)))
    assert not broken, f"{reference.name} {section!r} has XML that does not parse: {broken}"
    assert blocks, f"{reference.name} has no XML block under {section!r}"
    return blocks
