#!/usr/bin/env python3
"""Unit tests for the escalation e2e graders. Stdlib + pytest only (CI
installs pytest and nothing else — see .github/workflows/test-helpers.yml).

Proportionate by design: the live CLI surface is exercised by the eval run
itself; these tests pin the pure logic — contract resolution, runtime
assertions, journal roundtrip, and the seed/prompt lockstep.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checker = _load("escalation_behavior", "check_customer_escalation_behavior.py")
packager = _load("escalation_package", "check_customer_escalation_package.py")
escalation_is = sys.modules["escalation_is"]

SAMPLE_BPMN = """<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:uipath="http://uipath.org/schema/bpmn">
  <bpmn:process id="Process_1">
    <bpmn:extensionElements>
      <uipath:variables>
        <uipath:input name="customerTier" id="var_tier" type="string"/>
        <uipath:output name="severity" id="var_severity" type="string"/>
        <uipath:output name="caseKey" id="var_caseKey" type="string"/>
        <uipath:output name="jiraIssueKey" id="var_jiraKey" type="string"/>
      </uipath:variables>
    </bpmn:extensionElements>
    <bpmn:serviceTask id="JiraCreate1">
      <bpmn:extensionElements>
        <uipath:activity>
          <uipath:context>
            <uipath:input name="connectorKey" value="uipath-atlassian-jira"/>
            <uipath:input name="path" value="/curated_create_issue"/>
          </uipath:context>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
    <bpmn:serviceTask id="SlackSend1">
      <bpmn:extensionElements>
        <uipath:activity>
          <uipath:context>
            <uipath:input name="connectorKey" value="uipath-salesforce-slack"/>
            <uipath:input name="path" value="/send_message_to_channel_v2"/>
          </uipath:context>
        </uipath:activity>
      </bpmn:extensionElements>
    </bpmn:serviceTask>
  </bpmn:process>
</bpmn:definitions>
"""

SEED = {
    "correlationId": "ESC-BPMN-test",
    "inputs": {
        "customerTier": "Enterprise",
        "serviceState": "Unavailable",
        "workaroundAvailable": False,
        "correlationId": "ESC-BPMN-test",
        "jiraProjectKey": "CE",
        "jiraIssueTypeId": "11457",
        "slackChannelId": "C01H4SPS77W",
    },
    "expected": {"severity": "Sev1", "caseKey": "ESC-BPMN-test"},
}

CONTRACT = checker.Contract(
    output_ids={
        "severity": "var_severity",
        "caseKey": "var_caseKey",
        "jiraIssueKey": "var_jiraKey",
    },
    jira_create_ids=("JiraCreate1",),
    slack_send_ids=("SlackSend1",),
)


def good_debug_data() -> dict:
    return {
        "FinalStatus": "Completed",
        "InstanceId": "inst-1",
        "ElementExecutions": [
            {"ElementId": "Script1"},
            {"ElementId": "JiraCreate1"},
            {"ElementId": "SlackSend1"},
        ],
    }


def good_variables_data() -> dict:
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Globals": {
                    "var_severity": "Sev1",
                    "var_caseKey": "ESC-BPMN-test",
                    "var_jiraKey": "CE-101",
                },
                "Elements": [
                    {
                        "ElementId": "JiraCreate1",
                        "Outputs": {
                            "response": {"key": "CE-101", "id": "10001"}
                        },
                    },
                    {
                        "ElementId": "SlackSend1",
                        "Outputs": {
                            "response": {
                                "ts": "111.222",
                                "channel": "C01H4SPS77W",
                                "message": {
                                    "text": "[Sev1] ESC-BPMN-test escalation",
                                    "ts": "111.222",
                                },
                            }
                        },
                    },
                ],
            }
        ]
    }


class ContractResolutionTests(unittest.TestCase):
    def _resolve(self, xml: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bpmn"
            path.write_text(xml, encoding="utf-8")
            return checker.resolve_contract(path)

    def test_resolves_outputs_and_connector_elements(self):
        contract = self._resolve(SAMPLE_BPMN)
        self.assertEqual(
            contract.output_ids,
            {
                "severity": "var_severity",
                "caseKey": "var_caseKey",
                "jiraIssueKey": "var_jiraKey",
            },
        )
        self.assertEqual(contract.jira_create_ids, ("JiraCreate1",))
        self.assertEqual(contract.slack_send_ids, ("SlackSend1",))

    def test_missing_output_fails(self):
        broken = SAMPLE_BPMN.replace('name="jiraIssueKey"', 'name="somethingElse"')
        with self.assertRaisesRegex(checker.CheckFailure, "jiraIssueKey"):
            self._resolve(broken)

    def test_duplicate_output_fails(self):
        duplicated = SAMPLE_BPMN.replace(
            '<uipath:output name="caseKey" id="var_caseKey" type="string"/>',
            '<uipath:output name="caseKey" id="var_caseKey" type="string"/>'
            '<uipath:output name="caseKey" id="var_caseKey2" type="string"/>',
        )
        with self.assertRaisesRegex(checker.CheckFailure, "more than once"):
            self._resolve(duplicated)

    def test_missing_connector_fails(self):
        no_slack = SAMPLE_BPMN.replace("uipath-salesforce-slack", "uipath-else")
        with self.assertRaisesRegex(
            checker.CheckFailure, "send_message_to_channel"
        ):
            self._resolve(no_slack)


class OutcomeAssertionTests(unittest.TestCase):
    def assert_fails(self, debug, variables, incidents, pattern):
        with self.assertRaisesRegex(checker.CheckFailure, pattern):
            checker.assert_outcome(CONTRACT, SEED, debug, variables, incidents)

    def test_happy_path_returns_created_key(self):
        key = checker.assert_outcome(
            CONTRACT, SEED, good_debug_data(), good_variables_data(), []
        )
        self.assertEqual(key, "CE-101")

    def test_incident_fails(self):
        self.assert_fails(
            good_debug_data(),
            good_variables_data(),
            [{"Message": "boom"}],
            "incidents",
        )

    def test_wrong_severity_fails(self):
        variables = good_variables_data()
        variables["Variables"][0]["Globals"]["var_severity"] = "Sev2"
        self.assert_fails(good_debug_data(), variables, [], "severity")

    def test_wrong_output_type_fails(self):
        variables = good_variables_data()
        variables["Variables"][0]["Globals"]["var_severity"] = True
        self.assert_fails(good_debug_data(), variables, [], "exact type")

    def test_jira_key_output_must_match_created_key(self):
        variables = good_variables_data()
        variables["Variables"][0]["Globals"]["var_jiraKey"] = "CE-999"
        self.assert_fails(good_debug_data(), variables, [], "created issue")

    def test_double_jira_execution_fails(self):
        debug = good_debug_data()
        debug["ElementExecutions"].append({"ElementId": "JiraCreate1"})
        self.assert_fails(debug, good_variables_data(), [], "Jira create")

    def test_missing_slack_execution_fails(self):
        debug = good_debug_data()
        debug["ElementExecutions"] = [
            item
            for item in debug["ElementExecutions"]
            if item["ElementId"] != "SlackSend1"
        ]
        self.assert_fails(debug, good_variables_data(), [], "Slack send")

    def test_wrong_slack_channel_fails(self):
        variables = good_variables_data()
        response = variables["Variables"][0]["Elements"][1]["Outputs"]["response"]
        response["channel"] = "C0OTHER"
        self.assert_fails(good_debug_data(), variables, [], "went to")

    def test_slack_text_missing_correlation_fails(self):
        variables = good_variables_data()
        response = variables["Variables"][0]["Elements"][1]["Outputs"]["response"]
        response["message"]["text"] = "[Sev1] escalation"
        self.assert_fails(good_debug_data(), variables, [], "text")


class SideEffectHarvestTests(unittest.TestCase):
    def test_prefers_numeric_id_for_deletion_and_keeps_key(self):
        effects = checker.harvest_side_effects(CONTRACT, good_variables_data())
        self.assertEqual(effects["jira_keys"], ["CE-101"])
        self.assertEqual(effects["jira_issues"], ["10001"])
        self.assertEqual(effects["slack_messages"], [["C01H4SPS77W", "111.222"]])

    def test_falls_back_to_key_when_no_id(self):
        variables = copy.deepcopy(good_variables_data())
        del variables["Variables"][0]["Elements"][0]["Outputs"]["response"]["id"]
        effects = checker.harvest_side_effects(CONTRACT, variables)
        self.assertEqual(effects["jira_issues"], ["CE-101"])


class JournalTests(unittest.TestCase):
    def test_roundtrip_and_bad_line_tolerance(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "ids.jsonl"
            with patch.object(escalation_is, "JOURNAL", journal):
                escalation_is.record_created_id("jira_issue", "10001")
                escalation_is.record_created_id(
                    "slack_message", ["C01H4SPS77W", "111.222"]
                )
                with journal.open("a", encoding="utf-8") as handle:
                    handle.write("not json\n")
                records = escalation_is.read_journal(journal)
        self.assertEqual(records["jira_issue"], ["10001"])
        self.assertEqual(records["slack_message"], [["C01H4SPS77W", "111.222"]])

    def test_missing_journal_reads_empty(self):
        self.assertEqual(
            escalation_is.read_journal(Path("/nonexistent/ids.jsonl")), {}
        )


class SeedTests(unittest.TestCase):
    def test_seed_writes_consistent_case(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [sys.executable, str(HERE / "seed.py")],
                cwd=directory,
                check=True,
                capture_output=True,
            )
            seed = json.loads((Path(directory) / "seed.json").read_text())
        self.assertEqual(set(seed["inputs"]), set(SEED["inputs"]))
        correlation = seed["correlationId"]
        self.assertTrue(correlation.startswith("ESC-BPMN-"))
        self.assertEqual(seed["inputs"]["correlationId"], correlation)
        self.assertEqual(seed["expected"]["caseKey"], correlation)
        self.assertEqual(seed["expected"]["severity"], "Sev1")

    def test_prompt_declares_every_seeded_input(self):
        # Seed/prompt lockstep: an input the prompt never names would grade an
        # unstated requirement when the grader passes it to `bpmn debug`.
        task_text = (HERE / "customer_escalation_triage.yaml").read_text(
            encoding="utf-8"
        )
        for name in SEED["inputs"]:
            self.assertIn(name, task_text, f"prompt never names input {name}")

    def test_yaml_timeout_covers_debug_budget(self):
        task_text = (HERE / "customer_escalation_triage.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "timeout: 1200",
            task_text,
            "behavior criterion timeout drifted from the checker's budget",
        )
        self.assertLess(checker.DEBUG_TIMEOUT_SECONDS, 1200)


class PackageBindingTests(unittest.TestCase):
    def test_real_uuid_accepted(self):
        self.assertTrue(
            packager.is_real_connection_key(
                "5da18ec0-7de1-4e57-aaf1-ddc8a369c199"
            )
        )

    def test_stub_and_garbage_rejected(self):
        self.assertFalse(
            packager.is_real_connection_key(
                "00000000-0000-0000-0000-000000000000"
            )
        )
        self.assertFalse(packager.is_real_connection_key(""))
        self.assertFalse(packager.is_real_connection_key("not-a-uuid"))


if __name__ == "__main__":
    unittest.main()
