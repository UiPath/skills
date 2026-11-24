#!/usr/bin/env python3
"""Offline tests for the agent_deploy_run graders, on synthetic payloads."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_agent_deploy_behavior as check_behavior  # noqa: E402
import check_agent_deploy_folder as check_deployed  # noqa: E402
from check_agent_deploy_behavior import CheckFailure  # noqa: E402

REASON = "Isabella is a common female given name."

PROCESS_XML = """<?xml version="1.0" encoding="UTF-8"?>
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
    <bpmn:serviceTask id="lookalike">
      <bpmn:documentation>Not an Orchestrator.StartAgentJob, despite this text.</bpmn:documentation>
      <bpmn:extensionElements>
        <uipath:activity><uipath:type value="Orchestrator.StartJob" version="v2"/></uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
    <bpmn:scriptTask id="fake"/>
  </bpmn:process>
</bpmn:definitions>
"""


def process(xml=PROCESS_XML):
    return check_behavior.process_element(xml)


def variables(sum_value=9, gender="female", reason=REASON, agent_outputs=None):
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
                    {"ElementId": "lookalike", "Outputs": {"response": {"gender": gender, "reason": reason}}},
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

    def test_agent_output_as_json_string_passes(self):
        payload = variables(agent_outputs={"response": f'{{"gender": "Female", "reason": "{REASON}"}}'})
        check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_reason_matches_across_whitespace_and_case(self):
        payload = variables(agent_outputs={"response": {"gender": "female", "reason": f"  {REASON.upper()} "}})
        check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_other_node_cannot_cover_for_agent(self):
        payload = variables(agent_outputs={"response": {}})
        with self.assertRaisesRegex(CheckFailure, "Outputs"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_male_does_not_match_female(self):
        with self.assertRaisesRegex(CheckFailure, "Outputs"):
            check_behavior.assert_agent_provenance(process(), variables(), "male")

    def test_wrong_gender_with_both_labels_fails(self):
        payload = variables(
            gender="male",
            agent_outputs={"response": {"gender": "female", "reason": REASON, "labels": ["male", "female"]}},
        )
        with self.assertRaisesRegex(CheckFailure, "both"):
            check_behavior.assert_agent_provenance(process(), payload, "male")

    def test_constant_process_reason_fails(self):
        payload = variables(
            reason="Classified by the agent.",
            agent_outputs={"response": {"gender": "female", "reason": REASON}},
        )
        with self.assertRaisesRegex(CheckFailure, "reason"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_reason_that_is_only_the_label_fails(self):
        payload = variables(reason="female", agent_outputs={"response": {"gender": "female", "reason": REASON}})
        with self.assertRaisesRegex(CheckFailure, "reason"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_no_agent_job_fails(self):
        proc = process(PROCESS_XML.replace('value="Orchestrator.StartAgentJob"', 'value="Orchestrator.StartJob"'))
        with self.assertRaisesRegex(CheckFailure, "never called"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_type_named_only_in_text_is_not_an_agent_job(self):
        self.assertEqual(check_behavior.agent_job_ids(process()), ["classify"])


class AgentJobTests(unittest.TestCase):
    ROWS = [
        {"Name": "P", "ProcessType": "ProcessOrchestration", "Key": "AAAA"},
        {"Name": "A", "ProcessType": "Agent", "Key": "BBBB"},
    ]

    def test_agent_release_keys_are_case_folded(self):
        self.assertEqual(check_behavior.agent_release_keys(self.ROWS), {"bbbb"})

    def test_successful_agent_job_counts(self):
        jobs = [
            {"ReleaseKey": "aaaa", "State": "Successful"},
            {"ReleaseKey": "bbbb", "State": "Successful"},
        ]
        self.assertEqual(len(check_behavior.successful_agent_jobs(jobs, {"bbbb"})), 1)

    def test_faulted_or_other_jobs_do_not_count(self):
        jobs = [
            {"ReleaseKey": "bbbb", "State": "Faulted"},
            {"ReleaseKey": "aaaa", "State": "Successful"},
        ]
        self.assertEqual(check_behavior.successful_agent_jobs(jobs, {"bbbb"}), [])


class DeployedTests(unittest.TestCase):
    def test_both_types_present(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}, {"Name": "A", "ProcessType": "Agent"}]
        self.assertEqual(check_deployed.missing_types(rows), [])

    def test_agent_missing(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}]
        self.assertEqual(check_deployed.missing_types(rows), ["Agent"])


if __name__ == "__main__":
    unittest.main()
