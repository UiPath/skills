#!/usr/bin/env python3
"""Offline tests for check_vat.py's main flow, with the workflow runner and VIES stubbed
out: correct and gamed workflows, INFRA paths, the retry, and usage errors.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import io
import json
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vat_fakes import REGISTERED, Runner, check_vat, prefixed, sandbox, workflow_with_inputs  # noqa: E402


class MainTests(unittest.TestCase):
    def run_main(self, workflow, answer, vat, expect, truths=((None, None),)):
        """Returns (exit code or SystemExit message, stdout, stderr, runner, vies mock)."""
        text = workflow if isinstance(workflow, str) else json.dumps(workflow)
        if truths == ((None, None),):
            truths = [(vat in REGISTERED, None)] * 2
        runner = Runner(answer)
        vies = mock.Mock(side_effect=list(truths))
        out, err = io.StringIO(), io.StringIO()
        with sandbox(text), mock.patch.object(check_vat, "vies_valid", vies), \
                mock.patch.object(check_vat, "run_row", autospec=True, side_effect=runner), \
                mock.patch.object(check_vat.time, "sleep"), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                result = check_vat.main(["--vat", vat, "--expect", expect])
            except SystemExit as exc:
                result = exc.code
        return result, out.getvalue(), err.getvalue(), runner, vies

    def test_correct_workflow_passes_both_checks(self):
        workflow = workflow_with_inputs("vatNumber")
        result, out, *_ = self.run_main(workflow, prefixed, "RO34737997", "true")
        self.assertEqual(result, 0)
        self.assertIn(os.path.join("VatCheck", "Workflow.json"), out)
        self.assertEqual(self.run_main(workflow, prefixed, "RO12345674", "false")[0], 0)

    def test_workflow_taking_the_bare_number_passes(self):
        def bare(inputs, _call):
            return {"isValid": "RO" + next(iter(inputs.values())) in REGISTERED}
        workflow = workflow_with_inputs("vatNumber")
        self.assertEqual(self.run_main(workflow, bare, "RO34737997", "true")[0], 0)
        self.assertEqual(self.run_main(workflow, bare, "RO12345674", "false")[0], 0)

    def test_two_input_workflow_with_unrecognised_names_passes(self):
        def split(inputs, _call):
            if inputs.get("cc") != "RO" or "id" not in inputs:
                return {"error": "INVALID_INPUT"}
            return {"isValid": "RO" + inputs["id"] in REGISTERED}
        workflow = workflow_with_inputs("cc", "id")
        self.assertEqual(self.run_main(workflow, split, "RO34737997", "true")[0], 0)
        self.assertEqual(self.run_main(workflow, split, "RO12345674", "false")[0], 0)

    def test_two_input_workflow_with_recognisable_names_passes(self):
        def split(inputs, _call):
            if inputs.get("memberState") != "RO" or "taxId" not in inputs:
                return {"error": "INVALID_INPUT"}
            return {"isValid": "RO" + inputs["taxId"] in REGISTERED}
        workflow = workflow_with_inputs("memberState", "taxId")
        self.assertEqual(self.run_main(workflow, split, "RO34737997", "true")[0], 0)
        self.assertEqual(self.run_main(workflow, split, "RO12345674", "false")[0], 0)

    def test_hardcoded_true_fails_the_negative_check_without_a_retry(self):
        result, _, _, runner, vies = self.run_main(workflow_with_inputs("vatNumber"),
                                                    lambda *_: {"isValid": True}, "RO12345674", "false")
        self.assertIn("FAIL", str(result))
        self.assertEqual(vies.call_count, 1)
        self.assertEqual(len(runner.calls), 2)

    def test_wrong_output_key_fails(self):
        result, *_ = self.run_main(workflow_with_inputs("vatNumber"), lambda *_: {"valid": True},
                                   "RO34737997", "true")
        self.assertIn("no input contract returned a boolean isValid", str(result))

    def test_workflow_without_inputs_or_unreadable_fails(self):
        self.assertIn("declares no workflow inputs",
                      str(self.run_main(workflow_with_inputs(), prefixed, "RO34737997", "true")[0]))
        self.assertIn("not readable JSON", str(self.run_main("{not json", prefixed, "RO34737997", "true")[0]))

    def test_vies_without_an_answer_is_infrastructure_and_runs_nothing(self):
        result, _, err, runner, _ = self.run_main(workflow_with_inputs("vatNumber"), prefixed,
                                                  "RO34737997", "true", truths=[(None, "MS_UNAVAILABLE")])
        self.assertEqual(result, check_vat.INFRA_EXIT)
        self.assertIn("INFRA", err)
        self.assertEqual(runner.calls, [])

    def test_fixture_drift_is_infrastructure(self):
        result, _, err, *_ = self.run_main(workflow_with_inputs("vatNumber"), prefixed,
                                           "RO34737997", "true", truths=[(False, None)])
        self.assertEqual(result, check_vat.INFRA_EXIT)
        self.assertIn("update the fixture", err)

    def test_transient_refusal_is_retried_and_merged(self):
        def refused_then_fine(inputs, call):
            return {"isValid": False} if call <= 2 else prefixed(inputs, call)
        result, _, _, runner, vies = self.run_main(workflow_with_inputs("vatNumber"), refused_then_fine,
                                                    "RO34737997", "true")
        self.assertEqual(result, 0)
        self.assertEqual(vies.call_count, 2)
        self.assertEqual(len(runner.calls), 4)

    def test_vies_failing_mid_run_is_infrastructure(self):
        result, *_ = self.run_main(workflow_with_inputs("vatNumber"), lambda *_: {"isValid": False},
                                   "RO34737997", "true", truths=[(True, None), (None, "MS_MAX_CONCURRENT_REQ")])
        self.assertEqual(result, check_vat.INFRA_EXIT)

    def test_a_workflow_that_never_answers_true_fails_after_the_retry(self):
        result, _, _, runner, vies = self.run_main(workflow_with_inputs("vatNumber"), lambda *_: {"isValid": False},
                                                    "RO34737997", "true")
        self.assertIn("FAIL", str(result))
        self.assertEqual(vies.call_count, 2)
        self.assertEqual(len(runner.calls), 4)

    def test_no_retry_when_the_budget_is_nearly_used_up(self):
        runner = Runner(lambda *_: {"isValid": False})
        vies = mock.Mock(return_value=(True, None))
        with mock.patch.object(check_vat, "vies_valid", vies), mock.patch.object(check_vat, "run_row", autospec=True, side_effect=runner):
            passed, _ = check_vat.grade(Path("Workflow.json"), [{"v": "RO34737997"}], "RO", "34737997", True,
                                        time.monotonic() + 15)
        self.assertFalse(passed)
        self.assertEqual(vies.call_count, 1)
        self.assertEqual(len(runner.calls), 1)

    def test_malformed_vat_argument_is_a_usage_error(self):
        result, *_ = self.run_main(workflow_with_inputs("vatNumber"), prefixed, "34737997", "true")
        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
