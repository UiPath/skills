"""Unit tests for the offline helpers in bpmn_live."""

from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET

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
