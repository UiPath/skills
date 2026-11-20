#!/usr/bin/env python3
"""Unit tests for the escalation e2e graders. Stdlib, pytest and PyYAML (the
budget guards parse the task YAML; the workflow installs pyyaml for this job
— see .github/workflows/test-helpers.yml).

Proportionate by design: the live CLI surface is exercised by the eval run
itself; these tests pin the pure logic — contract resolution, runtime
assertions, journal roundtrip, and the seed/prompt lockstep.
"""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest

import yaml
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SHARED_SETUP = HERE.parent.parent / "_setup"


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
import _shared.bpmn_live as live  # noqa: E402
from _shared import bpmn_check  # noqa: E402

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
    <bpmn:scriptTask id="Classify1" scriptFormat="JavaScript">
      <bpmn:script><![CDATA[return vars.customerTier === "Enterprise" ? "Sev1" : (vars.serviceState === "Degraded" ? "Sev2" : "Sev3");]]></bpmn:script>
    </bpmn:scriptTask>
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
          <uipath:input target="query" name="send_as" value="user"/>
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
        "slackChannelId": "C0B2FDZD1M3",
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
                                "channel": "C0B2FDZD1M3",
                                "message": {
                                    "text": "[Sev1] ESC-BPMN-test escalation",
                                    "ts": "111.222",
                                },
                            }
                        },
                    },
                    # Appended, not prepended: tests index Elements[0].
                    {
                        "ElementId": "Classify1",
                        "Outputs": {"response": "Sev1"},
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
            checker.CheckFailure, "has no uipath-salesforce-slack step"
        ):
            self._resolve(no_slack)

    def test_any_jira_create_operation_resolves(self):
        # Several Jira objects create the same ticket, and the Studio Web
        # builder emits the generic `issue` object (run
        # adhoc-2026-11-14_08-01-54); the request names no operation, and the
        # tenant reread proves the ticket whichever one made it.
        for path in (
            "/curated_create_issue",
            "/curated-issue-create",
            "/curated_issue",
            "/create_issue",
            "/issue",
            "/rest/api/3/issue",
        ):
            with self.subTest(path=path):
                variant = SAMPLE_BPMN.replace("/curated_create_issue", path)
                self.assertEqual(
                    self._resolve(variant).jira_create_ids, ("JiraCreate1",)
                )

    def test_a_process_that_never_names_the_other_severities_fails(self):
        hardcoded = SAMPLE_BPMN.replace(
            'return vars.customerTier === "Enterprise" ? "Sev1" : (vars.serviceState === "Degraded" ? "Sev2" : "Sev3");',
            'return "Sev1";',
        )
        with self.assertRaisesRegex(checker.CheckFailure, "never names"):
            self._resolve(hardcoded)


class StudioWebLayoutTests(unittest.TestCase):
    """adhoc-2026-11-14_08-01-54: the Studio Web agent's correct project sat at
    CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn, and the old
    graders, pinned to CustomerEscalationTriageSolution/.../CustomerEscalationTriage.bpmn,
    failed it as missing before running it."""

    def test_the_studio_web_project_is_found_and_resolves(self):
        sw = (HERE / "fixtures" / "sw_Process.bpmn").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "CustomerEscalationTriage" / "CustomerEscalationTriage"
            project.mkdir(parents=True)
            (project / "project.uiproj").write_text('{"Name": "CustomerEscalationTriage"}')
            (project / "Process.bpmn").write_text(sw, encoding="utf-8")
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                self.assertFalse(Path("CustomerEscalationTriageSolution/CustomerEscalationTriage/CustomerEscalationTriage.bpmn").is_file())
                found = bpmn_check.locate_bpmn(f"{checker.NAME}.bpmn", [checker.LIVE_RUN_DIR])
                self.assertEqual(found.name, "Process.bpmn")
                self.assertEqual((packager.NAME, packager.LIVE_RUN_DIR), (checker.NAME, checker.LIVE_RUN_DIR))
                contract = checker.resolve_contract(found)
            finally:
                os.chdir(cwd)
        self.assertTrue(contract.jira_create_ids and contract.slack_send_ids)


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


def with_lookup_steps(debug: dict, variables: dict) -> tuple:
    """The good run plus a Jira search before the create, a Jira comment after
    it and a Slack channel lookup: same connectors, none returns an issue key
    or a message ts (Jira /search/jql, /issue/{id}/comment, Slack
    conversations.info response shapes)."""
    contract = checker.Contract(
        output_ids=CONTRACT.output_ids,
        jira_create_ids=("JiraComment1", "JiraCreate1", "JiraSearch1"),
        slack_send_ids=("SlackInfo1", "SlackSend1"),
    )
    debug["ElementExecutions"][1:1] = [{"ElementId": "JiraSearch1"}, {"ElementId": "SlackInfo1"}]
    debug["ElementExecutions"].append({"ElementId": "JiraComment1"})
    variables["Variables"][0]["Elements"] += [
        {"ElementId": "JiraSearch1", "Outputs": {"response": {"issues": [], "isLast": True}}},
        {
            "ElementId": "JiraComment1",
            "Outputs": {
                "response": {
                    "self": "https://x/rest/api/3/issue/10001/comment/10050",
                    "id": "10050",
                    "created": "2026-11-19T10:00:00.000+0000",
                }
            },
        },
        {
            "ElementId": "SlackInfo1",
            "Outputs": {"response": {"ok": True, "channel": {"id": "C0B2FDZD1M3", "name": "coding-agent-testing"}}},
        },
    ]
    return contract, debug, variables


class OtherStepsOnTheSameConnectorTests(unittest.TestCase):
    def test_a_search_comment_and_lookup_do_not_count_as_the_create_or_the_post(self):
        contract, debug, variables = with_lookup_steps(good_debug_data(), good_variables_data())
        self.assertEqual(checker.assert_outcome(contract, SEED, debug, variables, []), "CE-101")

    def test_a_comment_id_is_not_journalled_as_an_issue_to_delete(self):
        contract, _debug, variables = with_lookup_steps(good_debug_data(), good_variables_data())
        effects = checker.harvest_side_effects(contract, variables)
        self.assertEqual(effects["jira_issues"], ["10001"])
        self.assertEqual(effects["jira_keys"], ["CE-101"])

    def test_the_create_running_twice_still_fails(self):
        contract, debug, variables = with_lookup_steps(good_debug_data(), good_variables_data())
        debug["ElementExecutions"].append({"ElementId": "JiraCreate1"})
        with self.assertRaisesRegex(checker.CheckFailure, "Jira create"):
            checker.assert_outcome(contract, SEED, debug, variables, [])


def with_step(contract_field: str, step: str, response: dict, debug: dict, variables: dict) -> tuple:
    ids = getattr(CONTRACT, contract_field) + (step,)
    contract = checker.Contract(
        output_ids=CONTRACT.output_ids,
        jira_create_ids=ids if contract_field == "jira_create_ids" else CONTRACT.jira_create_ids,
        slack_send_ids=ids if contract_field == "slack_send_ids" else CONTRACT.slack_send_ids,
    )
    debug["ElementExecutions"].append({"ElementId": step})
    variables["Variables"][0]["Elements"].append({"ElementId": step, "Outputs": {"response": response}})
    return contract, debug, variables


class OneIssueOneMessageTests(unittest.TestCase):
    def test_a_get_issue_of_the_created_key_is_one_issue(self):
        contract, debug, variables = with_step(
            "jira_create_ids", "JiraGet1", {"key": "CE-101", "id": "10001", "fields": {}},
            good_debug_data(), good_variables_data(),
        )
        self.assertEqual(checker.assert_outcome(contract, SEED, debug, variables, []), "CE-101")

    def test_a_get_issue_is_not_journalled_twice(self):
        contract, _debug, variables = with_step(
            "jira_create_ids", "JiraGet1", {"key": "CE-101", "id": "10001", "fields": {}},
            good_debug_data(), good_variables_data(),
        )
        effects = checker.harvest_side_effects(contract, variables)
        self.assertEqual(effects["jira_keys"], ["CE-101"])
        self.assertEqual(effects["jira_issues"], ["10001"])

    def test_a_get_issue_alone_still_reaches_the_tenant_reread(self):
        debug, variables = good_debug_data(), good_variables_data()
        debug["ElementExecutions"] = [
            e for e in debug["ElementExecutions"] if e["ElementId"] != "JiraCreate1"
        ]
        variables["Variables"][0]["Elements"] = [
            e for e in variables["Variables"][0]["Elements"] if e["ElementId"] != "JiraCreate1"
        ]
        contract, debug, variables = with_step(
            "jira_create_ids", "JiraGet1", {"key": "CE-101", "id": "10001"}, debug, variables
        )
        contract = checker.Contract(CONTRACT.output_ids, ("JiraGet1",), CONTRACT.slack_send_ids)
        self.assertEqual(checker.assert_outcome(contract, SEED, debug, variables, []), "CE-101")

    def test_two_creates_with_different_keys_fail(self):
        contract, debug, variables = with_step(
            "jira_create_ids", "JiraCreate2", {"key": "CE-102", "id": "10002"},
            good_debug_data(), good_variables_data(),
        )
        with self.assertRaisesRegex(checker.CheckFailure, "Jira create"):
            checker.assert_outcome(contract, SEED, debug, variables, [])

    def test_two_posts_with_different_timestamps_fail(self):
        contract, debug, variables = with_step(
            "slack_send_ids", "SlackSend2",
            {"ts": "333.444", "channel": "C0B2FDZD1M3", "message": {"text": "[Sev1] ESC-BPMN-test", "ts": "333.444"}},
            good_debug_data(), good_variables_data(),
        )
        with self.assertRaisesRegex(checker.CheckFailure, "Slack send"):
            checker.assert_outcome(contract, SEED, debug, variables, [])


class RuleEncodingTests(unittest.TestCase):
    def test_the_severity_check_is_the_shared_one(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sample.bpmn"
            path.write_text(SAMPLE_BPMN, encoding="utf-8")
            with patch.object(checker, "assert_rule_encoded", side_effect=checker.CheckFailure("shared")):
                with self.assertRaisesRegex(checker.CheckFailure, "shared"):
                    checker.resolve_contract(path)


class SideEffectHarvestTests(unittest.TestCase):
    def test_prefers_numeric_id_for_deletion_and_keeps_key(self):
        effects = checker.harvest_side_effects(CONTRACT, good_variables_data())
        self.assertEqual(effects["jira_keys"], ["CE-101"])
        self.assertEqual(effects["jira_issues"], ["10001"])
        self.assertEqual(effects["slack_messages"], [["C0B2FDZD1M3", "111.222"]])

    def test_falls_back_to_key_when_no_id(self):
        variables = copy.deepcopy(good_variables_data())
        del variables["Variables"][0]["Elements"][0]["Outputs"]["response"]["id"]
        effects = checker.harvest_side_effects(CONTRACT, variables)
        self.assertEqual(effects["jira_issues"], ["CE-101"])


class OwnedJiraTargetTests(unittest.TestCase):
    CORRELATION = SEED["correlationId"]

    def _owned(self, effects, summaries):
        def read(_connection, key):
            summary = summaries[key]
            if isinstance(summary, Exception):
                raise summary
            return {"summary": summary}

        with patch.object(escalation_is, "get_issue_fields", side_effect=read):
            return checker.owned_jira_targets(effects, "conn", self.CORRELATION)

    def test_only_issues_whose_summary_carries_the_correlation_id_are_owned(self):
        effects = {"jira_targets": {"CE-101": "10001", "CE-7": "7"}}
        owned = self._owned(
            effects, {"CE-101": f"[Sev1] {self.CORRELATION} escalation", "CE-7": "an existing ticket"}
        )
        self.assertEqual(owned, ["10001"])

    def test_an_unreadable_issue_is_not_owned(self):
        effects = {"jira_targets": {"CE-101": "10001"}}
        self.assertEqual(self._owned(effects, {"CE-101": checker.CheckFailure("boom")}), [])

    def test_reads_are_capped_and_the_rest_reported(self):
        keys = {f"CE-{n}": str(n) for n in range(1, 6)}
        reads = []

        def read(_connection, key):
            reads.append(key)
            return {"summary": self.CORRELATION}

        out = io.StringIO()
        with patch.object(escalation_is, "get_issue_fields", side_effect=read), redirect_stdout(out):
            owned = checker.owned_jira_targets({"jira_targets": keys}, "conn", self.CORRELATION)
        self.assertEqual(len(reads), checker.MAX_OWNED_KEY_READS)
        self.assertEqual(owned, ["1", "2"])
        self.assertIn("NOTE", out.getvalue())
        self.assertIn("CE-5", out.getvalue())

    def test_harvest_maps_each_key_to_its_deletion_target(self):
        effects = checker.harvest_side_effects(CONTRACT, good_variables_data())
        self.assertEqual(effects["jira_targets"], {"CE-101": "10001"})


class JournalTests(unittest.TestCase):
    def test_roundtrip_and_bad_line_tolerance(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "ids.jsonl"
            with patch.object(escalation_is, "JOURNAL", journal):
                escalation_is.record_created_id("jira_issue", "10001")
                escalation_is.record_created_id(
                    "slack_message", ["C0B2FDZD1M3", "111.222"]
                )
                with journal.open("a", encoding="utf-8") as handle:
                    handle.write("not json\n")
                records = escalation_is.read_journal(journal)
        self.assertEqual(records["jira_issue"], ["10001"])
        self.assertEqual(records["slack_message"], [["C0B2FDZD1M3", "111.222"]])

    def test_missing_journal_reads_empty(self):
        self.assertEqual(
            escalation_is.read_journal(Path("/nonexistent/ids.jsonl")), {}
        )


class SlackLogScanTests(unittest.TestCase):
    def test_a_deeply_nested_string_does_not_stop_the_scan(self):
        post = '{"channel": "C0B2FDZD1M3", "ts": "1763405123.456789", "message": {}}'
        text = '{"a":' + "[" * 100000 + "\n" + post
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "debug.log"
            log.write_text(text, encoding="utf-8")
            with patch.object(escalation_is, "JOURNAL", root / "ids.jsonl"):
                escalation_is.journal_slack_posts_in_log(log)
                records = escalation_is.read_journal(root / "ids.jsonl")
        self.assertEqual(records["slack_message"], [["C0B2FDZD1M3", "1763405123.456789"]])


class OtherChannelJournalTests(unittest.TestCase):
    OTHER = {"channel": "C0OTHER0000", "ts": "1763405123.456789", "message": {}}

    def test_other_channel_post_is_not_journalled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log = root / "debug.log"
            log.write_text(json.dumps(self.OTHER), encoding="utf-8")
            with patch.object(escalation_is, "JOURNAL", root / "ids.jsonl"):
                escalation_is.journal_slack_posts_in_log(log)
                escalation_is.journal_slack_posts_in_log(root / "none.log", self.OTHER)
                with patch.object(
                    escalation_is, "element_output_records",
                    return_value=[{"response": self.OTHER}],
                ):
                    escalation_is.journal_slack_posts({}, {"SlackSend1"})
                records = escalation_is.read_journal(root / "ids.jsonl")
        self.assertNotIn("slack_message", records)

    def test_teardown_does_not_delete_a_planted_other_channel_pair(self):
        deleted = []
        planted = [["C0OTHER0000", "1763405123.456789"]]
        mine = [escalation_is.SLACK_CHANNEL, "1763405124.456789"]
        records = {"jira_issue": [], "slack_message": planted + [mine]}
        with tempfile.TemporaryDirectory() as tmp:
            patches = {
                "JOURNAL": Path(tmp) / "ids.jsonl",
                "read_journal": lambda: records,
                "connection_ids": lambda **_k: {
                    escalation_is.JIRA_CONNECTOR: "j",
                    escalation_is.SLACK_CONNECTOR: "s",
                },
                "delete_slack_message": lambda _c, ch, ts, **_k: deleted.append((ch, ts)) or True,
            }
            with patch.multiple(escalation_is, **patches):
                spec = importlib.util.spec_from_file_location(
                    "teardown_planted", SHARED_SETUP / "teardown_escalation.py"
                )
                module = importlib.util.module_from_spec(spec)
                with redirect_stdout(io.StringIO()):
                    try:
                        spec.loader.exec_module(module)
                    except SystemExit:
                        pass
        self.assertEqual(deleted, [tuple(mine)])


class PartialRunJournalTests(unittest.TestCase):
    PARTIAL_LOG = (
        'created CE-7 and then CE-8 in the project\n'
        '{"channel": "C0B2FDZD1M3", "ts": "1763405123.456789"}\n'
    )

    def _run(self, *, debug_error=None, variables_error=None, debug_data=None, log=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            live = root / "live"
            live.mkdir()
            (live / "debug.log").write_text(self.PARTIAL_LOG if log is None else log, encoding="utf-8")
            journal = root / "ids.jsonl"
            summaries = {"CE-7": "[Sev1] ESC-BPMN-test escalation", "CE-8": "someone else's"}

            def debug(*args, **kwargs):
                if debug_error:
                    raise debug_error
                return (debug_data or good_debug_data()), "instance-1"

            def cli(*args, **kwargs):
                if variables_error:
                    raise variables_error
                return object()

            with patch.object(checker, "LIVE_RUN_DIR", live), patch.object(
                escalation_is, "JOURNAL", journal
            ), patch.object(checker, "run_debug", debug), patch.object(
                checker, "run_cli", cli
            ), patch.object(
                checker, "payload_data", lambda *a: (None, good_variables_data())
            ), patch.object(
                escalation_is,
                "get_issue_fields",
                lambda conn, key: {"summary": summaries[key]},
            ):
                try:
                    checker.run_and_read(SEED, live, "jira-conn")
                except (checker.CheckFailure, subprocess.TimeoutExpired) as error:
                    return escalation_is.read_journal(journal), error
                return escalation_is.read_journal(journal), None

    def test_a_debug_failure_journals_only_this_runs_records(self):
        records, error = self._run(debug_error=checker.CheckFailure("timed out"))
        self.assertIsInstance(error, checker.CheckFailure)
        self.assertEqual(records["jira_issue"], ["CE-7"])
        self.assertNotIn("slack_message", records)

    def test_a_variables_read_failure_journals_from_the_log(self):
        records, error = self._run(variables_error=subprocess.TimeoutExpired("uip", 120))
        self.assertIsInstance(error, subprocess.TimeoutExpired)
        self.assertEqual(records["jira_issue"], ["CE-7"])

    def test_a_variables_read_failure_journals_keys_from_the_debug_response(self):
        debug_data = {**good_debug_data(), "Output": "created CE-7 and CE-8"}
        records, error = self._run(
            variables_error=subprocess.TimeoutExpired("uip", 120), debug_data=debug_data, log=""
        )
        self.assertIsInstance(error, subprocess.TimeoutExpired)
        self.assertEqual(records["jira_issue"], ["CE-7"])
        self.assertNotIn("slack_message", records)

    def test_partial_log_reads_are_capped_and_the_rest_reported(self):
        reads = []

        def read(_conn, key):
            reads.append(key)
            return {"summary": SEED["correlationId"]}

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "debug.log"
            path.write_text("created CE-7 CE-8 CE-9 CE-10", encoding="utf-8")
            out = io.StringIO()
            with patch.object(escalation_is, "JOURNAL", Path(directory) / "ids.jsonl"), patch.object(
                escalation_is, "get_issue_fields", side_effect=read
            ), redirect_stdout(out):
                checker.journal_partial_log(SEED, path, "jira-conn")
        self.assertEqual(reads, ["CE-7", "CE-8"])
        self.assertIn("NOTE", out.getvalue())
        self.assertIn("CE-10", out.getvalue())

    def test_a_clean_read_journals_nothing_here(self):
        records, error = self._run()
        self.assertIsNone(error)
        self.assertEqual(records, {})


class SeedTests(unittest.TestCase):
    def test_seed_writes_consistent_case(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(
                [sys.executable, str(HERE / "_setup" / "seed.py")],
                cwd=directory,
                check=True,
                capture_output=True,
                # The issue-type id is read from the tenant; this test runs offline.
                env={**os.environ, "ESCALATION_JIRA_ISSUETYPE_ID": "10009", "PYTHONPATH": str(SHARED_SETUP)},
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

    def test_prompt_helper_names_each_connection_and_the_folder(self):
        task_text = (HERE / "customer_escalation_triage.yaml").read_text(
            encoding="utf-8"
        )
        helper = task_text.split("<!-- helper:start -->")[1].split(
            "<!-- helper:end -->"
        )[0]
        for name in escalation_is.CONNECTION_NAMES.values():
            self.assertIn(name, helper)
        self.assertIn(escalation_is.FOLDER_PATH, helper)

    def test_yaml_timeout_covers_every_step_budget(self):
        """The criterion must outlast the sum of the live CLI calls it makes.

        A substring match on the whole YAML would also match `turn_timeout`,
        and comparing against DEBUG_TIMEOUT_SECONDS alone ignores the other
        nine calls -- both pass by construction. Parse the criterion's own
        timeout and compare it against the whole worst-case path, so raising any one step
        budget past the ceiling fails here rather than as a SIGKILL that
        strands created Jira and Slack ids for post_run to sweep.
        """

        task = yaml.safe_load(
            (HERE / "customer_escalation_triage.yaml").read_text(encoding="utf-8")
        )
        behavior = [
            criterion
            for criterion in task["success_criteria"]
            if "check_customer_escalation_behavior.py" in criterion.get("command", "")
        ]
        self.assertEqual(len(behavior), 1, "expected one behavior criterion")
        criterion_timeout = behavior[0]["timeout"]

        budget = checker.WORST_CASE_PATH_TIMEOUT
        self.assertEqual(
            budget,
            sum(checker.STEP_TIMEOUTS)
            + checker.MAX_OWNED_KEY_READS * escalation_is.JIRA_READ_TIMEOUT,
        )
        self.assertLessEqual(
            budget,
            criterion_timeout,
            f"the worst-case path sums to {budget}s but the behavior criterion "
            f"allows {criterion_timeout}s -- raise the criterion or lower a step",
        )

    def test_task_timeout_covers_the_turn_plus_all_grading(self):
        """The same watchdog bounds the turns AND grading (tests/README.md).

        Grading only gets what the turn did not spend, and firing the watchdog
        reports the whole task TIMEOUT -- losing even the criteria that passed.
        So turn_timeout + every criterion timeout must fit under task_timeout.
        """

        task = yaml.safe_load(
            (HERE / "customer_escalation_triage.yaml").read_text(encoding="utf-8")
        )
        limits = task["run_limits"]
        # Only criterion types that carry a timeout field cost wall clock;
        # skill_triggered and command_executed are in-process transcript scans.
        # A run_command that omits `timeout:` still costs the model default 30.
        timed = {"run_command": 30, "pytest": 60}
        criteria = sum(
            c.get("timeout", timed[c["type"]])
            for c in task["success_criteria"]
            if c["type"] in timed
        )
        needed = limits["turn_timeout"] + criteria
        self.assertLessEqual(
            needed,
            limits["task_timeout"],
            f"a full {limits['turn_timeout']}s turn plus {criteria}s of grading "
            f"needs {needed}s but task_timeout is {limits['task_timeout']}s -- "
            "the watchdog would report TIMEOUT and discard passing criteria",
        )

    def test_post_run_sweep_can_finish_before_it_is_killed(self):
        """The journal sweep is the only cleanup that survives a SIGKILL.

        If its post_run timeout is shorter than the calls it makes, it dies
        mid-flight and leaks live Jira issues and Slack messages.
        """

        task = yaml.safe_load(
            (HERE / "customer_escalation_triage.yaml").read_text(encoding="utf-8")
        )
        sweeps = [
            step
            for step in task["post_run"]
            if "teardown_escalation.py" in step.get("command", "")
        ]
        self.assertEqual(len(sweeps), 1, "expected one journal sweep step")
        self.assertLessEqual(
            escalation_is.TEARDOWN_TIMEOUT,
            sweeps[0]["timeout"],
            f"the sweep can spend {escalation_is.TEARDOWN_TIMEOUT}s but post_run "
            f"allows {sweeps[0]['timeout']}s -- it would be killed mid-cleanup",
        )
        # coder_eval rejects the task outright above this; a budget that does
        # not fit the cap has to come out of the per-call timeouts.
        self.assertLessEqual(
            sweeps[0]["timeout"],
            escalation_is.POST_RUN_TIMEOUT_CAP,
            "post_run timeout exceeds coder_eval's cap; the task will not load",
        )


class PackageBindingTests(unittest.TestCase):
    def test_real_uuid_accepted(self):
        # Any well-formed UUID exercises this; no live id needed.
        self.assertTrue(
            packager.is_real_connection_key(
                "3f2b9c14-7ae5-4d61-9b28-c05f18ad6e73"
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


class LiveTargetTests(unittest.TestCase):
    """The grader creates real Jira and Slack records, so it runs only when
    the active `uip` session is the target the run configured.
    """

    CLOUD = {
        "UIPATH_URL": "https://alpha.uipath.com",
        "UIPATH_ORGANIZATION_ID": "5b2a7c1e-0d4f-4e8a-9c3b-6f1e2d7a8b90",
        "UIPATH_TENANT_ID": "a1c3e5f7-2b4d-4f6a-8c0e-1d3f5a7b9c2e",
    }
    ETE = {
        "UIPATH_URL": "https://as.loc",
        "UIPATH_ORGANIZATION_ID": "0e9d8c7b-6a5f-4e3d-8c2b-1a0f9e8d7c6b",
        "UIPATH_TENANT_ID": "7f6e5d4c-3b2a-4190-8f7e-6d5c4b3a2918",
    }

    @staticmethod
    def _status(env, organization, tenant, status="Logged in"):
        return {
            "Status": status,
            "BaseUrl": env["UIPATH_URL"],
            "Organization": organization,
            "OrganizationId": env["UIPATH_ORGANIZATION_ID"],
            "Tenant": tenant,
            "TenantId": env["UIPATH_TENANT_ID"],
        }

    def _assert(self, environ, status):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"Result": "Success", "Data": status}),
        )
        with patch.dict(escalation_is.os.environ, environ, clear=True), patch.object(
            escalation_is, "run_cli", return_value=completed
        ) as self.ran:
            return escalation_is.assert_live_target()

    def test_cloud_target_is_accepted(self):
        status = self._status(self.CLOUD, "codereval", "DefaultTenant")
        target = self._assert(self.CLOUD, status)
        self.assertEqual(target["TenantId"], self.CLOUD["UIPATH_TENANT_ID"])

    def test_configured_ete_target_is_accepted(self):
        status = self._status(self.ETE, "codereval_13100000", "CoderEvalProv_13100000")
        target = self._assert(self.ETE, status)
        self.assertEqual(target["BaseUrl"], "https://as.loc")

    def test_trailing_slash_and_id_case_do_not_matter(self):
        status = self._status(self.ETE, "codereval_13100000", "CoderEvalProv_13100000")
        status["BaseUrl"] += "/"
        status["TenantId"] = status["TenantId"].upper()
        self._assert(self.ETE, status)

    def test_session_on_another_target_is_refused(self):
        status = self._status(self.CLOUD, "codereval", "DefaultTenant")
        with self.assertRaises(escalation_is.CheckFailure) as caught:
            self._assert(self.ETE, status)
        self.assertIn("active profile", str(caught.exception))

    def test_session_on_another_tenant_of_the_same_org_is_refused(self):
        status = self._status(self.ETE, "codereval_13100000", "CoderEvalProv_13100000")
        status["TenantId"] = self.CLOUD["UIPATH_TENANT_ID"]
        with self.assertRaises(escalation_is.CheckFailure):
            self._assert(self.ETE, status)

    def test_no_configured_target_is_refused_before_the_session_is_read(self):
        status = self._status(self.CLOUD, "codereval", "DefaultTenant")
        for name in [None, *escalation_is.TARGET_ENV.values()]:
            environ = {} if name is None else {
                key: value for key, value in self.CLOUD.items() if key != name
            }
            with self.subTest(missing=name or "all"):
                with self.assertRaises(escalation_is.CheckFailure) as caught:
                    self._assert(environ, status)
                self.assertIn("no configured eval target", str(caught.exception))
                self.ran.assert_not_called()

    def test_logged_out_session_is_refused(self):
        status = self._status(self.CLOUD, "codereval", "DefaultTenant", status="Expired")
        with self.assertRaises(escalation_is.CheckFailure):
            self._assert(self.CLOUD, status)



class ConnectionResolutionTests(unittest.TestCase):
    """Connections are scoped by folder NAME, as in the flow suite.

    Every `connections list` row carries both `Folder` and `FolderKey`, so the
    key is read off the matched row at runtime rather than committed here.
    """

    @staticmethod
    def _row(connector, name, folder="uipath-maestro-flow", state="Enabled"):
        return {
            "Id": f"id-{connector}",
            "Name": name,
            "ConnectorKey": connector,
            "Folder": folder,
            "FolderKey": "3f2b9c14-7ae5-4d61-9b28-c05f18ad6e73",
            "State": state,
        }

    def _rows(self, **overrides):
        return [
            self._row(connector, name, **overrides)
            for connector, name in escalation_is.CONNECTION_NAMES.items()
        ]

    def _resolve(self, rows):
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout=json.dumps({"Result": "Success", "Data": rows})
        )
        with patch.object(escalation_is, "run_cli", return_value=completed):
            return escalation_is.connection_ids()

    def test_resolves_both_connections_in_the_target_folder(self):
        resolved = self._resolve(self._rows())
        self.assertEqual(set(resolved), set(escalation_is.CONNECTION_NAMES))

    def test_same_named_connection_in_another_folder_is_rejected(self):
        with self.assertRaises(escalation_is.CheckFailure) as caught:
            self._resolve(self._rows(folder="some-other-team"))
        self.assertIn(escalation_is.FOLDER_PATH, str(caught.exception))

    def test_connection_that_is_not_the_sandbox_one_is_rejected(self):
        for connector in escalation_is.CONNECTION_NAMES:
            rows = [
                self._row(key, f"{name}-other" if key == connector else name)
                for key, name in escalation_is.CONNECTION_NAMES.items()
            ]
            with self.subTest(connector=connector):
                with self.assertRaises(escalation_is.CheckFailure) as caught:
                    self._resolve(rows)
                self.assertIn(connector, str(caught.exception))

    def test_disabled_connection_is_rejected(self):
        with self.assertRaises(escalation_is.CheckFailure):
            self._resolve(self._rows(state="Disabled"))

    def test_name_only_match_accepted_when_no_row_reports_a_folder(self):
        # Older CLI / env that does not populate `Folder`. Flow's fallback.
        resolved = self._resolve(self._rows(folder=""))
        self.assertEqual(set(resolved), set(escalation_is.CONNECTION_NAMES))

    def test_list_is_refreshed_so_a_new_connection_is_not_missed(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"Result": "Success", "Data": self._rows()}),
        )
        with patch.object(escalation_is, "run_cli", return_value=completed) as ran:
            escalation_is.connection_ids()
        self.assertIn("--refresh", ran.call_args.args[0])


class TeardownRetryTests(unittest.TestCase):
    """Teardown mirrors the flow suite: retry once, then confirm by reread.

    A transient 5xx on the first delete must not leak a real ticket in the
    shared CE project.
    """

    def _run_teardown(self, **patches):
        records = {"jira_issue": ["CE-1"], "slack_message": []}
        defaults = {
            "read_journal": lambda: records,
            "connection_ids": lambda **_kwargs: {
                escalation_is.JIRA_CONNECTOR: "jira-conn",
                escalation_is.SLACK_CONNECTOR: "slack-conn",
            },
        }
        defaults.update(patches)
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / ".created-ids.jsonl"
            with patch.multiple(escalation_is, JOURNAL=journal, **defaults):
                spec = importlib.util.spec_from_file_location(
                    "teardown_run", SHARED_SETUP / "teardown_escalation.py"
                )
                module = importlib.util.module_from_spec(spec)
                out = io.StringIO()
                try:
                    with redirect_stdout(out):
                        spec.loader.exec_module(module)
                except SystemExit:
                    pass
        return out.getvalue()

    def test_slack_only_journal_does_not_need_the_jira_connection(self):
        deleted = []
        asked = []

        def resolve(*, connectors=None, **_kwargs):
            asked.append(connectors)
            if escalation_is.JIRA_CONNECTOR in (connectors or escalation_is.CONNECTION_NAMES):
                raise escalation_is.CheckFailure("no Jira connection")
            return {escalation_is.SLACK_CONNECTOR: "slack-conn"}

        records = {"jira_issue": [], "slack_message": [[escalation_is.SLACK_CHANNEL, "1700000000.000001"]]}
        output = self._run_teardown(
            read_journal=lambda: records,
            connection_ids=resolve,
            delete_slack_message=lambda _c, ch, ts, **_k: deleted.append((ch, ts)) or True,
        )
        self.assertEqual(deleted, [(escalation_is.SLACK_CHANNEL, "1700000000.000001")], output)
        self.assertEqual(asked, [(escalation_is.SLACK_CONNECTOR,)])

    def test_sweep_stops_at_the_deadline_and_names_what_it_skipped(self):
        now = [0.0]
        started = []

        def slow_slack(_conn, _channel, ts, **_kwargs):
            started.append(now[0])
            now[0] += escalation_is.TEARDOWN_DELETE_TIMEOUT
            return True

        records = {
            "jira_issue": [],
            "slack_message": [[escalation_is.SLACK_CHANNEL, f"1700000000.{n:06d}"] for n in range(11)],
        }
        output = self._run_teardown(
            read_journal=lambda: records,
            delete_slack_message=slow_slack,
            _now=lambda: now[0],
        )
        skipped = [line for line in output.splitlines() if line.startswith("WARN: skipped Slack")]
        self.assertTrue(skipped, "nothing was skipped past the deadline")
        self.assertEqual(len(started) + len(skipped), 11)
        for ts in ("1700000000.%06d" % n for n in range(11 - len(skipped), 11)):
            self.assertTrue(any(ts in line for line in skipped), ts)
        self.assertLessEqual(
            max(started) + escalation_is.TEARDOWN_DELETE_TIMEOUT,
            escalation_is.POST_RUN_TIMEOUT_CAP,
        )

    def test_slow_connection_lookup_spends_the_same_budget(self):
        now = [0.0]
        lookup_timeouts = []
        started = []

        def slow_lookup(**kwargs):
            lookup_timeouts.append(kwargs["timeout"])
            now[0] += kwargs["timeout"]
            return {
                escalation_is.JIRA_CONNECTOR: "jira-conn",
                escalation_is.SLACK_CONNECTOR: "slack-conn",
            }

        def slow_slack(_conn, _channel, ts, **_kwargs):
            started.append(now[0])
            now[0] += escalation_is.TEARDOWN_DELETE_TIMEOUT
            return True

        records = {
            "jira_issue": [],
            "slack_message": [[escalation_is.SLACK_CHANNEL, f"1700000000.{n:06d}"] for n in range(11)],
        }
        output = self._run_teardown(
            read_journal=lambda: records,
            connection_ids=slow_lookup,
            delete_slack_message=slow_slack,
            _now=lambda: now[0],
        )
        self.assertTrue([l for l in output.splitlines() if l.startswith("WARN: skipped Slack")])
        self.assertLessEqual(
            max(started) + escalation_is.TEARDOWN_DELETE_TIMEOUT,
            escalation_is.POST_RUN_TIMEOUT_CAP,
        )
        self.assertLessEqual(lookup_timeouts[0], escalation_is.TEARDOWN_CONNECTIONS_TIMEOUT)

    def test_transient_first_failure_is_retried(self):
        attempts = []

        def flaky(_conn, issue, **_kwargs):
            attempts.append(issue)
            return len(attempts) > 1  # first call fails, second succeeds

        self._run_teardown(delete_jira_issue=flaky)
        self.assertEqual(len(attempts), 2, "teardown did not retry the delete")

    def test_reread_confirming_absence_counts_as_deleted(self):
        reread = []

        def always_unconfirmed(_conn, _issue, **_kwargs):
            return False

        def absent(_conn, issue, **_kwargs):
            reread.append(issue)
            return True

        self._run_teardown(
            delete_jira_issue=always_unconfirmed,
            jira_issue_absent=absent,
        )
        self.assertEqual(reread, ["CE-1"], "teardown never confirmed by reread")


class DeleteConfirmationTests(unittest.TestCase):
    """A provider's own absence phrase is proof, whatever status it rides on.

    Slack answers a delete of an already-gone message with 400 and
    `message_not_found` -- no 404, and "not found" underscored -- so a generic
    status gate reports a leak for a message that is in fact gone.
    """

    @staticmethod
    def _completed(stdout):
        return subprocess.CompletedProcess(args=[], returncode=1, stdout=stdout, stderr="")

    def test_slack_message_not_found_is_confirmed_absent(self):
        observed = json.dumps({
            "Result": "Failure",
            "Message": "400 Bad Request",
            "Instructions": '{"message":"message_not_found",'
                            '"providerMessage":"{\\"ok\\":false,\\"error\\":\\"message_not_found\\"}"}',
        })
        self.assertTrue(
            live.delete_target_is_absent(
                self._completed(observed), "slack message", "1788913576.470749"
            )
        )

    def test_unrelated_failure_is_not_confirmed_absent(self):
        observed = json.dumps({"Result": "Failure", "Message": "500 Internal Server Error"})
        self.assertFalse(
            live.delete_target_is_absent(
                self._completed(observed), "slack message", "1788913576.470749"
            )
        )


V1_SEND_AS = '<uipath:input target="query" name="send_as" value="user"/>'
V2_QUERY_TEMPLATE = (
    '<uipath:input name="queryParameters" type="json" target="queryParameters"><![CDATA[{}]]></uipath:input>'
)


class SendIdentityTests(unittest.TestCase):
    """Flow grades send_as because the runtime response cannot reveal it.

    A node posting as the default bot returns the same ts/channel/content as
    one posting as the required user, so this is only catchable on the
    authored artifact.
    """

    def _contract_from(self, bpmn: str):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "Identity.bpmn"
            path.write_text(bpmn, encoding="utf-8")
            return checker.resolve_contract(path)

    def test_default_bot_identity_fails(self):
        with self.assertRaisesRegex(checker.CheckFailure, "send_as"):
            self._contract_from(
                SAMPLE_BPMN.replace('name="send_as" value="user"', 'name="send_as" value="bot"')
            )

    def test_missing_send_as_fails(self):
        with self.assertRaisesRegex(checker.CheckFailure, "send_as"):
            self._contract_from(
                SAMPLE_BPMN.replace(
                    '<uipath:input target="query" name="send_as" value="user"/>', ""
                )
            )

    def test_user_identity_passes(self):
        self.assertTrue(self._contract_from(SAMPLE_BPMN).slack_send_ids)

    def test_v2_user_identity_passes(self):
        self.assertTrue(self._contract_from(self._v2('{"send_as":"user"}')).slack_send_ids)

    def test_v2_other_identity_fails(self):
        for payload in ('{"send_as":"bot"}', '{"send_as":"user "}', "{}", "not json"):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(checker.CheckFailure, "send_as"):
                    self._contract_from(self._v2(payload))

    def test_v1_trailing_space_fails(self):
        with self.assertRaisesRegex(checker.CheckFailure, "send_as"):
            self._contract_from(SAMPLE_BPMN.replace('name="send_as" value="user"', 'name="send_as" value="user "'))

    def test_both_shapes_on_one_node_fail(self):
        with self.assertRaisesRegex(checker.CheckFailure, "send_as"):
            self._contract_from(
                SAMPLE_BPMN.replace(V1_SEND_AS, V1_SEND_AS + V2_QUERY_TEMPLATE.format('{"send_as":"user"}'))
            )

    @staticmethod
    def _v2(payload: str) -> str:
        return SAMPLE_BPMN.replace(V1_SEND_AS, V2_QUERY_TEMPLATE.format(payload))


if __name__ == "__main__":
    unittest.main()
