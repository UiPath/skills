"""Focused tests for the complex escalation seed and checker helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load(
    "customer_escalation_orchestration_checker",
    "check_customer_escalation_orchestration.py",
)
seed = _load("customer_escalation_orchestration_seed", "seed.py")


def _payload(**outputs):
    return {"Variables": {"Globals": outputs}}


class CustomerEscalationOrchestrationTests(unittest.TestCase):
    def test_seed_covers_success_duplicate_and_exception_paths(self) -> None:
        document = seed.build_seed()
        cases = document["cases"]

        self.assertEqual(len(cases), 4)
        self.assertEqual(cases[0]["expected"]["route"], "EngineeringEscalation")
        self.assertEqual(cases[1]["expected"]["jiraAction"], "UpdateExisting")
        self.assertEqual(cases[2]["expected"]["exceptionCode"], "SALESFORCE_NO_MATCH")
        self.assertEqual(cases[3]["expected"]["exceptionCode"], "INVALID_AGENT_JSON")

    def test_seed_case_keys_do_not_leak_expected_severity(self) -> None:
        document = seed.build_seed()
        keys = [case["inputs"]["correlationId"] for case in document["cases"]]

        self.assertEqual(len(keys), len(set(keys)))
        for key in keys:
            self.assertNotIn("SEV", key.upper())
            self.assertNotIn("DUPLICATE", key.upper())

    def test_named_comparison_accepts_boolean_variants(self) -> None:
        checker.assert_named_equals(
            _payload(engineeringHandoff="yes"), "engineeringHandoff", True
        )
        checker.assert_named_equals(
            _payload(engineeringHandoff="No"), "engineeringHandoff", False
        )

    def test_named_comparison_rejects_wrong_route(self) -> None:
        with self.assertRaisesRegex(SystemExit, "expected 'EngineeringEscalation'"):
            checker.assert_named_equals(
                _payload(route="HumanReview"), "route", "EngineeringEscalation"
            )

    def test_structural_checker_accepts_expected_shape(self) -> None:
        flow = {
            "nodes": [
                {"id": "start", "type": "core.trigger.manual"},
                {
                    "id": "parse_outlook_email",
                    "type": "core.action.script",
                    "inputs": {"script": "parse Outlook sender subject body attachments"},
                },
                {
                    "id": "salesforce_lookup",
                    "type": "core.action.script",
                    "inputs": {"script": "Salesforce account contact case lookup SALESFORCE_NO_MATCH"},
                },
                {
                    "id": "severity_agent",
                    "type": "core.action.script",
                    "inputs": {"script": "severity agent parses severityAgentJson INVALID_AGENT_JSON"},
                },
                {
                    "id": "jira_duplicate_search",
                    "type": "core.action.script",
                    "inputs": {"script": "Jira duplicate search create update"},
                },
                {
                    "id": "exception_decision",
                    "type": "core.logic.decision",
                    "inputs": {"label": "exception routing"},
                },
                {
                    "id": "severity_switch",
                    "type": "core.logic.switch",
                    "inputs": {"label": "Sev1 Sev2 Sev3 routing"},
                },
                {
                    "id": "draft_agent",
                    "type": "core.action.script",
                    "inputs": {"script": "draft agent prepares responseDraft"},
                },
                {
                    "id": "drive_summary",
                    "type": "core.action.script",
                    "inputs": {"script": "Drive summary and attachment archive"},
                },
                {
                    "id": "slack_alert",
                    "type": "core.action.script",
                    "inputs": {"script": "Slack alert for Sev1"},
                },
                {
                    "id": "outlook_ack",
                    "type": "core.action.script",
                    "inputs": {"script": "Outlook draft acknowledgement"},
                },
                {"id": "end", "type": "core.control.end"},
            ],
            "edges": [
                {"sourceNodeId": "start", "targetNodeId": "parse_outlook_email"},
                {"sourceNodeId": "parse_outlook_email", "targetNodeId": "salesforce_lookup"},
                {"sourceNodeId": "salesforce_lookup", "targetNodeId": "severity_agent"},
                {"sourceNodeId": "severity_agent", "targetNodeId": "jira_duplicate_search"},
                {"sourceNodeId": "jira_duplicate_search", "targetNodeId": "exception_decision"},
                {"sourceNodeId": "exception_decision", "targetNodeId": "severity_switch"},
                {"sourceNodeId": "severity_switch", "targetNodeId": "draft_agent"},
                {"sourceNodeId": "draft_agent", "targetNodeId": "drive_summary"},
                {"sourceNodeId": "drive_summary", "targetNodeId": "slack_alert"},
                {"sourceNodeId": "slack_alert", "targetNodeId": "outlook_ack"},
                {"sourceNodeId": "outlook_ack", "targetNodeId": "end"},
            ],
            "variables": {
                "globals": [
                    {"id": name, "direction": "out"}
                    for name in checker.REQUIRED_OUTPUTS
                ]
            },
        }

        path = HERE / "tmp_flow_for_test.json"
        path.write_text(json.dumps(flow), encoding="utf-8")
        original = checker.FLOW_GLOB
        try:
            checker.FLOW_GLOB = str(path)
            checker.assert_structural_orchestration()
        finally:
            checker.FLOW_GLOB = original
            path.unlink(missing_ok=True)

    def test_structural_checker_rejects_basic_triage_shape(self) -> None:
        flow = {
            "nodes": [
                {"id": "start", "type": "core.trigger.manual"},
                {"id": "classify", "type": "core.action.script", "inputs": {"script": "severity only"}},
                {"id": "end", "type": "core.control.end"},
            ],
            "edges": [{"sourceNodeId": "start", "targetNodeId": "classify"}],
            "variables": {"globals": []},
        }

        path = HERE / "tmp_basic_flow_for_test.json"
        path.write_text(json.dumps(flow), encoding="utf-8")
        original = checker.FLOW_GLOB
        try:
            checker.FLOW_GLOB = str(path)
            with self.assertRaisesRegex(SystemExit, "multi-stage orchestration"):
                checker.assert_structural_orchestration()
        finally:
            checker.FLOW_GLOB = original
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
