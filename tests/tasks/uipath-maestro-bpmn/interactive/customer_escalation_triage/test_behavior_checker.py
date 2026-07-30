#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("check_customer_escalation_behavior.py")
SPEC = importlib.util.spec_from_file_location("behavior_checker", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)


class BehaviorCheckerTests(unittest.TestCase):
    def test_hidden_live_matrix_covers_all_required_outcome_families(self) -> None:
        self.assertEqual(len(checker.SCENARIOS), 9)
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
            2,
        )
        self.assertEqual(
            {
                case.outputs["severity"]
                for case in checker.SCENARIOS
                if case.uses_error_boundary
            },
            {"Sev1", "Sev2"},
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

    def test_solution_lease_deletes_every_captured_id(self) -> None:
        first = "11111111-1111-1111-1111-111111111111"
        second = "22222222-2222-2222-2222-222222222222"
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "Eval.uipx"
            manifest.write_text(
                json.dumps({"SolutionId": second}),
                encoding="utf-8",
            )
            lease = checker.AlphaSolutionLease(manifest)
            lease.capture_payload({"Data": {"SolutionId": first}})
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
            self.assertEqual(deleted, {first, second})
            self.assertEqual(lease.cleanup(), [])

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
                        "Message": "Delete failed (404): Not Found",
                    }
                ),
                stderr="",
            )

            with patch.object(checker, "run_cli", return_value=completed):
                self.assertEqual(lease.cleanup(), [])


if __name__ == "__main__":
    unittest.main()
