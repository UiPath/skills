"""Guard the bundled current-v3 ScriptTask registry contract.

Run with:
    pytest tests/scripts/test_bpmn_script_task_contract.py
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = (
    ROOT
    / "skills"
    / "uipath-maestro-bpmn"
    / "validator"
    / "bpmn-spec.json"
)
NS = {
    "bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL",
    "uipath": "http://uipath.org/schema/bpmn",
}


def _script_task_entry() -> dict[str, object]:
    registry = json.loads(SPEC.read_text(encoding="utf-8"))
    return registry["extensionTypes"]["BPMN.ScriptTask"]


def _template_root() -> ET.Element:
    template = _script_task_entry()["xmlTemplate"]
    wrapper = (
        '<root xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
        'xmlns:uipath="http://uipath.org/schema/bpmn">'
        f"{template}"
        "</root>"
    )
    return ET.fromstring(wrapper)[0]


def test_script_task_registry_entry_uses_current_v3_shape() -> None:
    entry = _script_task_entry()
    assert entry["bpmnElement"] == "bpmn:ScriptTask"
    assert entry["extensionTag"] == "uipath:mapping"
    assert entry["inputPattern"] == "scriptArgs"

    task = _template_root()
    assert task.tag == f"{{{NS['bpmn']}}}scriptTask"
    assert task.attrib["scriptFormat"] == "JavaScript"

    mapping = task.find("bpmn:extensionElements/uipath:mapping", NS)
    assert mapping is not None
    mapping_type = mapping.find("uipath:type", NS)
    assert mapping_type is not None
    assert mapping_type.attrib == {"value": "BPMN.Variables", "version": "v1"}

    input_schema = mapping.find("uipath:context/uipath:inputSchema", NS)
    assert input_schema is not None
    schema = json.loads(input_schema.text or "")
    assert schema["properties"] == {
        "vars": {"type": "object"},
        "metadata": {"type": "object"},
    }

    args = mapping.find("uipath:input", NS)
    assert args is not None
    assert args.attrib == {
        "name": "args",
        "type": "json",
        "target": "bodyField",
    }
    assert json.loads(args.text or "") == {
        "vars": "=vars",
        "metadata": "=metadata",
    }

    outputs = {
        output.attrib["name"]: output.attrib
        for output in mapping.findall("uipath:output", NS)
    }
    assert outputs == {
        "scriptResponse": {
            "name": "scriptResponse",
            "type": "jsonSchema",
            "source": "=result.response",
            "var": "{scriptResponseVarId}",
        },
        "Error": {
            "name": "Error",
            "type": "jsonSchema",
            "source": "=Error",
            "var": "{errorVarId}",
        },
    }

    version = task.find("bpmn:extensionElements/uipath:scriptVersion", NS)
    assert version is not None
    assert version.attrib["value"] == "v3"
    script = task.find("bpmn:script", NS)
    assert script is not None
    assert (script.text or "").strip() == "return null;"
