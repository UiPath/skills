"""Shared loader for the canonical BPMN example in the maestro-bpmn skill.

The contract guards in this directory all assert properties of the same
`## A complete minimal file` example, which agents copy verbatim. Loading it
in one place keeps them from drifting apart on which section is canonical or
on how the XML block is extracted.
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
