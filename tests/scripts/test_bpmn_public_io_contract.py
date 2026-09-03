"""Guard the minimal public process I/O example in the BPMN skill."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from bpmn_doc_example import NS, minimal_example


def _variables(process: ET.Element) -> dict[str, ET.Element]:
    items = process.findall(
        "bpmn:extensionElements/uipath:variables/*",
        NS,
    )
    return {item.attrib["id"]: item for item in items}


def _mapping_outputs(element: ET.Element) -> list[ET.Element]:
    mapping = element.find("bpmn:extensionElements/uipath:mapping", NS)
    assert mapping is not None
    mapping_type = mapping.find("uipath:type", NS)
    assert mapping_type is not None
    assert mapping_type.attrib["value"] == "BPMN.Variables"
    return mapping.findall("uipath:output", NS)


def test_minimal_example_bridges_public_input_to_mutable_state() -> None:
    root = minimal_example()
    process = root.find("bpmn:process", NS)
    assert process is not None

    starts = process.findall("bpmn:startEvent", NS)
    assert len(starts) == 1
    start = starts[0]

    variables = _variables(process)
    public_inputs = [
        item for item in variables.values() if item.tag.endswith("}input")
    ]
    assert public_inputs
    for public_input in public_inputs:
        assert public_input.attrib["elementId"] == start.attrib["id"]
        matches = [
            output
            for output in _mapping_outputs(start)
            if output.attrib.get("source") == f"=vars.{public_input.attrib['id']}"
        ]
        assert len(matches) == 1
        mutable = variables[matches[0].attrib["var"]]
        assert mutable.tag.endswith("}inputOutput")
        assert mutable.attrib["type"] == public_input.attrib["type"]
        assert "elementId" not in mutable.attrib


def test_minimal_example_bridges_mutable_state_to_public_output() -> None:
    root = minimal_example()
    process = root.find("bpmn:process", NS)
    assert process is not None

    ends = process.findall("bpmn:endEvent", NS)
    assert len(ends) == 1
    end = ends[0]
    variables = _variables(process)
    public_outputs = [
        item for item in variables.values() if item.tag.endswith("}output")
    ]
    assert public_outputs
    for public_output in public_outputs:
        assert public_output.attrib["elementId"] == end.attrib["id"]
        matches = [
            output
            for output in _mapping_outputs(end)
            if output.attrib.get("var") == public_output.attrib["id"]
        ]
        assert len(matches) == 1
        source = matches[0].attrib["source"]
        assert source.startswith("=vars.")
        mutable = variables[source.removeprefix("=vars.")]
        assert mutable.tag.endswith("}inputOutput")
        assert mutable.attrib["type"] == public_output.attrib["type"]
        assert "elementId" not in mutable.attrib
