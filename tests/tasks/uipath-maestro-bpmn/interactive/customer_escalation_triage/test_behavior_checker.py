#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


SCRIPT = Path(__file__).with_name("check_customer_escalation_behavior.py")
SPEC = importlib.util.spec_from_file_location("behavior_checker", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


class BehaviorCheckerTests(unittest.TestCase):
    @staticmethod
    def environment() -> checker.LiveEnvironment:
        return checker.LiveEnvironment(
            jira_connection_id="jira-connection",
            drive_connection_id="drive-connection",
            slack_connection_id="slack-connection",
        )

    @staticmethod
    def contract() -> checker.RuntimeContract:
        return checker.RuntimeContract(
            public_output_ids={"route": "output_route"},
            root_end_id="End",
            parallel_split_id="Split",
            parallel_join_id="Join",
            marker_id="Marker",
            marker_collection_id="MarkerCollection",
            error_end_id="ErrorEnd",
            error_boundary_id="Boundary",
            jira_create_id="JiraCreate",
            jira_update_id="JiraUpdate",
            drive_copy_id="DriveCopy",
            slack_send_id="SlackSend",
        )

    @staticmethod
    def jira_create_element(summary: str) -> ET.Element:
        node = ET.Element(checker.q(checker.BPMN_NS, "sendTask"), id="Jira")
        extensions = ET.SubElement(
            node,
            checker.q(checker.BPMN_NS, "extensionElements"),
        )
        activity = ET.SubElement(
            extensions,
            checker.q(checker.UIPATH_NS, "activity"),
        )
        body = {
            "fields": {
                "project": {"key": "=vars.JiraProjectKey"},
                "issuetype": {"id": "=vars.JiraIssueTypeId"},
                "reporter": {"id": "=vars.JiraReporterAccountId"},
                "summary": summary,
                "description": "=vars.CorrelationId",
            }
        }
        ET.SubElement(
            activity,
            checker.q(checker.UIPATH_NS, "input"),
            target="body",
            name="body",
            value=json.dumps(body),
        )
        return node

    def test_hidden_live_matrix_covers_all_required_outcome_families(self) -> None:
        self.assertEqual(len(checker.SCENARIOS), 14)
        self.assertRegex(checker.RUN_NONCE, r"^[0-9a-f]{12}$")
        correlations = {
            case.inputs["correlationId"] for case in checker.SCENARIOS
        }
        self.assertEqual(len(correlations), len(checker.SCENARIOS))
        for correlation in correlations:
            self.assertRegex(
                correlation,
                rf"^EVAL-live-alpha-{checker.RUN_NONCE}-.+-Exact$",
            )
        routes = {case.outputs["route"] for case in checker.SCENARIOS}
        failures = {
            case.outputs["failureReason"]
            for case in checker.SCENARIOS
        }
        self.assertEqual(
            routes,
            {
                "NewEscalation",
                "ExistingIssue",
                "ManualReview",
                "Informational",
            },
        )
        self.assertTrue(
            {
                "",
                "CrmNotFound",
                "CrmAmbiguous",
                "InvalidAgentOutput",
                "JiraUnavailable",
            }
            <= failures
        )
        self.assertEqual(
            sum(case.uses_error_boundary for case in checker.SCENARIOS),
            4,
        )
        self.assertEqual(
            {
                case.outputs["severity"]
                for case in checker.SCENARIOS
                if case.uses_error_boundary
            },
            {"Sev1", "Sev2"},
        )
        self.assertEqual(
            {
                (
                    case.outputs["severity"],
                    bool(case.inputs["duplicateIssueKey"].strip()),
                )
                for case in checker.SCENARIOS
                if case.uses_error_boundary
            },
            {
                ("Sev1", False),
                ("Sev1", True),
                ("Sev2", False),
                ("Sev2", True),
            },
        )
        self.assertTrue(
            any(
                case.outputs["route"] == "ExistingIssue"
                and case.outputs["severity"] == "Sev1"
                and case.outputs["jiraAction"] == "UpdateExisting"
                and not case.uses_error_boundary
                for case in checker.SCENARIOS
            )
        )
        self.assertTrue(
            any(
                case.uses_error_boundary
                and case.outputs["severity"] == "Sev2"
                and bool(case.inputs["duplicateIssueKey"].strip())
                for case in checker.SCENARIOS
            )
        )
        contextual_pair = [
            case
            for case in checker.SCENARIOS
            if case.name.startswith("informational-auto-disabled-")
        ]
        self.assertEqual(len(contextual_pair), 2)
        self.assertTrue(
            all(
                case.inputs["autoSendEnabled"] is False
                and case.outputs["responseMode"] == "Draft"
                for case in contextual_pair
            )
        )
        self.assertNotEqual(
            contextual_pair[0].inputs["businessImpact"],
            contextual_pair[1].inputs["businessImpact"],
        )
        self.assertEqual(
            {
                key: value
                for key, value in contextual_pair[0].outputs.items()
                if key != "caseKey"
            },
            {
                key: value
                for key, value in contextual_pair[1].outputs.items()
                if key != "caseKey"
            },
        )

    def test_public_outputs_are_read_by_exact_external_variable_id(self) -> None:
        contract = checker.RuntimeContract(
            public_output_ids={
                "route": "output_route",
                "engineeringNeeded": "output_engineeringNeeded",
            },
            root_end_id="End",
            parallel_split_id="Split",
            parallel_join_id="Join",
            marker_id="Marker",
            marker_collection_id="MarkerCollection",
            error_end_id="ErrorEnd",
            error_boundary_id="Boundary",
            jira_create_id="JiraCreate",
            jira_update_id="JiraUpdate",
            drive_copy_id="DriveCopy",
            slack_send_id="SlackSend",
        )
        scope = {
            "Globals": {
                "OutputRoute": "NewEscalation",
                "OutputEngineeringNeeded": True,
                "Route": "wrong internal value",
            }
        }
        self.assertEqual(
            checker.root_public_outputs(scope, contract),
            {
                "route": "NewEscalation",
                "engineeringNeeded": True,
            },
        )

    def test_connector_outputs_preserve_live_iteration_order(self) -> None:
        variables_data = {
            "Variables": [
                {
                    "Elements": [
                        {
                            "ElementId": "DriveCopy",
                            "Outputs": {"result": {"name": "first.txt"}},
                        },
                        {
                            "ElementId": "Other",
                            "Outputs": {"result": {"name": "ignored.txt"}},
                        },
                        {
                            "ElementId": "DriveCopy",
                            "Outputs": {"result": {"name": "second.txt"}},
                        },
                    ]
                }
            ]
        }
        self.assertEqual(
            checker.element_output_records(variables_data, "DriveCopy"),
            [
                {"result": {"name": "first.txt"}},
                {"result": {"name": "second.txt"}},
            ],
        )

    def test_connector_outputs_search_all_runtime_scopes(self) -> None:
        variables_data = {
            "Variables": [
                {
                    "Elements": [
                        {
                            "ElementId": "DriveCopy",
                            "Outputs": {"id": "first"},
                        }
                    ]
                },
                {
                    "Elements": [
                        {
                            "ElementId": "DriveCopy",
                            "Outputs": {"id": "second"},
                        }
                    ]
                },
            ]
        }

        self.assertEqual(
            checker.element_output_records(variables_data, "DriveCopy"),
            [{"id": "first"}, {"id": "second"}],
        )

    def test_marker_collection_is_read_by_scoped_variable_id(self) -> None:
        variables_data = {
            "Variables": [
                {"Globals": {"Other": ["ignored"]}},
                {
                    "Globals": {
                        "MarkerCollection": ["first.txt", "second.txt"]
                    }
                },
            ]
        }
        self.assertEqual(
            checker.runtime_variable_values(
                variables_data, "marker_collection"
            ),
            [["first.txt", "second.txt"]],
        )

    def test_connector_response_ids_ignore_nested_resource_metadata(self) -> None:
        outputs = [
            {
                "Response": {
                    "Owners": [{"PermissionId": "not-the-file-id"}],
                    "Id": "copied-file-id",
                }
            }
        ]

        self.assertEqual(
            checker.connector_response_values(outputs, "id"),
            ["copied-file-id"],
        )

    def test_runtime_contract_rejects_duplicate_connector_keys(self) -> None:
        process = ET.fromstring(
            f"""
            <bpmn:process
                xmlns:bpmn="{checker.BPMN_NS}"
                xmlns:uipath="{checker.UIPATH_NS}">
              <bpmn:sendTask id="First">
                <bpmn:extensionElements>
                  <uipath:activity>
                    <uipath:context>
                      <uipath:input name="connectorKey" value="duplicate" />
                      <uipath:input name="path" value="/same-path" />
                    </uipath:context>
                  </uipath:activity>
                </bpmn:extensionElements>
              </bpmn:sendTask>
              <bpmn:sendTask id="Second">
                <bpmn:extensionElements>
                  <uipath:activity>
                    <uipath:context>
                      <uipath:input name="connectorKey" value="duplicate" />
                      <uipath:input name="path" value="/same-path" />
                    </uipath:context>
                  </uipath:activity>
                </bpmn:extensionElements>
              </bpmn:sendTask>
            </bpmn:process>
            """
        )

        with self.assertRaisesRegex(
            checker.CheckFailure, "duplicate connector key"
        ):
            checker.index_runtime_connectors(process)

    def test_live_target_rejects_the_wrong_tenant(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "Status": "Logged in",
                        "BaseUrl": "https://alpha.uipath.com",
                        "Organization": "codereval",
                        "Tenant": "WrongTenant",
                    },
                }
            ),
            stderr="",
        )
        with (
            patch.object(checker, "run_cli", return_value=completed),
            self.assertRaisesRegex(
                checker.CheckFailure, "live grader must target"
            ),
        ):
            checker.assert_live_target()

    def test_task_blocks_cloud_mutations_but_allows_discovery(self) -> None:
        task_text = Path(__file__).with_name(
            "customer_escalation_triage.yaml"
        ).read_text(encoding="utf-8")
        match = re.search(
            r'Agent left BPMN cloud execution and mutation to the grader".*?'
            r"command_pattern: '([^']+)'",
            task_text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        pattern = re.compile(match.group(1))
        blocked = (
            "uip maestro bpmn debug Project",
            "uip --profile alpha --output=json maestro bpmn debug Project",
            'uip --log-file "/tmp/foo bar.log" maestro bpmn debug Project',
            "uip --log-file '/tmp/foo bar.log' maestro bpmn debug Project",
            'uip --output-filter "Data.foo == `x`" solution upload Eval.uipx',
            'uip maestro --log-file "/tmp/foo bar.log" bpmn debug Project',
            'uip maestro bpmn --output-filter "Data.foo == `x`" debug Project',
            "sh -c 'uip maestro bpmn debug Project'",
            'bash -c "uip solution upload Eval.uipx"',
            "env bash -c 'uip solution upload Eval.uipx'",
            "eval 'uip is resources run delete connector operation'",
            "command uip solution upload Eval.uipx",
            "exec uip solution upload Eval.uipx",
            "! uip solution upload Eval.uipx",
            "time uip solution upload Eval.uipx",
            "/usr/bin/env uip solution upload Eval.uipx",
            "env -u UNUSED uip solution upload Eval.uipx",
            "FOO=bar uip solution upload Eval.uipx",
            "UIPATH_PROFILE=alpha uip maestro bpmn debug Project",
            "(uip solution upload Eval.uipx)",
            "{ uip solution upload Eval.uipx; }",
            "if true; then uip solution upload Eval.uipx; fi",
            "while false; do uip maestro bpmn debug Project; done",
            "x=uip; $x solution upload Eval.uipx",
            'x=/usr/local/bin/uip; "$x" maestro bpmn debug Project',
            "$(which uip) solution upload Eval.uipx",
            "$(uip solution upload Eval.uipx)",
            "`uip maestro bpmn debug Project`",
            # Conservative by design: this task has no legitimate reason to
            # serialize cloud-mutating commands into a shell heredoc.
            "cat <<'EOF'\nuip solution upload Eval.uipx\nEOF",
            "/usr/local/bin/uip maestro bpmn debug Project",
            "uip maestro bpmn debug-instance cancel instance-id",
            "uip maestro bpmn process run Process",
            "uip maestro bpmn process publish Project",
            "uip solution upload Eval.uipx",
            "uip solution --output json upload Eval.uipx",
            '"uip" solution upload Eval.uipx',
            "'/usr/local/bin/uip' solution publish Eval.zip",
            '"$UIP" solution upload Eval.uipx',
            '"${UIP}" maestro bpmn debug Project',
            "uip solution publish Eval.zip",
            "uip solution deploy run Eval",
            "uip solution deploy activate Eval",
            "uip solution deploy uninstall Eval",
            "uip solution delete solution-id",
            "uip solution packages delete Eval 1.0.0",
            "uip solution projects publish solution-id project-id",
            "uip solution projects resync solution-id project-id",
            "uip solution project publish solution-id project-id",
            "uip solution project --output=json resync solution-id project-id",
            "uip is connections create slack",
            "uip is --output json connections create slack",
            "uip is connections delete connection-id",
            "uip is resources run create connector operation",
            "uip is resources run update connector operation",
            "uip is resources run delete connector operation",
            "uip is resources run replace connector operation",
            "uip is connectors import ./connector",
            "uip is connectors --profile alpha publish ./connector",
        )
        allowed = (
            'echo "uip solution upload Eval.uipx"',
            "printf '%s' 'uip maestro bpmn debug Project'",
            "uip maestro bpmn registry list --output json",
            'uip --log-file "/tmp/foo bar.log" maestro bpmn registry list',
            "uip maestro bpmn registry get BPMN.Variables --output json",
            "uip maestro bpmn debug-instance variables-all instance-id",
            "uip maestro bpmn instance variables-all instance-id",
            "uip solution deploy list",
            "uip solution deploy status deployment-id",
            "uip solution packages list",
            "uip solution projects list Eval.uipx",
            "uip is connections list --all-folders --output json",
            "uip is connections ping connection-id --output json",
            "uip is resources describe connector operation --output json",
            "uip is resources list connector --output json",
            "uip is resources run get connector operation --output json",
        )
        for command in blocked:
            with self.subTest(blocked=command):
                self.assertRegex(command, pattern)
        for command in allowed:
            with self.subTest(allowed=command):
                self.assertNotRegex(command, pattern)

    def test_run_cli_caps_subprocess_to_absolute_live_deadline(self) -> None:
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="{}",
            stderr="",
        )
        with (
            patch.object(checker, "ACTIVE_CLI_DEADLINE", 103.5),
            patch.object(checker.time, "monotonic", return_value=100.0),
            patch.object(
                checker.subprocess,
                "run",
                return_value=completed,
            ) as run,
        ):
            checker.run_cli(["uip", "login", "status"], timeout=60)

        self.assertEqual(run.call_args.kwargs["timeout"], 3.5)

    def test_run_cli_refuses_new_work_after_absolute_deadline(self) -> None:
        with (
            patch.object(checker, "ACTIVE_CLI_DEADLINE", 99.0),
            patch.object(checker.time, "monotonic", return_value=100.0),
            patch.object(checker.subprocess, "run") as run,
            self.assertRaisesRegex(
                checker.CheckFailure,
                "operation deadline reached",
            ),
        ):
            checker.run_cli(["uip", "login", "status"], timeout=60)

        run.assert_not_called()

    def test_live_checker_keeps_outer_timeout_cleanup_reserve(self) -> None:
        task_text = Path(__file__).with_name(
            "customer_escalation_triage.yaml"
        ).read_text(encoding="utf-8")
        match = re.search(
            r"description: \"The exact submitted project executes hidden "
            r"scenarios in live Alpha.*?\n\s+timeout: (\d+)",
            task_text,
            flags=re.DOTALL,
        )
        self.assertIsNotNone(match)
        assert match is not None
        outer_timeout = int(match.group(1))
        self.assertGreaterEqual(
            outer_timeout - checker.LIVE_CLEANUP_DEADLINE_SECONDS,
            600,
        )
        self.assertGreater(
            checker.LIVE_CLEANUP_DEADLINE_SECONDS,
            checker.LIVE_RUN_DEADLINE_SECONDS,
        )

    def test_cleanup_signal_is_record_only_for_every_cleanup_stage(self) -> None:
        for signum in (checker.signal.SIGTERM, checker.signal.SIGINT):
            for interrupted_index in range(3):
                with self.subTest(
                    signum=signum,
                    interrupted_index=interrupted_index,
                ):
                    self.assert_cleanup_signal_is_record_only(
                        signum,
                        interrupted_index,
                    )

    def assert_cleanup_signal_is_record_only(
        self,
        signum: int,
        interrupted_index: int,
    ) -> None:
        signal_state = checker.CleanupSignalState()
        signal_state.begin_cleanup()
        calls: list[str] = []

        def cleanup_stage(index: int) -> list[str]:
            calls.append(f"{index}:start")
            if index == interrupted_index:
                signal_state.handle(signum, None)
            calls.append(f"{index}:complete")
            return []

        failures = checker.collect_cleanup_failures(
            tuple(
                (
                    f"stage {index}",
                    lambda index=index: cleanup_stage(index),
                )
                for index in range(3)
            )
        )

        self.assertEqual(
            calls,
            [
                "0:start",
                "0:complete",
                "1:start",
                "1:complete",
                "2:start",
                "2:complete",
            ],
        )
        self.assertEqual(failures, [])
        self.assertTrue(signal_state.termination_requested)

    def test_every_interrupted_cleanup_stage_is_retried_and_completed(
        self,
    ) -> None:
        for interrupted_index in range(3):
            with self.subTest(interrupted_index=interrupted_index):
                attempts = [0, 0, 0]
                completed: list[int] = []

                def cleanup_stage(index: int) -> list[str]:
                    attempts[index] += 1
                    if (
                        index == interrupted_index
                        and attempts[index] == 1
                    ):
                        raise KeyboardInterrupt("cancel interrupted")
                    completed.append(index)
                    return []

                failures = checker.collect_cleanup_failures(
                    tuple(
                        (
                            f"stage {index}",
                            lambda index=index: cleanup_stage(index),
                        )
                        for index in range(3)
                    )
                )

                self.assertEqual(failures, [])
                self.assertEqual(completed, [0, 1, 2])
                self.assertEqual(attempts[interrupted_index], 2)
                self.assertEqual(
                    sum(attempts),
                    4,
                    "only the interrupted stage should be retried",
                )

    def test_cleanup_interrupt_at_deadline_is_not_retried_but_later_stages_run(
        self,
    ) -> None:
        calls: list[str] = []

        def interrupted() -> list[str]:
            calls.append("interrupted")
            raise KeyboardInterrupt("deadline interrupt")

        def later_stage() -> list[str]:
            calls.append("later")
            return []

        with (
            patch.object(checker, "ACTIVE_CLI_DEADLINE", 99.0),
            patch.object(checker.time, "monotonic", return_value=100.0),
        ):
            failures = checker.collect_cleanup_failures(
                (
                    ("interrupted stage", interrupted),
                    ("later stage", later_stage),
                )
            )

        self.assertEqual(calls, ["interrupted", "later"])
        self.assertEqual(
            failures,
            [
                "interrupted stage cleanup raised unexpectedly: "
                "deadline interrupt"
            ],
        )

    def test_cleanup_signal_preserves_second_signal_safety(self) -> None:
        signal_state = checker.CleanupSignalState()

        with self.assertRaisesRegex(
            KeyboardInterrupt,
            "terminated during live Alpha evaluation",
        ):
            signal_state.handle(checker.signal.SIGTERM, None)

        signal_state.handle(checker.signal.SIGINT, None)
        signal_state.begin_cleanup()
        signal_state.handle(checker.signal.SIGTERM, None)

    def test_jira_create_requires_correlation_in_each_remote_field(self) -> None:
        environment = self.environment()
        correlation = "EVAL-correlation"
        fields = {
            "project": {"key": environment.jira_project_key},
            "issuetype": {"id": environment.jira_issue_type_id},
            "reporter": {
                "accountId": environment.jira_reporter_account_id
            },
            "summary": f"Escalation {correlation}",
            "description": "missing token",
        }
        with (
            patch.object(
                checker,
                "read_jira_issue_fields",
                return_value=fields,
            ),
            self.assertRaisesRegex(
                checker.CheckFailure, "'description'.*does not contain"
            ),
        ):
            checker.assert_jira_issue_contract(
                "CE-1",
                correlation,
                environment,
                require_summary=True,
            )

    def test_static_jira_summary_requires_all_business_tokens(self) -> None:
        invalid_summaries = {
            "customer": "=js:'Escalation ' + vars.CorrelationId",
            "escalation": "=js:'Customer ' + vars.CorrelationId",
            "correlation": "Customer escalation without runtime id",
        }
        key = ("uipath-atlassian-jira", "/curated_create_issue")
        for missing_term, summary in invalid_summaries.items():
            with (
                self.subTest(missing_term=missing_term),
                self.assertRaisesRegex(
                    checker.CheckFailure,
                    "summary must contain",
                ),
            ):
                checker.validate_connector_inputs(
                    self.jira_create_element(summary),
                    key,
                )

        checker.validate_connector_inputs(
            self.jira_create_element(
                "=js:'Customer escalation ' + vars.CorrelationId"
            ),
            key,
        )

    def test_remote_jira_summary_requires_customer_and_escalation(self) -> None:
        environment = self.environment()
        correlation = "EVAL-correlation"
        base_fields = {
            "project": {"key": environment.jira_project_key},
            "issuetype": {"id": environment.jira_issue_type_id},
            "reporter": {
                "accountId": environment.jira_reporter_account_id
            },
            "description": f"Handled {correlation}",
        }
        invalid_summaries = (
            f"Escalation {correlation}",
            f"Customer {correlation}",
        )
        for summary in invalid_summaries:
            with (
                self.subTest(summary=summary),
                patch.object(
                    checker,
                    "read_jira_issue_fields",
                    return_value={**base_fields, "summary": summary},
                ),
                self.assertRaisesRegex(
                    checker.CheckFailure,
                    "missing required terms",
                ),
            ):
                checker.assert_jira_issue_contract(
                    "CE-1",
                    correlation,
                    environment,
                    require_summary=True,
                )

    def test_jira_update_seed_does_not_precontain_correlation(self) -> None:
        case = checker.SCENARIOS[2]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {"id": "1001", "key": "CE-1"},
                }
            ),
            stderr="",
        )
        with patch.object(
            checker, "run_cli", return_value=completed
        ) as run:
            self.assertEqual(
                checker.create_seed_jira_issue(case, environment, lease),
                "CE-1",
            )

        command = run.call_args.args[0]
        body = json.loads(command[command.index("--body") + 1])
        self.assertNotIn(
            case.inputs["correlationId"],
            json.dumps(body),
        )
        self.assertIn(checker.RUN_NONCE, body["fields"]["summary"])
        self.assertFalse(lease.pending_jira_seeds)

    def test_failed_jira_seed_envelope_harvests_top_level_id(self) -> None:
        case = checker.SCENARIOS[2]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        failed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": "response arrived after an upstream error",
                    "Data": {
                        "id": "seed-id",
                        "key": "CE-100",
                        "fields": {
                            "project": {"id": "shared-project-id"}
                        },
                    },
                }
            ),
            stderr="",
        )
        summary = f"Live update seed {checker.RUN_NONCE} for {case.name}"
        searched = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "items": [
                            {
                                "id": "seed-id",
                                "key": "CE-100",
                                "fields": {"summary": summary},
                            }
                        ]
                    },
                }
            ),
            stderr="",
        )

        with (
            patch.object(
                checker,
                "run_cli",
                side_effect=[failed, searched],
            ),
            self.assertRaisesRegex(
                checker.CheckFailure,
                "cleanup recovery found",
            ),
        ):
            checker.create_seed_jira_issue(case, environment, lease)

        self.assertEqual(lease.jira_issue_ids, {"seed-id"})
        self.assertNotIn("shared-project-id", lease.jira_issue_ids)

    def test_timed_out_jira_seed_is_recovered_by_exact_summary(self) -> None:
        case = checker.SCENARIOS[2]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        timed_out = subprocess.TimeoutExpired(
            cmd=["uip", "is", "resources", "run", "create"],
            timeout=180,
        )
        summary = f"Live update seed {checker.RUN_NONCE} for {case.name}"
        searched = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "items": [
                            {
                                "id": "recovered-seed-id",
                                "key": "CE-101",
                                "fields": {"summary": summary},
                            },
                            {
                                "id": "unrelated-id",
                                "key": "CE-102",
                                "fields": {
                                    "summary": f"{summary} unrelated"
                                },
                            },
                        ]
                    },
                }
            ),
            stderr="",
        )
        empty_search = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"items": []}}
            ),
            stderr="",
        )

        with (
            patch.object(
                checker,
                "run_cli",
                side_effect=[timed_out, empty_search, searched],
            ),
            patch.object(checker.time, "sleep") as sleep,
            self.assertRaisesRegex(
                checker.CheckFailure,
                "cleanup recovery found 1 exact issue",
            ),
        ):
            checker.create_seed_jira_issue(case, environment, lease)

        sleep.assert_called_once_with(2)
        self.assertEqual(lease.jira_issue_ids, {"recovered-seed-id"})
        self.assertFalse(lease.pending_jira_seeds)

    def test_interrupted_jira_seed_remains_recoverable_in_final_cleanup(
        self,
    ) -> None:
        case = checker.SCENARIOS[2]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        empty_search = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"items": []}}
            ),
            stderr="",
        )

        with (
            patch.object(
                checker,
                "run_cli",
                side_effect=[
                    KeyboardInterrupt("terminated after remote create"),
                    empty_search,
                    empty_search,
                ],
            ),
            patch.object(checker.time, "sleep"),
            self.assertRaises(KeyboardInterrupt),
        ):
            checker.create_seed_jira_issue(case, environment, lease)

        summary = f"Live update seed {checker.RUN_NONCE} for {case.name}"
        self.assertEqual(lease.pending_jira_seeds, {summary: case.name})

        recovered = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "items": [
                            {
                                "id": "late-seed-id",
                                "key": "CE-103",
                                "fields": {"summary": summary},
                            }
                        ]
                    },
                }
            ),
            stderr="",
        )
        deleted = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"Deleted": True}}
            ),
            stderr="",
        )
        with patch.object(
            checker,
            "run_cli",
            side_effect=[recovered, deleted],
        ):
            self.assertEqual(lease.cleanup(), [])

        self.assertFalse(lease.pending_jira_seeds)
        self.assertFalse(lease.jira_issue_ids)

    def test_partial_jira_seed_key_is_leased_before_envelope_validation(
        self,
    ) -> None:
        case = checker.SCENARIOS[2]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        failed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Data": {"key": "CE-104"},
                    "Message": "malformed upstream response",
                }
            ),
            stderr="",
        )
        empty_search = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"items": []}}
            ),
            stderr="",
        )

        with (
            patch.object(
                checker,
                "run_cli",
                side_effect=[failed, *(empty_search for _ in range(5))],
            ),
            patch.object(checker.time, "sleep"),
            self.assertRaises(checker.CheckFailure),
        ):
            checker.create_seed_jira_issue(case, environment, lease)

        self.assertEqual(lease.jira_issue_ids, {"CE-104"})
        self.assertFalse(lease.pending_jira_seeds)

    def test_seed_recovery_leases_id_even_when_update_key_is_missing(
        self,
    ) -> None:
        case = checker.SCENARIOS[2]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        summary = f"Live update seed {checker.RUN_NONCE} for {case.name}"
        lease.begin_jira_seed(case.name, summary)
        recovered = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "items": [
                            {
                                "id": "id-without-key",
                                "fields": {"summary": summary},
                            }
                        ]
                    },
                }
            ),
            stderr="",
        )

        with patch.object(checker, "run_cli", return_value=recovered):
            self.assertEqual(
                checker.recover_seed_jira_issues(
                    case.name,
                    summary,
                    environment,
                    lease,
                    require_issue_key=False,
                ),
                (),
            )

        self.assertEqual(lease.jira_issue_ids, {"id-without-key"})
        self.assertFalse(lease.pending_jira_seeds)

    def test_ordered_drive_copies_verify_each_remote_file(self) -> None:
        case = checker.SCENARIOS[0]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        correlation = case.inputs["correlationId"]
        outputs = [
            {
                "Response": {
                    "id": "file-1",
                    "name": f"{correlation}-outage.png",
                }
            },
            {
                "Response": {
                    "id": "file-2",
                    "name": f"{correlation}-trace.zip",
                }
            },
        ]
        metadata = [
            {"id": environment.drive_source_file_ids[0], "md5Checksum": "abc"},
            {
                "id": environment.drive_source_file_ids[1],
                "md5Checksum": "xyz",
            },
            {
                "id": "file-1",
                "name": f"{correlation}-outage.png",
                "parents": [environment.drive_destination_folder_id],
                "md5Checksum": "abc",
            },
            {
                "id": "file-2",
                "name": f"{correlation}-trace.zip",
                "parents": [environment.drive_destination_folder_id],
                "md5Checksum": "xyz",
            },
        ]
        with patch.object(
            checker, "read_drive_file", side_effect=metadata
        ):
            checker.assert_ordered_drive_copies(
                case,
                case.attachment_iterations,
                outputs,
                environment,
                lease,
            )
        self.assertEqual(lease.drive_file_ids, {"file-1", "file-2"})

    def test_scenario_inputs_bind_distinct_drive_sources_per_item(self) -> None:
        case = checker.SCENARIOS[0]
        environment = self.environment()

        inputs = checker.scenario_inputs(case, environment)

        self.assertEqual(
            [
                attachment["driveFileId"]
                for attachment in inputs["attachments"]
            ],
            list(environment.drive_source_file_ids),
        )

    def test_drive_copies_reject_reusing_first_source_content(self) -> None:
        case = checker.SCENARIOS[0]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        correlation = case.inputs["correlationId"]
        outputs = [
            {
                "Response": {
                    "id": "file-1",
                    "name": f"{correlation}-outage.png",
                }
            },
            {
                "Response": {
                    "id": "file-2",
                    "name": f"{correlation}-trace.zip",
                }
            },
        ]
        metadata = [
            {"id": environment.drive_source_file_ids[0], "md5Checksum": "abc"},
            {
                "id": environment.drive_source_file_ids[1],
                "md5Checksum": "xyz",
            },
            {
                "id": "file-1",
                "name": f"{correlation}-outage.png",
                "parents": [environment.drive_destination_folder_id],
                "md5Checksum": "abc",
            },
            {
                "id": "file-2",
                "name": f"{correlation}-trace.zip",
                "parents": [environment.drive_destination_folder_id],
                "md5Checksum": "abc",
            },
        ]

        with (
            patch.object(
                checker,
                "read_drive_file",
                side_effect=metadata,
            ),
            self.assertRaisesRegex(
                checker.CheckFailure,
                "source content",
            ),
        ):
            checker.assert_ordered_drive_copies(
                case,
                case.attachment_iterations,
                outputs,
                environment,
                lease,
            )

    def test_drive_source_fixtures_must_have_distinct_checksums(self) -> None:
        environment = self.environment()
        with (
            patch.object(
                checker,
                "read_drive_file",
                return_value={"md5Checksum": "same"},
            ),
            self.assertRaisesRegex(
                checker.CheckFailure,
                "distinct MD5 checksums",
            ),
        ):
            checker.require_distinct_drive_source_fixtures(environment)

    def test_ordered_drive_copies_accept_reversed_runtime_records(self) -> None:
        case = checker.SCENARIOS[0]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        correlation = case.inputs["correlationId"]
        reversed_outputs = [
            {
                "Response": {
                    "id": "file-2",
                    "name": f"{correlation}-trace.zip",
                }
            },
            {
                "Response": {
                    "id": "file-1",
                    "name": f"{correlation}-outage.png",
                }
            },
        ]
        metadata = {
            environment.drive_source_file_ids[0]: {
                "id": environment.drive_source_file_ids[0],
                "md5Checksum": "abc",
            },
            environment.drive_source_file_ids[1]: {
                "id": environment.drive_source_file_ids[1],
                "md5Checksum": "xyz",
            },
            "file-1": {
                "id": "file-1",
                "name": f"{correlation}-outage.png",
                "parents": [environment.drive_destination_folder_id],
                "md5Checksum": "abc",
            },
            "file-2": {
                "id": "file-2",
                "name": f"{correlation}-trace.zip",
                "parents": [environment.drive_destination_folder_id],
                "md5Checksum": "xyz",
            },
        }
        with patch.object(
            checker,
            "read_drive_file",
            side_effect=lambda file_id, _environment: metadata[file_id],
        ):
            checker.assert_ordered_drive_copies(
                case,
                case.attachment_iterations,
                reversed_outputs,
                environment,
                lease,
            )
        self.assertEqual(lease.drive_file_ids, {"file-1", "file-2"})

    def test_attachment_marker_rejects_reversed_runtime_order(self) -> None:
        case = checker.SCENARIOS[0]
        variables_data = {
            "Variables": [
                {
                    "Globals": {
                        "MarkerCollection": list(
                            reversed(case.attachment_iterations)
                        )
                    }
                }
            ]
        }

        with self.assertRaisesRegex(
            checker.CheckFailure, "marker collection expected"
        ):
            checker.attachment_marker_order(
                case,
                variables_data,
                self.contract(),
            )

    def test_slack_send_requires_exact_live_message_content(self) -> None:
        case = checker.SCENARIOS[0]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        timestamp = "123.456"
        text = " | ".join(
            (
                case.inputs["correlationId"],
                case.outputs["route"],
                case.outputs["severity"],
            )
        )
        outputs = [
            {
                "Response": {
                    "channel": environment.slack_channel_id,
                    "ts": timestamp,
                    "message": {"text": text, "ts": timestamp},
                }
            }
        ]
        checker.assert_slack_send(case, outputs, environment, lease)
        self.assertEqual(
            lease.slack_messages,
            {(environment.slack_channel_id, timestamp)},
        )

        outputs[0]["Response"]["message"]["text"] = (
            case.inputs["correlationId"]
        )
        with self.assertRaisesRegex(
            checker.CheckFailure, "correlation, route, severity"
        ):
            checker.assert_slack_send(
                case,
                outputs,
                environment,
                checker.ConnectorSideEffectLease(environment),
            )

    def test_slack_wrong_channel_is_queued_for_actual_channel_cleanup(
        self,
    ) -> None:
        case = checker.SCENARIOS[0]
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        timestamp = "123.999"
        wrong_channel = "C-WRONG-CHANNEL"
        outputs = [
            {
                "Response": {
                    "channel": wrong_channel,
                    "ts": timestamp,
                    "message": {
                        "text": " ".join(
                            (
                                case.inputs["correlationId"],
                                case.outputs["route"],
                                case.outputs["severity"],
                            )
                        ),
                        "ts": timestamp,
                    },
                }
            }
        ]

        with self.assertRaisesRegex(
            checker.CheckFailure,
            "exact destination",
        ):
            checker.assert_slack_send(
                case,
                outputs,
                environment,
                lease,
            )

        self.assertEqual(
            lease.slack_messages,
            {(wrong_channel, timestamp)},
        )

    def test_connector_cleanup_retries_every_failed_delete(self) -> None:
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        lease.slack_messages.add((environment.slack_channel_id, "123.456"))
        lease.drive_file_ids.add("drive-file")
        lease.jira_issue_ids.add("jira-issue")
        attempts: dict[str, int] = {}

        def delete_once_then_succeed(
            arguments: list[str],
            **_kwargs: object,
        ) -> subprocess.CompletedProcess[str]:
            connector_key = arguments[5]
            attempts[connector_key] = attempts.get(connector_key, 0) + 1
            succeeded = attempts[connector_key] > 1
            return subprocess.CompletedProcess(
                args=arguments,
                returncode=0 if succeeded else 1,
                stdout=json.dumps(
                    {
                        "Result": "Success" if succeeded else "Failure",
                        "Data": {"Deleted": True} if succeeded else None,
                        "Message": "" if succeeded else "transient failure",
                    }
                ),
                stderr="",
            )

        with patch.object(
            checker,
            "run_cli",
            side_effect=delete_once_then_succeed,
        ) as run:
            self.assertEqual(lease.cleanup(), [])

        self.assertEqual(run.call_count, 6)
        self.assertFalse(lease.slack_messages)
        self.assertFalse(lease.drive_file_ids)
        self.assertFalse(lease.jira_issue_ids)

    def test_connector_cleanup_treats_not_found_as_already_absent(self) -> None:
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        lease.slack_messages.add((environment.slack_channel_id, "123.456"))
        lease.drive_file_ids.add("drive-file")
        lease.jira_issue_ids.add("jira-issue")
        absent = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": (
                        "Slack message 123.456, Drive file drive-file, and "
                        "Jira issue jira-issue not found (404)"
                    ),
                }
            ),
            stderr="",
        )

        with patch.object(checker, "run_cli", return_value=absent) as run:
            self.assertEqual(lease.cleanup(), [])

        self.assertEqual(run.call_count, 3)
        self.assertFalse(lease.slack_messages)
        self.assertFalse(lease.drive_file_ids)
        self.assertFalse(lease.jira_issue_ids)

    def test_connector_cleanup_does_not_confuse_connection_404_for_target(
        self,
    ) -> None:
        environment = self.environment()
        lease = checker.ConnectorSideEffectLease(environment)
        lease.drive_file_ids.add("drive-file")
        wrong_absence = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": "Connection not found (404)",
                }
            ),
            stderr="",
        )

        with patch.object(checker, "run_cli", return_value=wrong_absence):
            failures = lease.cleanup()

        self.assertEqual(len(failures), 1)
        self.assertEqual(lease.drive_file_ids, {"drive-file"})

    def test_absence_check_rejects_target_echoed_after_connection_404(
        self,
    ) -> None:
        wrong_absence = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": (
                        "404 OAuth connection not found; "
                        "request path /files/file-123"
                    ),
                }
            ),
            stderr="",
        )

        self.assertFalse(
            checker.delete_target_is_absent(
                wrong_absence,
                "drive file",
                "file-123",
            )
        )

    def test_variables_failure_recovers_connector_ids_for_cleanup(self) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        with tempfile.TemporaryDirectory() as directory:
            solution_lease = checker.AlphaSolutionLease(
                Path(directory) / "Eval.uipx"
            )
            failed = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=json.dumps(
                    {
                        "Result": "Failure",
                        "Message": "transient variables failure",
                    }
                ),
                stderr="",
            )
            recovered = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(
                    {
                        "Result": "Success",
                        "Data": {
                            "SolutionId": (
                                "99999999-9999-9999-9999-999999999999"
                            ),
                            "Variables": [
                                {
                                    "Elements": [
                                        {
                                            "ElementId": "JiraCreate",
                                            "Outputs": {
                                                "response": {
                                                    "id": "jira-issue"
                                                }
                                            },
                                        },
                                        {
                                            "ElementId": "DriveCopy",
                                            "Outputs": {
                                                "response": {
                                                    "id": "drive-file"
                                                }
                                            },
                                        },
                                        {
                                            "ElementId": "SlackSend",
                                            "Outputs": {
                                                "response": {
                                                    "channel": (
                                                        environment
                                                        .slack_channel_id
                                                    ),
                                                    "ts": "123.456",
                                                }
                                            },
                                        },
                                    ]
                                }
                            ]
                        },
                    }
                ),
                stderr="",
            )
            with (
                patch.object(
                    checker,
                    "run_cli",
                    side_effect=[failed, recovered],
                ) as run,
                self.assertRaisesRegex(
                    checker.CheckFailure,
                    "transient variables failure",
                ),
            ):
                checker.variables_all_with_cleanup_recovery(
                    "instance-id",
                    "scenario",
                    self.contract(),
                    environment,
                    solution_lease,
                    side_effects,
                )

        self.assertEqual(run.call_count, 2)
        self.assertEqual(side_effects.jira_issue_ids, {"jira-issue"})
        self.assertEqual(side_effects.drive_file_ids, {"drive-file"})
        self.assertEqual(
            side_effects.slack_messages,
            {(environment.slack_channel_id, "123.456")},
        )
        self.assertFalse(solution_lease.solution_ids)

    def test_cleanup_harvest_never_queues_protected_drive_ids(self) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        protected_ids = (
            *environment.drive_source_file_ids,
            environment.drive_destination_folder_id,
        )
        output_ids = (*protected_ids, "generated-copy-id")
        variables_data = {
            "Variables": [
                {
                    "Elements": [
                        {
                            "ElementId": "DriveCopy",
                            "Outputs": {"response": {"id": file_id}},
                        }
                        for file_id in output_ids
                    ]
                }
            ]
        }

        checker.capture_connector_outputs_for_cleanup(
            variables_data,
            self.contract(),
            environment,
            side_effects,
        )

        self.assertEqual(
            side_effects.drive_file_ids,
            {"generated-copy-id"},
        )

    def test_logged_instance_id_trusts_only_exact_envelope_field(
        self,
    ) -> None:
        payload = json.dumps(
            {
                "Result": "Success",
                "Data": {
                    "InstanceId": "instance-owned",
                    "Diagnostic": {
                        "InstanceId": "instance-shared-decoy"
                    },
                },
            }
        )
        self.assertEqual(
            checker.logged_instance_id(payload),
            "instance-owned",
        )

    def test_logged_instance_id_uses_trusted_failure_message_fallback(
        self,
    ) -> None:
        payload = json.dumps(
            {
                "Result": "Failure",
                "Data": None,
                "Message": "Created InstanceId: instance-from-message",
                "Diagnostic": {
                    "InstanceId": "instance-shared-decoy"
                },
            }
        )
        self.assertEqual(
            checker.logged_instance_id(payload),
            "instance-from-message",
        )

    def test_logged_instance_id_rejects_conflicting_exact_ids(self) -> None:
        first = json.dumps(
            {
                "Result": "Success",
                "Data": {"InstanceId": "instance-one"},
            }
        )
        second = json.dumps(
            {
                "Result": "Success",
                "Data": {"InstanceId": "instance-two"},
            }
        )
        self.assertIsNone(checker.logged_instance_id(first, second))

    def test_debug_cancel_absence_must_be_tied_to_exact_instance(
        self,
    ) -> None:
        wrong_absence = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": (
                        "404 tenant endpoint not found; request path "
                        "/debug-instances/instance-owned/cancel"
                    ),
                }
            ),
            stderr="",
        )
        exact_terminal = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Data": {
                        "InstanceId": "instance-owned",
                        "Status": "Completed",
                    },
                }
            ),
            stderr="",
        )

        self.assertFalse(
            checker.debug_instance_is_terminal_or_absent(
                wrong_absence,
                "instance-owned",
            )
        )
        self.assertTrue(
            checker.debug_instance_is_terminal_or_absent(
                exact_terminal,
                "instance-owned",
            )
        )

    def test_precreate_journal_id_absence_skips_variable_harvest(
        self,
    ) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        with tempfile.TemporaryDirectory() as directory:
            solution_lease = checker.AlphaSolutionLease(
                Path(directory) / "Eval.uipx"
            )
            with (
                patch.object(
                    checker,
                    "cancel_debug_instance_for_recovery",
                    return_value=([], True),
                ),
                patch.object(
                    checker,
                    "variables_all_with_cleanup_recovery",
                ) as variables,
            ):
                self.assertEqual(
                    checker.best_effort_capture_instance_outputs(
                        "allocated-before-create",
                        "scenario",
                        self.contract(),
                        environment,
                        solution_lease,
                        side_effects,
                    ),
                    [],
                )

        variables.assert_not_called()

    def test_instance_journal_reads_only_top_level_id(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "instance.json"
            journal.write_text(
                json.dumps(
                    {
                        "InstanceId": "instance-owned",
                        "Diagnostic": {
                            "InstanceId": "instance-shared-decoy"
                        },
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                checker.read_instance_id_journal(journal),
                "instance-owned",
            )

    def test_live_run_lease_recovers_exact_journal_before_search(
        self,
    ) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = root / "instance.json"
            journal.write_text(
                json.dumps({"InstanceId": "instance-owned"}),
                encoding="utf-8",
            )
            solution_lease = checker.AlphaSolutionLease(root / "Eval.uipx")
            lease = checker.LiveRunLease(
                contract=self.contract(),
                environment=environment,
                solution_lease=solution_lease,
                side_effects=side_effects,
            )
            lease.begin("scenario", "correlation", journal)
            with (
                patch.object(
                    checker,
                    "best_effort_capture_instance_outputs",
                    return_value=[],
                ) as recover_instance,
            ):
                self.assertEqual(lease.cleanup(), [])

        recover_instance.assert_called_once()
        self.assertEqual(
            recover_instance.call_args.args[0],
            "instance-owned",
        )
        self.assertFalse(lease.pending_correlations)
        self.assertFalse(lease.active_instances)

    def test_missing_journal_never_attempts_unreliable_connector_search(
        self,
    ) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            missing_journal = root / "instance.json"
            lease = checker.LiveRunLease(
                contract=self.contract(),
                environment=environment,
                solution_lease=checker.AlphaSolutionLease(
                    root / "Eval.uipx"
                ),
                side_effects=side_effects,
            )
            lease.begin("scenario", "correlation", missing_journal)
            with patch.object(checker, "run_cli") as run:
                self.assertEqual(lease.cleanup(), [])

        run.assert_not_called()
        self.assertFalse(lease.pending_correlations)

    def test_successful_debug_registers_the_durable_instance_journal(
        self,
    ) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "InstanceId": "instance-owned",
                        "FinalStatus": "Completed",
                    },
                }
            ),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = root / "instance.json"
            journal.write_text(
                json.dumps({"InstanceId": "instance-owned"}),
                encoding="utf-8",
            )
            solution_lease = checker.AlphaSolutionLease(root / "Eval.uipx")
            live_runs = checker.LiveRunLease(
                contract=self.contract(),
                environment=environment,
                solution_lease=solution_lease,
                side_effects=side_effects,
            )
            live_runs.begin("scenario", "correlation", journal)
            with patch.object(
                checker,
                "run_cli",
                return_value=completed,
            ):
                result = checker.run_debug_with_cleanup_recovery(
                    ["uip", "maestro", "bpmn", "debug", "Project"],
                    log_file=root / "debug.log",
                    case_name="scenario",
                    contract=self.contract(),
                    environment=environment,
                    solution_lease=solution_lease,
                    side_effects=side_effects,
                    live_run_lease=live_runs,
                    correlation="correlation",
                    instance_id_file=journal,
                )

        self.assertEqual(result[-1], "instance-owned")
        self.assertEqual(
            live_runs.active_instances,
            {"instance-owned": ("scenario", "correlation")},
        )

    def test_debug_timeout_recovers_from_partial_instance_id(self) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        timed_out = subprocess.TimeoutExpired(
            cmd=["uip", "maestro", "bpmn", "debug"],
            timeout=480,
            output=b'partial output InstanceId: "instance-timeout"',
            stderr=b"",
        )
        recovered = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {
                    "Result": "Success",
                    "Data": {
                        "Variables": [
                            {
                                "Elements": [
                                    {
                                        "ElementId": "DriveCopy",
                                        "Outputs": {
                                            "response": {
                                                "id": "drive-timeout"
                                            }
                                        },
                                    }
                                ]
                            }
                        ]
                    },
                }
            ),
            stderr="",
        )
        deleted = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"Deleted": True}}
            ),
            stderr="",
        )
        canceled = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"Canceled": True}}
            ),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            solution_lease = checker.AlphaSolutionLease(root / "Eval.uipx")
            contract = self.contract()
            live_run_lease = checker.LiveRunLease(
                contract=contract,
                environment=environment,
                solution_lease=solution_lease,
                side_effects=side_effects,
            )
            with (
                patch.object(
                    checker,
                    "run_cli",
                    side_effect=[timed_out, canceled, recovered, deleted],
                ) as run,
                self.assertRaises(subprocess.TimeoutExpired),
            ):
                checker.run_debug_with_cleanup_recovery(
                    ["uip", "maestro", "bpmn", "debug", "Project"],
                    log_file=root / "debug.log",
                    case_name="scenario",
                    contract=contract,
                    environment=environment,
                    solution_lease=solution_lease,
                    side_effects=side_effects,
                    live_run_lease=live_run_lease,
                    correlation="correlation-timeout",
                    instance_id_file=root / "instance.json",
                )

        self.assertEqual(run.call_count, 4)
        self.assertIn(
            "cancel",
            run.call_args_list[1].args[0],
        )
        self.assertIn(
            "drive-timeout",
            json.dumps(run.call_args_list[-1].args[0]),
        )
        self.assertFalse(side_effects.drive_file_ids)

    def test_malformed_debug_uses_log_and_harvests_failure_data(self) -> None:
        environment = self.environment()
        side_effects = checker.ConnectorSideEffectLease(environment)
        malformed = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout="not a JSON response",
            stderr="",
        )
        failed_with_data = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": "instance query was incomplete",
                    "Data": {
                        "Variables": [
                            {
                                "Elements": [
                                    {
                                        "ElementId": "JiraCreate",
                                        "Outputs": {
                                            "response": {"id": "jira-log"}
                                        },
                                    },
                                        {
                                            "ElementId": "SlackSend",
                                            "Outputs": {
                                                "response": {
                                                    "channel": (
                                                        environment
                                                        .slack_channel_id
                                                    ),
                                                    "ts": "123.789",
                                                }
                                            },
                                        },
                                ]
                            }
                        ]
                    },
                }
            ),
            stderr="",
        )
        failed_retry = subprocess.CompletedProcess(
            args=[],
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": "still unavailable",
                }
            ),
            stderr="",
        )
        deleted = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"Deleted": True}}
            ),
            stderr="",
        )
        canceled = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(
                {"Result": "Success", "Data": {"Canceled": True}}
            ),
            stderr="",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            log_file = root / "debug.log"
            log_file.write_text(
                "runtime started; Instance ID: instance-from-log",
                encoding="utf-8",
            )
            solution_lease = checker.AlphaSolutionLease(root / "Eval.uipx")
            contract = self.contract()
            live_run_lease = checker.LiveRunLease(
                contract=contract,
                environment=environment,
                solution_lease=solution_lease,
                side_effects=side_effects,
            )
            with (
                patch.object(
                    checker,
                    "run_cli",
                    side_effect=[
                        malformed,
                        canceled,
                        failed_with_data,
                        failed_retry,
                        deleted,
                        deleted,
                    ],
                ) as run,
                self.assertRaisesRegex(
                    checker.CheckFailure,
                    "invalid JSON",
                ),
            ):
                checker.run_debug_with_cleanup_recovery(
                    ["uip", "maestro", "bpmn", "debug", "Project"],
                    log_file=log_file,
                    case_name="scenario",
                    contract=contract,
                    environment=environment,
                    solution_lease=solution_lease,
                    side_effects=side_effects,
                    live_run_lease=live_run_lease,
                    correlation="correlation-malformed",
                    instance_id_file=root / "instance.json",
                )

        self.assertEqual(run.call_count, 6)
        self.assertIn("cancel", run.call_args_list[1].args[0])
        cleanup_commands = json.dumps(
            [call.args[0] for call in run.call_args_list[4:]]
        )
        self.assertIn("jira-log", cleanup_commands)
        self.assertIn("123.789", cleanup_commands)
        self.assertFalse(side_effects.jira_issue_ids)
        self.assertFalse(side_effects.slack_messages)

    def test_solution_lease_deletes_only_the_manifest_id(self) -> None:
        solution_id = "22222222-2222-2222-2222-222222222222"
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "Eval.uipx"
            manifest.write_text(
                json.dumps({"SolutionId": solution_id}),
                encoding="utf-8",
            )
            lease = checker.AlphaSolutionLease(manifest)
            completed = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(
                    {"Result": "Success", "Data": {"Deleted": True}}
                ),
                stderr="",
            )
            with patch.object(checker, "run_cli", return_value=completed) as run:
                self.assertEqual(lease.cleanup(), [])

            deleted = {
                call.args[0][3]
                for call in run.call_args_list
            }
            self.assertEqual(deleted, {solution_id})
            self.assertEqual(lease.cleanup(), [])

    def test_solution_lease_retries_a_failed_delete(self) -> None:
        solution_id = "11111111-1111-1111-1111-111111111111"
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "Eval.uipx"
            manifest.write_text(
                json.dumps({"SolutionId": solution_id}),
                encoding="utf-8",
            )
            lease = checker.AlphaSolutionLease(manifest)
            failed = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=json.dumps(
                    {
                        "Result": "Failure",
                        "Message": "transient delete failure",
                    }
                ),
                stderr="",
            )
            succeeded = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(
                    {"Result": "Success", "Data": {"Deleted": True}}
                ),
                stderr="",
            )
            with patch.object(
                checker,
                "run_cli",
                side_effect=[failed, succeeded],
            ) as run:
                self.assertEqual(lease.cleanup(), [])
                self.assertEqual(run.call_count, 2)
                self.assertTrue(lease.cleaned)
                self.assertEqual(
                    lease.removed_solution_ids,
                    {solution_id},
                )
                self.assertEqual(lease.cleanup(), [])
                self.assertEqual(run.call_count, 2)

    def test_solution_lease_accepts_id_that_never_reached_alpha(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "Eval.uipx"
            manifest.write_text(
                json.dumps(
                    {
                        "SolutionId": "11111111-1111-1111-1111-111111111111"
                    }
                ),
                encoding="utf-8",
            )
            lease = checker.AlphaSolutionLease(manifest)
            completed = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=json.dumps(
                    {
                        "Result": "Failure",
                        "Message": (
                            "Solution "
                            "11111111-1111-1111-1111-111111111111 "
                            "not found (404)"
                        ),
                    }
                ),
                stderr="",
            )

            with patch.object(checker, "run_cli", return_value=completed):
                self.assertEqual(lease.cleanup(), [])


if __name__ == "__main__":
    unittest.main()
