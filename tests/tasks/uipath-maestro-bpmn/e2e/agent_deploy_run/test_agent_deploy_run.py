#!/usr/bin/env python3
"""Offline tests for the agent_deploy_run graders, on synthetic payloads."""

from __future__ import annotations

import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_agent_deploy_behavior as check_behavior  # noqa: E402
import check_agent_deploy_folder as check_deployed  # noqa: E402
from check_agent_deploy_behavior import CheckFailure  # noqa: E402

PROCESS_XML = """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="P">
    <bpmn:extensionElements>
      <uipath:variables>
        <uipath:output id="sumVar" name="sum" type="number" elementId="done"/>
        <uipath:output id="genderVar" name="gender" type="string" elementId="done"/>
        <uipath:output id="reasonVar" name="reason" type="string" elementId="done"/>
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:serviceTask id="classify">
      <bpmn:extensionElements>
        <uipath:activity><uipath:type value="Orchestrator.StartAgentJob" version="v2"/></uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
    <bpmn:scriptTask id="fake"/>
  </bpmn:process>
</bpmn:definitions>
"""


def process():
    return ET.fromstring(PROCESS_XML).find("{http://www.omg.org/spec/BPMN/20100524/MODEL}process")


def variables(sum_value=9, gender="female", reason="Common female name.", agent_outputs=None):
    if agent_outputs is None:
        agent_outputs = {"response": {"gender": gender, "reason": reason}}
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Globals": {"sumVar": sum_value, "genderVar": gender, "reasonVar": reason},
                "GlobalDefinitions": {},
                "Elements": [
                    {"ElementId": "classify", "Outputs": agent_outputs},
                    {"ElementId": "fake", "Outputs": {"scriptResponse": "female"}},
                ],
            }
        ]
    }


class OutputTests(unittest.TestCase):
    def test_correct_outputs_pass(self):
        check_behavior.assert_outputs(process(), variables(), 4, 5, "female")

    def test_sum_as_numeric_string_passes(self):
        check_behavior.assert_outputs(process(), variables(sum_value="9"), 4, 5, "female")

    def test_wrong_sum_fails(self):
        with self.assertRaisesRegex(CheckFailure, "sum"):
            check_behavior.assert_outputs(process(), variables(sum_value=45), 4, 5, "female")

    def test_concatenated_sum_fails(self):
        with self.assertRaisesRegex(CheckFailure, "sum"):
            check_behavior.assert_outputs(process(), variables(sum_value="45"), 4, 5, "female")

    def test_null_gender_fails(self):
        with self.assertRaisesRegex(CheckFailure, "gender"):
            check_behavior.assert_outputs(process(), variables(gender=None), 4, 5, "female")

    def test_gender_is_case_insensitive(self):
        check_behavior.assert_outputs(process(), variables(gender="Female"), 4, 5, "female")

    def test_empty_reason_fails(self):
        with self.assertRaisesRegex(CheckFailure, "reason"):
            check_behavior.assert_outputs(process(), variables(reason="  "), 4, 5, "female")


class ProvenanceTests(unittest.TestCase):
    def test_agent_node_output_passes(self):
        check_behavior.assert_agent_provenance(process(), variables(), "female")

    def test_other_node_cannot_cover_for_agent(self):
        payload = variables(agent_outputs={"response": {}})
        with self.assertRaisesRegex(CheckFailure, "Outputs"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_male_does_not_match_female(self):
        with self.assertRaisesRegex(CheckFailure, "Outputs"):
            check_behavior.assert_agent_provenance(process(), variables(), "male")

    def test_no_agent_job_fails(self):
        no_agent = ET.fromstring(PROCESS_XML.replace("Orchestrator.StartAgentJob", "Orchestrator.StartJob"))
        proc = no_agent.find("{http://www.omg.org/spec/BPMN/20100524/MODEL}process")
        with self.assertRaisesRegex(CheckFailure, "never called"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")


class DeployedTests(unittest.TestCase):
    def test_both_types_present(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}, {"Name": "A", "ProcessType": "Agent"}]
        self.assertEqual(check_deployed.missing_types(rows), [])

    def test_agent_missing(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}]
        self.assertEqual(check_deployed.missing_types(rows), ["Agent"])


if __name__ == "__main__":
    unittest.main()
