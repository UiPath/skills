#!/usr/bin/env python3
"""`drive_case._is_transient`: which CLI refusals get another attempt.

A route that ends on the tenant carries no verdict about the build, and across nine
runs of the seven-route SDD eleven route verdicts were lost that way. A refusal that
names its reason must still fail on the first attempt: retrying a real one turns a
plan defect into a pass.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "drive_case_under_test", Path(__file__).parent / "drive_case.py"
)
drive_case = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(drive_case)


class TransientMarkerTests(unittest.TestCase):
    def assert_retries(self, detail: str):
        self.assertTrue(drive_case._is_transient(detail), detail)

    def assert_fails_at_once(self, detail: str):
        self.assertFalse(drive_case._is_transient(detail), detail)

    def test_gateway_timeout_retries(self):
        self.assert_retries("Error listing tasks | unknown_error | Gateway Timeout")

    def test_service_unavailable_retries(self):
        self.assert_retries("Error listing tasks | unknown_error | Service Unavailable")

    def test_a_reasonless_listing_failure_retries(self):
        """`unknown_error` plus a content-free message is a service that could not
        answer. It ended a route on 34632357797 after the buyer stage was selected."""
        self.assert_retries("Error listing tasks | unknown_error | An error occurred")

    def test_an_expired_session_retries(self):
        """A 403 naming `authentication_required` is the tenant's session, never the
        plan. It cost four route verdicts across 34558832471 and 34613296008."""
        self.assert_retries(
            "Error getting instance | Forbidden | authentication_required | Status: 403 Forbidden"
        )
        self.assert_retries(
            "Error getting variables | Forbidden | authentication_required | Status: 403"
        )

    def test_a_named_refusal_fails_at_once(self):
        self.assert_fails_at_once(
            "Error listing tasks | invalid_argument | Folder does not exist or the user "
            "does not have access to the folder."
        )

    def test_a_plan_defect_fails_at_once(self):
        self.assert_fails_at_once(
            "Validation failed | invalid_argument | the caseplan is not valid"
        )

    def test_a_missing_resource_fails_at_once(self):
        self.assert_fails_at_once(
            "Error getting instance | not_found | No instance exists with that id"
        )


class PlatformIncidentTests(unittest.TestCase):
    """Which case incidents mean the route judges nothing.

    Across 17 runs the case recorded 27 incidents. Twenty-five name something the build
    wrote: empty inputs, an expression that dereferenced undefined, an Integration
    Services 400, a catalog the folder does not hold. Two do not.
    """

    @staticmethod
    def _incident(message: str) -> dict:
        return {"ElementId": "t1", "Code": 170002, "Message": message}

    def test_a_service_fault_alone_judges_nothing(self):
        for message in ("HTTP Request Failed", "LLM model not available"):
            self.assertTrue(
                drive_case.incidents_are_all_platform([self._incident(message)]), message
            )

    def test_a_plan_defect_still_counts(self):
        for message in (
            "Input validation failed",
            "Error evaluating data expression: Worker operation failed",
            "Request to Integration Services failed with status code '400'",
            "No task catalog exists with name phase-escalation",
        ):
            self.assertFalse(
                drive_case.incidents_are_all_platform([self._incident(message)]), message
            )

    def test_one_plan_defect_among_service_faults_still_counts(self):
        self.assertFalse(drive_case.incidents_are_all_platform([
            self._incident("HTTP Request Failed"),
            self._incident("Input validation failed"),
        ]))

    def test_no_incident_is_not_a_service_fault(self):
        """A case that faulted with nothing recorded still has to fail on its own terms."""
        self.assertFalse(drive_case.incidents_are_all_platform([]))


class AlreadyCompletedTests(unittest.TestCase):
    """A write that landed and then answered with a transient marker.

    `envelope_retrying` sends a refused write again, and Orchestrator refuses the second
    attempt of a completion with `This Action is already completed by the same user`. Run
    34672482504's compliance-reject lost its first gate there.
    """

    def test_the_marker_is_recognised_whatever_the_casing(self):
        for detail in (
            "Error completing task '101524657' | This Action is already completed by the same user",
            "error completing task | this action is ALREADY COMPLETED BY THE SAME USER",
        ):
            self.assertIn(drive_case._ALREADY_COMPLETED, detail.lower(), detail)

    def test_a_real_completion_refusal_is_not_it(self):
        for detail in (
            "Error completing task | This action is no longer assigned to you",
            "Error completing task | The task is not in a state that allows completion",
        ):
            self.assertNotIn(drive_case._ALREADY_COMPLETED, detail.lower(), detail)


if __name__ == "__main__":
    unittest.main()
