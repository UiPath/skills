"""Guard the supported CLI project scaffold in the BPMN skill."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import UUID


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = (
    ROOT
    / "skills"
    / "uipath-maestro-bpmn"
    / "references"
    / "structural-bpmn.md"
)
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "bpmndi": "http://www.omg.org/spec/BPMN/20100524/DI",
    "di": "http://www.omg.org/spec/DD/20100524/DI",
    "uipath": "http://uipath.org/schema/bpmn",
}


def _minimal_example() -> ET.Element:
    section = REFERENCE.read_text(encoding="utf-8").split(
        "## A complete minimal file",
        maxsplit=1,
    )[1]
    match = re.search(r"```xml\n(?P<xml>.*?)\n```", section, re.DOTALL)
    assert match, "structural-bpmn.md is missing its complete minimal XML example"
    return ET.fromstring(match.group("xml"))


def test_minimal_example_has_supported_root_contract() -> None:
    root = _minimal_example()
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


def test_minimal_example_has_integral_flow_and_di() -> None:
    root = _minimal_example()
    process = root.find("bpmn:process", NS)
    assert process is not None

    nodes_by_type = {
        kind: [
            element.attrib["id"]
            for element in list(process)
            if element.tag.rsplit("}", 1)[-1] == kind
        ]
        for kind in ("startEvent", "task", "endEvent")
    }
    assert all(len(ids) == 1 for ids in nodes_by_type.values())
    start_id = nodes_by_type["startEvent"][0]
    task_id = nodes_by_type["task"][0]
    end_id = nodes_by_type["endEvent"][0]
    node_ids = {start_id, task_id, end_id}

    flows = process.findall("bpmn:sequenceFlow", NS)
    assert len(flows) == 2
    flow_ids = {flow.attrib["id"] for flow in flows}
    assert {
        (flow.attrib["sourceRef"], flow.attrib["targetRef"])
        for flow in flows
    } == {
        (start_id, task_id),
        (task_id, end_id),
    }
    incoming_by_node = {
        element.attrib["id"]: {
            incoming.text
            for incoming in element.findall("bpmn:incoming", NS)
            if incoming.text
        }
        for element in list(process)
        if element.attrib.get("id") in node_ids
    }
    outgoing_by_node = {
        element.attrib["id"]: {
            outgoing.text
            for outgoing in element.findall("bpmn:outgoing", NS)
            if outgoing.text
        }
        for element in list(process)
        if element.attrib.get("id") in node_ids
    }
    flow_by_pair = {
        (flow.attrib["sourceRef"], flow.attrib["targetRef"]): flow.attrib["id"]
        for flow in flows
    }
    assert outgoing_by_node[start_id] == {flow_by_pair[(start_id, task_id)]}
    assert incoming_by_node[task_id] == {flow_by_pair[(start_id, task_id)]}
    assert outgoing_by_node[task_id] == {flow_by_pair[(task_id, end_id)]}
    assert incoming_by_node[end_id] == {flow_by_pair[(task_id, end_id)]}

    shapes = root.findall(".//bpmndi:BPMNShape", NS)
    edges = root.findall(".//bpmndi:BPMNEdge", NS)
    assert len(shapes) == len(node_ids)
    assert len(edges) == len(flow_ids)
    assert {shape.attrib["bpmnElement"] for shape in shapes} == node_ids
    assert {edge.attrib["bpmnElement"] for edge in edges} == flow_ids
    assert all(len(edge.findall("di:waypoint", NS)) >= 2 for edge in edges)


def test_variable_and_migration_examples_use_serializer_attributes() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    variables_section = text.split("## Variables (`BPMN.Variables`)", maxsplit=1)[1]
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

    assert '<uipath:migrationVersion version="11.5" />' in variables_section
    assert "<uipath:migrationVersion value=" not in variables_section
