"""Guard the supported CLI project scaffold in the BPMN skill."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
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
    (0x0 bounds and single-waypoint edges report Valid on uip 1.203.0).
    """

    root = minimal_example()
    process = root.find("bpmn:process", NS)
    assert process is not None

    # Derived, not whitelisted: adding a node type to the doc example must not
    # surface as a DI-coverage mismatch. Sort every id-bearing process child
    # into the DI it needs, so growing the example moves an id between these
    # sets rather than breaking an assertion.
    EDGE_ELEMENTS = ("sequenceFlow", "association")
    NO_DI_ELEMENTS = ("dataObject", "dataObjectReference", "extensionElements")

    def local(element: ET.Element) -> str:
        return element.tag.rsplit("}", 1)[-1]

    node_ids = {
        element.attrib["id"]
        for element in process
        if element.get("id") and local(element) not in EDGE_ELEMENTS + NO_DI_ELEMENTS
    }
    edge_ids = {
        element.attrib["id"]
        for element in process
        if element.get("id") and local(element) in EDGE_ELEMENTS
    }
    shapes = root.findall(".//bpmndi:BPMNShape", NS)
    edges = root.findall(".//bpmndi:BPMNEdge", NS)

    assert {shape.attrib["bpmnElement"] for shape in shapes} == node_ids
    assert {edge.attrib["bpmnElement"] for edge in edges} == edge_ids
    assert all(len(edge.findall("di:waypoint", NS)) >= 2 for edge in edges)


def test_variable_and_migration_examples_use_serializer_attributes() -> None:
    text = REFERENCE.read_text(encoding="utf-8")
    # Match the heading, not its parenthetical: the section has been titled both
    # "## Variables" and "## Variables (`BPMN.Variables`)".
    _, marker, variables_section = text.partition("\n## Variables")
    assert marker, "structural-bpmn.md is missing its Variables section"
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
    # Every declaration carries an elementId naming the element that owns it. A
    # declaration without one is not a variable to the canvas, so each
    # `vars.<id>` reference to it fails on import.
    assert all(item.attrib.get("elementId") for item in declarations), [
        item.attrib for item in declarations
    ]

    # Pin the contract, not a version number: the attribute is `version` and its
    # value is an integer (the reader does Number.parseInt, so "11.5" -> 11).
    assert re.search(
        r'<uipath:migrationVersion version="\d+"\s*/>', variables_section
    ), variables_section
    assert "<uipath:migrationVersion value=" not in variables_section


def test_script_task_examples_dispatch_and_return_bare() -> None:
    """The half of the variable contract that fails silently.

    A mapping `uipath:type` other than `BPMN.Variables` overwrites the parser's
    `Scp.Script` extension type, so the runtime never dispatches the script:
    the element completes, the output mapping resolves against an empty result,
    and the target variable reads back `null`. Nothing surfaces it — which is
    how the wrong value shipped in this reference for seven weeks.

    Paired with the return shape, because the two only work together: at
    `scriptVersion` v2+ the runtime wraps the return under `response`
    (`ScriptActivities.cs`), so a script that wraps it again double-wraps.
    """
    text = REFERENCE.read_text(encoding="utf-8")
    fragments = re.findall(
        r"```xml\n(?P<xml>(?:(?!```).)*?<bpmn:scriptTask.*?)\n```", text, re.DOTALL
    )
    assert fragments, "structural-bpmn.md is missing its script-task example"

    for xml in fragments:
        wrapper = ET.fromstring(
            '<root xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"'
            ' xmlns:uipath="http://uipath.org/schema/bpmn"'
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            f"{xml}"
            "</root>"
        )
        for task in wrapper.iter("{%s}scriptTask" % NS["bpmn"]):
            types = [
                el.attrib.get("value")
                for mapping in task.iter("{%s}mapping" % NS["uipath"])
                for el in mapping.findall("uipath:type", NS)
            ]
            assert types, f"script task {task.attrib.get('id')} declares no uipath:type"
            assert all(value == "BPMN.Variables" for value in types), (
                f"script task {task.attrib.get('id')} maps through {types}; anything "
                "other than BPMN.Variables overwrites Scp.Script and the script "
                "never runs"
            )
            # The template omits scriptVersion, which parses as v1 and rejects a
            # bare return, so the example must carry it explicitly.
            versions = [
                el.attrib.get("value")
                for el in task.iter("{%s}scriptVersion" % NS["uipath"])
            ]
            assert versions and all(v and v != "v1" for v in versions), (
                f"script task {task.attrib.get('id')} needs an explicit "
                f"uipath:scriptVersion of v2 or later; got {versions}"
            )
            body = "".join(
                el.text or "" for el in task.iter("{%s}script" % NS["bpmn"])
            )
            assert not re.search(r"\breturn\s*\{\s*response\b", body), (
                f"script task {task.attrib.get('id')} wraps its return in "
                "`response`; the v2+ runtime already does, so this double-wraps "
                "to result.response.response"
            )
