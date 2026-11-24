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


def variables(sum_value=9, gender="female", reason=REASON, agent_outputs=None, agent_runs=None):
    if agent_outputs is None:
        agent_outputs = {"response": {"gender": gender, "reason": reason}}
    if agent_runs is None:
        agent_runs = [agent_outputs]
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Globals": {"sumVar": sum_value, "genderVar": gender, "reasonVar": reason},
                "GlobalDefinitions": {},
                "Elements": [
                    *({"ElementId": "classify", "Outputs": outputs} for outputs in agent_runs),
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
        with self.assertRaisesRegex(CheckFailure, "exactly the label"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_male_does_not_match_female(self):
        with self.assertRaisesRegex(CheckFailure, "exactly the label"):
            check_behavior.assert_agent_provenance(process(), variables(), "male")

    def test_wrong_gender_with_both_labels_fails(self):
        payload = variables(
            gender="male",
            agent_outputs={"response": {"gender": "female", "reason": REASON, "labels": ["male", "female"]}},
        )
        with self.assertRaisesRegex(CheckFailure, "exactly the label"):
            check_behavior.assert_agent_provenance(process(), payload, "male")

    def test_unknown_classification_with_a_matching_hint_fails(self):
        payload = variables(agent_outputs={"response": {"gender": "unknown", "hint": "female", "note": REASON}})
        with self.assertRaisesRegex(CheckFailure, r"labels per run: \[\['female', 'unknown'\]\]"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_label_and_reason_from_different_runs_fail(self):
        payload = variables(
            agent_runs=[
                {"response": {"gender": "female", "reason": "A different explanation."}},
                {"response": {"gender": "unknown", "reason": REASON}},
            ]
        )
        with self.assertRaisesRegex(CheckFailure, "exactly the label"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_one_matching_run_among_several_passes(self):
        payload = variables(
            agent_runs=[
                {"response": {"gender": "unknown", "reason": "Retrying."}},
                {"response": {"gender": "female", "reason": REASON}},
            ]
        )
        check_behavior.assert_agent_provenance(process(), payload, "female")

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


def job(release="bbbb", state="Successful", trace="0a1b2c3d4e5f60718293a4b5c6d7e8f9"):
    return {"ReleaseName": "A", "Release": {"Key": release}, "State": state, "TraceId": trace}


class AgentJobTests(unittest.TestCase):
    ROWS = [
        {"Name": "P", "ProcessType": "ProcessOrchestration", "Key": "AAAA"},
        {"Name": "A", "ProcessType": "Agent", "Key": "BBBB"},
    ]
    TRACE = "0A1B2C3D-4E5F-6071-8293-A4B5C6D7E8F9"

    def traced(self, jobs):
        return check_behavior.traced_agent_jobs(jobs, {"bbbb"}, self.TRACE)

    def test_agent_release_keys_are_case_folded(self):
        self.assertEqual(check_behavior.agent_release_keys(self.ROWS), {"bbbb"})

    def test_agent_job_on_the_run_trace_counts(self):
        self.assertEqual(len(self.traced([job(release="aaaa"), job(release="BBBB")])), 1)

    def test_faulted_agent_job_does_not_count(self):
        self.assertEqual(self.traced([job(state="Faulted")]), [])

    def test_concurrent_agent_job_on_another_trace_does_not_count(self):
        self.assertEqual(self.traced([job(trace="ffffffffffffffffffffffffffffffff")]), [])

    def test_job_without_a_release_does_not_count(self):
        self.assertEqual(self.traced([{"State": "Successful", "TraceId": self.TRACE}]), [])

    def test_run_without_a_trace_fails_before_listing(self):
        with self.assertRaisesRegex(CheckFailure, "TraceId"):
            check_behavior.assert_agent_job_ran("Shared/x", {"CreationTime": "2026-01-01T00:00:00Z", "TraceId": None})


class DeployedTests(unittest.TestCase):
    def test_both_types_present(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}, {"Name": "A", "ProcessType": "Agent"}]
        self.assertEqual(check_deployed.missing_types(rows), [])

    def test_agent_missing(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}]
        self.assertEqual(check_deployed.missing_types(rows), ["Agent"])


if __name__ == "__main__":
    unittest.main()
