"""Guard the canonical BPMN DI shape dimensions in the BPMN skill."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "uipath-maestro-bpmn"
REFERENCE = SKILL / "references" / "structural-bpmn.md"

NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "dc": "http://www.omg.org/spec/DD/20100524/DC",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "uipath": "http://uipath.org/schema/bpmn",
}
WRAPPER = "<root {}>{{}}</root>".format(
    " ".join(f'xmlns:{prefix}="{uri}"' for prefix, uri in NS.items())
)

# Sized to fit contents, so no fixed width/height applies.
SIZED_TO_FIT = {"participant", "lane", "group", "textAnnotation"}


def _dimension_table() -> dict[str, tuple[int, int]]:
    section = REFERENCE.read_text(encoding="utf-8").split(
        "### Canonical shape dimensions",
        maxsplit=1,
    )
    assert len(section) == 2, "structural-bpmn.md lost its canonical dimensions section"
    dimensions: dict[str, tuple[int, int]] = {}
    for row in re.finditer(
        r"^\|\s*(?P<label>.+?)\s*\|\s*(?P<width>\d+)×(?P<height>\d+)\s*\|\s*$",
        section[1],
        re.MULTILINE,
    ):
        size = (int(row.group("width")), int(row.group("height")))
        for name in re.findall(r"`([a-z][A-Za-z]*)`", row.group("label")):
            dimensions[name] = size
    return dimensions


def test_documented_dimensions_match_the_canvas_serializer() -> None:
    dimensions = _dimension_table()
    for element in (
        "task",
        "sendTask",
        "receiveTask",
        "scriptTask",
        "userTask",
        "manualTask",
        "serviceTask",
        "businessRuleTask",
        "callActivity",
        "subProcess",
        "textAnnotation",
    ):
        assert dimensions[element] == (100, 80), element
    for element in (
        "startEvent",
        "endEvent",
        "intermediateCatchEvent",
        "intermediateThrowEvent",
        "boundaryEvent",
    ):
        assert dimensions[element] == (36, 36), element
    for element in (
        "exclusiveGateway",
        "inclusiveGateway",
        "parallelGateway",
        "eventBasedGateway",
        "complexGateway",
    ):
        assert dimensions[element] == (50, 50), element
    assert dimensions["dataObjectReference"] == (36, 50)
    assert dimensions["dataStoreReference"] == (50, 50)


def test_sized_to_fit_elements_are_documented_as_such() -> None:
    section = REFERENCE.read_text(encoding="utf-8").split(
        "Size these to fit their contents",
        maxsplit=1,
    )
    assert len(section) == 2, "structural-bpmn.md lost its sized-to-fit guidance"
    guidance = section[1].split("`uip maestro bpmn format", maxsplit=1)[0]
    for element in ("subProcess", "participant", "lane", "group"):
        assert f"`{element}`" in guidance, element
    assert 'isExpanded="true"' in guidance


def _parse(block: str) -> ET.Element | None:
    """Parse a whole document as-is; wrap a bare fragment so its prefixes bind."""
    candidates = (
        [block] if block.lstrip().startswith("<?xml") else [block, WRAPPER.format(block)]
    )
    for candidate in candidates:
        try:
            return ET.fromstring(candidate)
        except ET.ParseError:
            continue
    return None


def _examples() -> list[ET.Element]:
    roots = []
    for path in sorted(SKILL.rglob("*.md")):
        for block in re.findall(
            r"```xml\n(.*?)\n```",
            path.read_text(encoding="utf-8"),
            re.DOTALL,
        ):
            if "BPMNShape" not in block:
                continue
            root = _parse(block)
            if root is not None:
                roots.append(root)
    return roots


def test_documented_examples_use_canonical_dimensions() -> None:
    dimensions = _dimension_table()
    checked = 0
    for root in _examples():
        tags = {
            element.get("id"): element.tag.split("}")[-1]
            for element in root.iter()
            if element.get("id")
        }
        for shape in root.iter(f"{{{NS['bpmndi']}}}BPMNShape"):
            tag = tags.get(shape.get("bpmnElement"))
            bounds = shape.find("dc:Bounds", NS)
            if tag is None or bounds is None or tag in SIZED_TO_FIT:
                continue
            if tag == "subProcess" and shape.get("isExpanded") == "true":
                continue
            expected = dimensions.get(tag)
            if expected is None:
                continue
            actual = (int(float(bounds.get("width"))), int(float(bounds.get("height"))))
            assert actual == expected, (
                f"{tag} shape {shape.get('bpmnElement')} is {actual[0]}x{actual[1]}, "
                f"expected {expected[0]}x{expected[1]}"
            )
            checked += 1
    assert checked, "no documented BPMNShape example was validated"
