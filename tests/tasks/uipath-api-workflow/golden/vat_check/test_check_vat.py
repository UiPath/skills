#!/usr/bin/env python3
"""Offline tests for check_vat.py: input-contract discovery, the pass/fail rule, VIES's own
answer, the time budget, and the main flow with the workflow runner and VIES stubbed out.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import http.client
import io
import json
import os
import sys
import tempfile
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_vat  # noqa: E402

REGISTERED = {"RO34737997"}


def workflow_with_inputs(*names):
    properties = {name: {"type": "string"} for name in names}
    return {"input": {"schema": {"format": "json", "document": {"type": "object", "properties": properties}}}}


@contextlib.contextmanager
def sandbox(workflow_text):
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "VatCheck"
        project.mkdir()
        (project / "Workflow.json").write_text(workflow_text)
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            yield
        finally:
            os.chdir(cwd)


class Runner:
    """Stand-in for eval_scoring.run_row; `answer(inputs, call_number)` returns the raw output."""

    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def __call__(self, _workflow_path, inputs, timeout=90):
        self.calls.append(inputs)
        return True, self.answer(inputs, len(self.calls)), None


def prefixed(inputs, _call):
    """A correct workflow with one input that takes the prefixed VAT id."""
    return {"isValid": next(iter(inputs.values())) in REGISTERED}


class InputContractTests(unittest.TestCase):
    def candidates(self, *names):
        return check_vat.input_candidates(list(names), "RO", "34737997")

    def test_single_input_gets_the_prefixed_then_the_bare_number(self):
        self.assertEqual(self.candidates("vatNumber"), [{"vatNumber": "RO34737997"}, {"vatNumber": "34737997"}])

    def test_country_and_number_inputs_are_recognised_by_name(self):
        self.assertEqual(self.candidates("countryCode", "vatNumber"),
                         [{"vatNumber": "RO34737997"}, {"vatNumber": "34737997"},
                          {"countryCode": "RO", "vatNumber": "34737997"}])
        self.assertIn({"memberState": "RO", "taxId": "34737997"}, self.candidates("memberState", "taxId"))

    def test_two_unnamed_inputs_get_the_split_in_both_orders(self):
        candidates = self.candidates("a", "b")
        self.assertIn({"a": "RO", "b": "34737997"}, candidates)
        self.assertIn({"a": "34737997", "b": "RO"}, candidates)
        self.assertIn({"a": "RO34737997"}, candidates)

    def test_swagger_requester_and_trader_fields_are_left_out(self):
        names = ["countryCode", "vatNumber", "requesterMemberStateCode", "requesterNumber", "traderName"]
        self.assertEqual(self.candidates(*names), self.candidates("countryCode", "vatNumber"))

    def test_extra_input_is_left_out_before_any_split_is_tried(self):
        self.assertEqual(self.candidates("vatNumber", "timeoutSeconds")[:2],
                         [{"vatNumber": "RO34737997"}, {"vatNumber": "34737997"}])

    def test_unrecognised_country_input_still_gets_the_split(self):
        self.assertIn({"cc": "RO", "vatNumber": "34737997"}, self.candidates("cc", "vatNumber"))

    def test_a_lone_country_looking_input_still_gets_the_vat_id(self):
        self.assertIn({"vatCountryNumber": "RO34737997"}, self.candidates("vatCountryNumber"))

    def test_candidates_are_capped_and_empty_without_inputs(self):
        self.assertLessEqual(len(self.candidates(*[f"in{i}" for i in range(30)])), check_vat.MAX_CANDIDATES)
        self.assertEqual(self.candidates(), [])

    def test_declared_inputs_reads_input_schema_properties(self):
        self.assertEqual(check_vat.declared_inputs(workflow_with_inputs("countryCode", "vatNumber")),
                         ["countryCode", "vatNumber"])
        self.assertEqual(check_vat.declared_inputs({}), [])
        self.assertEqual(check_vat.declared_inputs({"input": {"schema": {"document": {"properties": []}}}}), [])
        for malformed in ({"input": []}, {"input": {"schema": "x"}}, {"input": {"schema": {"document": 3}}}):
            with self.subTest(malformed=malformed):
                self.assertEqual(check_vat.declared_inputs(malformed), [])
        self.assertEqual(len(check_vat.declared_inputs(workflow_with_inputs(*[f"in{i}" for i in range(50)]))), 20)


class OutputAndVerdictTests(unittest.TestCase):
    def test_only_a_boolean_isValid_counts(self):
        self.assertIs(check_vat.is_valid_of({"isValid": True}), True)
        self.assertIs(check_vat.is_valid_of({"isValid": False}), False)
        for raw in ({"isValid": "true"}, {"IsValid": True}, {"valid": True}, True, None, [True]):
            with self.subTest(raw=raw):
                self.assertIsNone(check_vat.is_valid_of(raw))

    def test_expect_true_needs_some_contract_to_answer_true(self):
        self.assertTrue(check_vat.verdict([({"v": 1}, False, "x"), ({"v": 2}, True, "y")], True)[0])
        self.assertFalse(check_vat.verdict([({"v": 1}, False, "x"), ({"v": 2}, False, "y")], True)[0])

    def test_expect_false_needs_a_false_and_no_true(self):
        self.assertTrue(check_vat.verdict([({"v": 1}, False, "x"), ({"v": 2}, None, "err")], False)[0])
        self.assertFalse(check_vat.verdict([({"v": 1}, False, "x"), ({"v": 2}, True, "y")], False)[0])

    def test_no_boolean_answer_fails_both_ways(self):
        for expected in (True, False):
            with self.subTest(expected=expected):
                passed, reason = check_vat.verdict([({"v": 1}, None, "run failed")], expected)
                self.assertFalse(passed)
                self.assertIn("no input contract", reason)


class FindWorkflowTests(unittest.TestCase):
    def test_ignores_root_and_node_modules_and_picks_the_first_project_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Workflow.json").write_text("{}")
            (root / "node_modules" / "pkg").mkdir(parents=True)
            (root / "node_modules" / "pkg" / "Workflow.json").write_text("{}")
            self.assertIsNone(check_vat.find_workflow(root))
            for project in ("Vat", "Vat-Check"):
                (root / project).mkdir()
                (root / project / "Workflow.json").write_text("{}")
            # String order, as `LC_ALL=C sort` sees it: "-" sorts before "/".
            self.assertEqual(check_vat.find_workflow(root), (root / "Vat-Check" / "Workflow.json").resolve())


class ViesValidTests(unittest.TestCase):
    @staticmethod
    def respond(payload):
        response = mock.MagicMock()
        response.__enter__.return_value = io.BytesIO(json.dumps(payload).encode())
        return response

    def ask(self, urlopen, deadline_in=300):
        with mock.patch("urllib.request.urlopen", urlopen), mock.patch.object(check_vat.time, "sleep"):
            return check_vat.vies_valid("RO", "34737997", time.monotonic() + deadline_in)

    def test_returns_the_boolean_vies_gives(self):
        for valid in (True, False):
            with self.subTest(valid=valid):
                self.assertEqual(self.ask(mock.Mock(return_value=self.respond({"valid": valid}))), (valid, None))

    def test_saturation_without_a_valid_field_is_no_answer_after_retries(self):
        busy = {"actionSucceed": False, "errorWrappers": [{"error": "MS_MAX_CONCURRENT_REQ"}]}
        urlopen = mock.Mock(side_effect=lambda *a, **k: self.respond(busy))
        value, reason = self.ask(urlopen)
        self.assertIsNone(value)
        self.assertIn("MS_MAX_CONCURRENT_REQ", reason)
        self.assertEqual(urlopen.call_count, 3)

    def test_network_and_protocol_errors_are_no_answer(self):
        for error in (urllib.error.URLError("down"), ConnectionResetError("reset"), TimeoutError("slow"),
                      http.client.IncompleteRead(b"")):
            with self.subTest(error=type(error).__name__):
                value, reason = self.ask(mock.Mock(side_effect=error))
                self.assertIsNone(value)
                self.assertIn(type(error).__name__, reason)

    def test_non_object_payload_is_no_answer(self):
        self.assertIsNone(self.ask(mock.Mock(return_value=self.respond(["unexpected"])))[0])

    def test_does_not_retry_past_the_deadline(self):
        urlopen = mock.Mock(side_effect=urllib.error.URLError("down"))
        self.ask(urlopen, deadline_in=10)
        self.assertEqual(urlopen.call_count, 1)


class EvaluateTests(unittest.TestCase):
    def test_runs_nothing_once_the_budget_is_used_up(self):
        runner = Runner(prefixed)
        with mock.patch.object(check_vat, "run_row", autospec=True, side_effect=runner):
            observations = check_vat.evaluate(Path("Workflow.json"), [{"v": "RO1"}], time.monotonic())
        self.assertEqual(runner.calls, [])
        self.assertIn("budget", observations[0][2])

    def test_missing_uip_is_infrastructure(self):
        with mock.patch.object(check_vat, "run_row", autospec=True, side_effect=FileNotFoundError("uip")), \
                self.assertRaises(check_vat.InfraError):
            check_vat.evaluate(Path("Workflow.json"), [{"v": "RO1"}], time.monotonic() + 300)


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

    def test_correct_workflow_passes_both_checklist_checks(self):
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
