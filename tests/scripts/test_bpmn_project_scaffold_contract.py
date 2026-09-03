"""Guard the supported CLI project scaffold in the BPMN skill."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET  # noqa: F401
from uuid import UUID

from bpmn_doc_example import NS, REFERENCE, minimal_example


def test_minimal_example_has_supported_root_contract() -> None:
    root = minimal_example()
    process = root.find("bpmn:process", NS)
    assert process is not None
    assert process.attrib.get("isExecutable") in (None, "false")
    extensions = process.find("bpmn:extensionElements", NS)
    assert extensions is not None
    assert extensions.find("uipath:variables", NS) is not None
    assert extensions.find("uipath:bindings", NS) is not None

    starts = process.findall("bpmn:startEvent", NS)
    assert len(starts) == 1
    entry_point = starts[0].find(
        "bpmn:extensionElements/uipath:entryPointId",
        NS,
    )
    assert entry_point is not None
    UUID(entry_point.attrib["value"])


def test_minimal_example_has_complete_di_coverage() -> None:
    """Every node has a shape, every flow an edge, every edge two waypoints.

    Deliberately narrow: this pins DI *coverage* over the canonical example
    agents copy, which is what the CLI's `validate` still does not enforce
    (0x0 bounds and single-waypoint edges report Valid on uip 1.202.0).
    It does not re-assert the example's graph wiring -- that is a hand-written
    snippet checked into this repo, not a regression surface.
    """

    root = minimal_example()
    process = root.find("bpmn:process", NS)
    assert process is not None

    # Derived, not whitelisted: adding a node type to the doc example must not
    # surface as a DI-coverage mismatch.
    node_ids = {
        element.attrib["id"]
        for element in process
        if element.get("id")
        and element.tag.rsplit("}", 1)[-1]
        not in ("sequenceFlow", "extensionElements")
    }
    flow_ids = {
        flow.attrib["id"] for flow in process.findall("bpmn:sequenceFlow", NS)
    }
    shapes = root.findall(".//bpmndi:BPMNShape", NS)
    edges = root.findall(".//bpmndi:BPMNEdge", NS)

    assert {shape.attrib["bpmnElement"] for shape in shapes} == node_ids
    assert {edge.attrib["bpmnElement"] for edge in edges} == flow_ids
    assert all(len(edge.findall("di:waypoint", NS)) >= 2 for edge in edges)


def test_variable_and_migration_examples_use_serializer_attributes() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    variables_section = text.split("## Variables (`BPMN.Variables`)", maxsplit=1)[1]
    variables_section = variables_section.split("\n## ", 1)[0]
    match = re.search(r"```xml\n(?P<xml>.*?)\n```", variables_section, re.DOTALL)
    assert match, "structural-bpmn.md is missing its variable declaration example"

    wrapper = ET.fromstring(
        '<root xmlns:uipath="http://uipath.org/schema/bpmn">'
        f"{match.group('xml')}"
        "</root>"
    )
    variables = wrapper.find("uipath:variables", NS)
    assert variables is not None
    declarations = list(variables)
    assert declarations
    assert all(item.attrib.get("id") for item in declarations)
    assert all(item.attrib.get("name") for item in declarations)
    assert all(item.attrib.get("type") for item in declarations)

    # Pin the contract, not a version number: the attribute is `version` and its
    # value is an integer (the reader does Number.parseInt, so "11.5" -> 11).
    assert re.search(
        r'<uipath:migrationVersion version="\d+"\s*/>', variables_section
    ), variables_section
    assert "<uipath:migrationVersion value=" not in variables_section
