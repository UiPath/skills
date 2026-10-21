#!/usr/bin/env python3
"""Offline tests for check_vat.py: what counts as an answer and the pass/fail rule.

Run: python3 -m unittest discover -s <this directory>
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vat_fakes import check_vat  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
