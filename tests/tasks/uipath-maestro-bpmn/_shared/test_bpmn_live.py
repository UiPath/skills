"""Unit tests for the offline helpers in bpmn_live."""

from __future__ import annotations

import ast
import glob
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpmn_live  # noqa: E402
import pytest  # noqa: E402

PROCESS = f"""
<bpmn:process xmlns:bpmn="{bpmn_live.BPMN_NS}" xmlns:uipath="{bpmn_live.UIPATH_NS}" id="Process_1">
  <bpmn:extensionElements>
    <uipath:variables version="v1">
      <uipath:input id="input_Var_Invoice" name="invoiceNumber" type="string" elementId="Start_1" />
      <uipath:inputOutput id="Var_Invoice" name="invoiceNumber" type="string" elementId="Process_1" />
      <uipath:output id="output_Var_Total" name="total" type="number" elementId="End_1" />
    </uipath:variables>
  </bpmn:extensionElements>
  <bpmn:startEvent id="Start_1">
    <bpmn:extensionElements>
      <uipath:mapping version="v1">
        <uipath:output name="invoiceNumber" var="Var_Invoice" source="=vars.input_Var_Invoice" />
      </uipath:mapping>
    </bpmn:extensionElements>
  </bpmn:startEvent>
  <bpmn:sendTask id="Task_1">
    <bpmn:extensionElements>
      <uipath:activity version="v1">
        <uipath:input name="body" type="json" target="body"><![CDATA[{{}}]]></uipath:input>
      </uipath:activity>
    </bpmn:extensionElements>
  </bpmn:sendTask>
</bpmn:process>
"""

VARIABLES = {
    "Variables": [
        {
            "ParentElementId": None,
            "Globals": {
                "input_Var_Invoice": "MCS-1",
                "Var_Invoice": "MCS-1",
                "output_Var_Total": 8,
            },
            "Elements": [
                {"ElementId": "Start_1", "Outputs": {"invoiceNumber": "MCS-1"}},
                {"ElementId": "Task_1", "Outputs": {"response": {"rows": [{"id": "r1"}]}}},
            ],
        }
    ]
}


def test_input_echo_ids_covers_the_input_its_copy_and_the_start() -> None:
    ids = bpmn_live.input_echo_ids(ET.fromstring(PROCESS))
    assert {"input_Var_Invoice", "invoiceNumber", "Var_Invoice", "Start_1"} <= ids
    assert "output_Var_Total" not in ids
    assert "Task_1" not in ids


def test_output_leaves_skips_input_echoes() -> None:
    skip = bpmn_live.input_echo_ids(ET.fromstring(PROCESS))
    assert bpmn_live.output_leaves(VARIABLES, skip) == [8, "r1"]
    assert "MCS-1" in bpmn_live.output_leaves(VARIABLES)


def test_input_echo_ids_follows_copies_through_any_element() -> None:
    process = PROCESS.replace(
        "<bpmn:sendTask id=\"Task_1\">",
        "<bpmn:task id=\"Task_Copy\"><bpmn:extensionElements><uipath:mapping version=\"v1\">"
        "<uipath:output name=\"work\" var=\"Var_Work\" source=\"=vars.Var_Invoice\" />"
        "</uipath:mapping></bpmn:extensionElements></bpmn:task>"
        "<bpmn:sendTask id=\"Task_1\">",
    )
    ids = bpmn_live.input_echo_ids(ET.fromstring(process))
    assert {"Var_Work", "work"} <= ids
    assert "Task_Copy" not in ids


def _evidence(incidents) -> bpmn_live.DebugEvidence:
    return bpmn_live.DebugEvidence(VARIABLES, "", incidents, incidents)


def test_require_clean_run_accepts_a_completed_run() -> None:
    assert bpmn_live.require_clean_run({"FinalStatus": "Completed"}, _evidence([])) == "Completed"


@pytest.mark.parametrize(
    "debug_data, incidents, message",
    [
        ({"FinalStatus": "Faulted"}, [], "final status was 'Faulted'"),
        ({"FinalStatus": "Completed"}, [{"Code": 102010}], "unexpected incidents"),
        ({"FinalStatus": "Completed"}, None, "unknown shape"),
    ],
)
def test_require_clean_run_rejects(debug_data, incidents, message) -> None:
    with pytest.raises(bpmn_live.CheckFailure, match=message):
        bpmn_live.require_clean_run(debug_data, _evidence(incidents))


CONNECTOR_PROCESS = f"""
<bpmn:process xmlns:bpmn="{bpmn_live.BPMN_NS}" xmlns:uipath="{bpmn_live.UIPATH_NS}" id="Process_1">
  <bpmn:sendTask id="Task_Send">
    <bpmn:extensionElements>
      <uipath:activity version="v1">
        <uipath:context>
          <uipath:input name="connectorKey" value="uipath-salesforce-slack" />
          <uipath:input name="path" value="/send_message_to_channel_v2" />
          <uipath:input name="objectName" value="send_message_to_channel_v2" />
        </uipath:context>
      </uipath:activity>
    </bpmn:extensionElements>
  </bpmn:sendTask>
</bpmn:process>
"""


def test_index_runtime_connectors_keys_carry_key_path_and_object() -> None:
    connectors = bpmn_live.index_runtime_connectors(ET.fromstring(CONNECTOR_PROCESS))
    assert connectors == {
        ("uipath-salesforce-slack", "/send_message_to_channel_v2", "send_message_to_channel_v2"): ("Task_Send",)
    }


def _connector_unpacks(tree: ast.AST) -> list[tuple[int, int]]:
    """(line, arity) of every `for (...), ids in <x>.items()` over a name
    bound to index_runtime_connectors(...)."""
    bound = {
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Call)
        and getattr(node.value.func, "id", getattr(node.value.func, "attr", None)) == "index_runtime_connectors"
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.For, ast.comprehension)):
            continue
        source = node.iter
        if not (
            isinstance(source, ast.Call)
            and isinstance(source.func, ast.Attribute)
            and source.func.attr == "items"
            and isinstance(source.func.value, ast.Name)
            and source.func.value.id in bound
        ):
            continue
        target = node.target
        if isinstance(target, ast.Tuple) and isinstance(target.elts[0], ast.Tuple):
            found.append((target.lineno, len(target.elts[0].elts)))
    return found


@pytest.mark.parametrize(
    "script",
    sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_*.py"))),
    ids=os.path.basename,
)
def test_graders_unpack_the_full_connector_key(script: str) -> None:
    tree = ast.parse(Path(script).read_text(encoding="utf-8"))
    bad = [line for line, arity in _connector_unpacks(tree) if arity != 3]
    assert not bad, f"{os.path.basename(script)} unpacks index_runtime_connectors keys at lines {bad}"
