#!/usr/bin/env python3
"""Offline tests for check_vat.py: VIES's own answer, its retries, and the grading time
budget.

Run: python3 -m unittest discover -s <this directory>
"""
import http.client
import io
import json
import sys
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vat_fakes import Runner, check_vat, prefixed  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
