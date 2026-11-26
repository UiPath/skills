#!/usr/bin/env python3
"""Offline tests for the agent_deploy_run graders, on synthetic payloads."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_agent_deploy_behavior as check_behavior  # noqa: E402
import check_agent_deploy_folder as check_deployed  # noqa: E402
from check_agent_deploy_behavior import CheckFailure  # noqa: E402

REASON = "Isabella is a common female given name."

AGENT_TASK = """
    <bpmn:serviceTask id="{id}">
      <bpmn:extensionElements>
        <uipath:activity version="v1">
          <uipath:type value="Orchestrator.StartAgentJob" version="v2"/>
          <uipath:output name="Process response" type="Orchestrator.RunJob" source="=result" var="{id}_processResponse"/>
          <uipath:output name="gender" type="string" source="=result.gender" var="{id}Gender" custom="true"/>
          <uipath:output name="reason" type="string" source="=result.reason" var="{id}Reason" custom="true"/>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>"""

PROCESS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                  xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="P">
    <bpmn:extensionElements>
      <uipath:variables version="v1">
        <uipath:inputOutput id="classifyGender" name="gender" type="string" elementId="classify"/>
        <uipath:inputOutput id="classifyReason" name="reason" type="string" elementId="classify"/>
        <uipath:inputOutput id="scriptGender" name="scriptGender" type="json" elementId="fake"/>
        <uipath:output id="sumVar" name="sum" type="number" elementId="done"/>
        <uipath:output id="genderVar" name="gender" type="string" elementId="done"/>
        <uipath:output id="reasonVar" name="reason" type="string" elementId="done"/>
      </uipath:variables>
    </bpmn:extensionElements>""" + AGENT_TASK.format(id="classify") + """
    <bpmn:serviceTask id="lookalike">
      <bpmn:documentation>Not an Orchestrator.StartAgentJob, despite this text.</bpmn:documentation>
      <bpmn:extensionElements>
        <uipath:activity><uipath:type value="Orchestrator.StartJob" version="v2"/></uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
    <bpmn:scriptTask id="fake" scriptFormat="JavaScript">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1"/>
          <uipath:output name="scriptGender" type="json" source="=result.response" var="scriptGender"/>
        </uipath:mapping>
      </bpmn:extensionElements>
      <bpmn:script>return "female";</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="done">
      <bpmn:extensionElements>
        <uipath:mapping version="v1">
          <uipath:type value="BPMN.Variables" version="v1"/>
          <uipath:output name="sum" type="number" source="=js:vars.sumValue" var="sumVar"/>
          <uipath:output name="gender" type="string" source="=js:vars.classifyGender" var="genderVar"/>
          <uipath:output name="reason" type="string" source="=js:vars.classifyReason" var="reasonVar"/>
        </uipath:mapping>
      </bpmn:extensionElements>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""

TWO_AGENT_CALLS_XML = PROCESS_XML.replace(
    '\n    <bpmn:serviceTask id="lookalike">', AGENT_TASK.format(id="classify2") + '\n    <bpmn:serviceTask id="lookalike">'
)


def process(xml=PROCESS_XML):
    return check_behavior.process_element(xml)


def variables(sum_value=9, gender="female", reason=REASON, agent_outputs=None, agent_runs=None):
    if agent_outputs is None:
        agent_outputs = {"gender": gender, "reason": reason}
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
        payload = variables(agent_outputs=f'{{"gender": "Female", "reason": "{REASON}"}}')
        check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_reason_matches_across_whitespace_and_case(self):
        payload = variables(agent_outputs={"gender": "female", "reason": f"  {REASON.upper()} "})
        check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_other_node_cannot_cover_for_agent(self):
        payload = variables(agent_outputs={})
        with self.assertRaisesRegex(CheckFailure, "result.gender"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_male_does_not_match_female(self):
        with self.assertRaisesRegex(CheckFailure, "result.gender"):
            check_behavior.assert_agent_provenance(process(), variables(), "male")

    def test_wrong_gender_with_both_labels_fails(self):
        payload = variables(
            gender="male",
            agent_outputs={"gender": "female", "reason": REASON, "labels": ["male", "female"]},
        )
        with self.assertRaisesRegex(CheckFailure, "result.gender"):
            check_behavior.assert_agent_provenance(process(), payload, "male")

    def test_unknown_classification_with_a_matching_hint_fails(self):
        payload = variables(agent_outputs={"gender": "unknown", "hint": "female", "note": REASON})
        with self.assertRaisesRegex(CheckFailure, "result.gender"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_label_and_reason_from_different_runs_fail(self):
        payload = variables(
            agent_runs=[
                {"gender": "female", "reason": "A different explanation."},
                {"gender": "unknown", "reason": REASON},
            ]
        )
        with self.assertRaisesRegex(CheckFailure, "ran 2 times"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_two_runs_of_the_agent_node_fail(self):
        payload = variables(
            agent_runs=[
                {"gender": "unknown", "reason": "Retrying."},
                {"gender": "female", "reason": REASON},
            ]
        )
        with self.assertRaisesRegex(CheckFailure, "ran 2 times"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_empty_classification_with_a_matching_hint_fails(self):
        payload = variables(agent_outputs={"gender": "", "hint": "female", "note": REASON})
        with self.assertRaisesRegex(CheckFailure, "result.gender"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_gender_published_from_a_script_fails(self):
        proc = process(PROCESS_XML.replace("=js:vars.classifyGender", "=js:vars.scriptGender"))
        with self.assertRaisesRegex(CheckFailure, "scriptGender"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_gender_with_a_literal_fallback_fails(self):
        proc = process(PROCESS_XML.replace("=js:vars.classifyGender", "=js:vars.classifyGender || 'female'"))
        with self.assertRaisesRegex(CheckFailure, "gender"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_agent_variable_also_written_elsewhere_fails(self):
        proc = process(PROCESS_XML.replace('var="scriptGender"', 'var="classifyGender"'))
        with self.assertRaisesRegex(CheckFailure, "classifyGender"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_gender_and_reason_from_different_agent_calls_fail(self):
        proc = process(TWO_AGENT_CALLS_XML.replace("=js:vars.classifyReason", "=js:vars.classify2Reason"))
        with self.assertRaisesRegex(CheckFailure, "classify2"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_fields_nested_below_the_mapped_path_fail(self):
        payload = variables(agent_outputs={"response": {"gender": "female", "reason": REASON}})
        with self.assertRaisesRegex(CheckFailure, "result.gender"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_nested_mapping_reads_the_nested_fields(self):
        proc = process(PROCESS_XML.replace("=result.gender", "=result.response.gender").replace(
            "=result.reason", "=result?.response?.reason"
        ))
        payload = variables(agent_outputs={"response": {"gender": "female", "reason": REASON}})
        check_behavior.assert_agent_provenance(proc, payload, "female")

    def test_gender_mapped_from_the_whole_response_passes(self):
        proc = process(PROCESS_XML.replace("=js:vars.classifyGender", "=js:vars.classify_processResponse.gender"))
        check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_constant_process_reason_fails(self):
        proc = process(PROCESS_XML.replace("=js:vars.classifyReason", "=js:'Classified by the agent.'"))
        with self.assertRaisesRegex(CheckFailure, "`reason` is published from"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_reason_published_from_the_gender_field_fails(self):
        proc = process(PROCESS_XML.replace("=js:vars.classifyReason", "=js:vars.classifyGender"))
        with self.assertRaisesRegex(CheckFailure, "both published from result.gender"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_reason_that_is_only_the_label_fails(self):
        payload = variables(agent_outputs={"gender": "female", "reason": "Female"})
        with self.assertRaisesRegex(CheckFailure, "result.reason"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_empty_agent_reason_fails(self):
        payload = variables(agent_outputs={"gender": "female", "reason": "  "})
        with self.assertRaisesRegex(CheckFailure, "result.reason"):
            check_behavior.assert_agent_provenance(process(), payload, "female")

    def test_no_agent_job_fails(self):
        proc = process(PROCESS_XML.replace('value="Orchestrator.StartAgentJob"', 'value="Orchestrator.StartJob"'))
        with self.assertRaisesRegex(CheckFailure, "never called"):
            check_behavior.assert_agent_provenance(proc, variables(), "female")

    def test_type_named_only_in_text_is_not_an_agent_job(self):
        self.assertEqual(check_behavior.agent_job_ids(process()), ["classify"])


FOLDER_AGENT_JOB = "c0ffee00-0000-4000-8000-000000000001"
OTHER_JOB = "c0ffee00-0000-4000-8000-000000000002"


def job(key=FOLDER_AGENT_JOB, release="bbbb", state="Successful"):
    return {"Key": key, "ReleaseName": "A", "Release": {"Key": release}, "State": state}


class AgentJobTests(unittest.TestCase):
    ROWS = [
        {"Name": "P", "ProcessType": "ProcessOrchestration", "Key": "AAAA"},
        {"Name": "A", "ProcessType": "Agent", "Key": "BBBB"},
    ]
    STARTED = {"c0ffee00-0000-4000-8000-000000000001"}
    EXECUTIONS = [
        {"ElementId": "start", "JobKey": None, "ElementRuns": [{"JobKey": None}]},
        {"ElementId": "classify", "JobKey": None, "ElementRuns": [{"JobKey": "C0FFEE00-0000-4000-8000-000000000001"}]},
        {"ElementId": "lookalike", "JobKey": "dddd", "ElementRuns": [{"JobKey": "dddd"}]},
    ]

    def started(self, jobs):
        return check_behavior.started_agent_jobs(jobs, {"bbbb"}, self.STARTED)

    def test_agent_release_keys_are_case_folded(self):
        self.assertEqual(check_behavior.agent_release_keys(self.ROWS), {"bbbb"})

    def test_job_keys_come_only_from_agent_job_nodes(self):
        self.assertEqual(check_behavior.started_job_keys(self.EXECUTIONS, ["classify"]), self.STARTED)

    def test_the_started_agent_job_counts(self):
        self.assertEqual(len(self.started([job(release="aaaa"), job(release="BBBB")])), 1)

    def test_faulted_agent_job_does_not_count(self):
        self.assertEqual(self.started([job(state="Faulted")]), [])

    def test_concurrent_agent_job_the_node_did_not_start_does_not_count(self):
        self.assertEqual(self.started([job(key="c0ffee00-0000-4000-8000-000000000002")]), [])

    def test_started_job_of_another_release_does_not_count(self):
        self.assertEqual(self.started([job(release="eeee")]), [])

    def job_ran(self, xml, executions, jobs):
        def fake_cli(arguments, *, timeout):
            rows = self.ROWS if arguments[2] == "processes" else jobs
            return SimpleNamespace(returncode=0, stdout=json.dumps({"Result": "Success", "Data": rows}), stderr="")

        with mock.patch.object(check_behavior, "fetch_element_executions", return_value=executions), mock.patch.object(
            check_behavior, "run_cli", fake_cli
        ):
            check_behavior.assert_agent_job_ran("Shared/run", "2026-11-24T00:00:00Z", process(xml), "inst", "fk")

    def test_the_mapped_node_job_passes(self):
        executions = [{"ElementId": "classify", "ElementRuns": [{"JobKey": FOLDER_AGENT_JOB}]}]
        self.job_ran(PROCESS_XML, executions, [job(key=FOLDER_AGENT_JOB, release="BBBB")])

    def test_a_second_agent_call_cannot_supply_the_job(self):
        executions = [
            {"ElementId": "classify", "ElementRuns": [{"JobKey": OTHER_JOB}]},
            {"ElementId": "classify2", "ElementRuns": [{"JobKey": FOLDER_AGENT_JOB}]},
        ]
        jobs = [job(key=OTHER_JOB, release="eeee"), job(key=FOLDER_AGENT_JOB, release="BBBB")]
        with self.assertRaisesRegex(CheckFailure, "classify"):
            self.job_ran(TWO_AGENT_CALLS_XML, executions, jobs)

    def test_two_jobs_from_the_mapped_node_fail(self):
        executions = [{"ElementId": "classify", "ElementRuns": [{"JobKey": OTHER_JOB}, {"JobKey": FOLDER_AGENT_JOB}]}]
        jobs = [job(key=OTHER_JOB, release="eeee"), job(key=FOLDER_AGENT_JOB, release="BBBB")]
        with self.assertRaisesRegex(CheckFailure, "2 jobs"):
            self.job_ran(PROCESS_XML, executions, jobs)


class DeployedTests(unittest.TestCase):
    def test_both_types_present(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}, {"Name": "A", "ProcessType": "Agent"}]
        self.assertEqual(check_deployed.missing_types(rows), [])

    def test_agent_missing(self):
        rows = [{"Name": "P", "ProcessType": "ProcessOrchestration"}]
        self.assertEqual(check_deployed.missing_types(rows), ["Agent"])


if __name__ == "__main__":
    unittest.main()
