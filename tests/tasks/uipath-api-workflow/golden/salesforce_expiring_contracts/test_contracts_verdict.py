#!/usr/bin/env python3
"""Offline tests for check_contracts.py's reading of the workflow: the 30-day window, the
inputs it infers, what counts as a returned contract, and the verdict.

Run: python3 -m unittest discover -s <this directory>
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts_fakes import CONTRACTS, TODAY, cc, contract  # noqa: E402


class WindowTests(unittest.TestCase):
    def test_window_includes_today_through_thirty_days(self):
        self.assertTrue(cc.is_inside(contract(0, "x"), TODAY))
        self.assertTrue(cc.is_inside(contract(30, "x"), TODAY))
        self.assertFalse(cc.is_inside(contract(31, "x"), TODAY))
        self.assertFalse(cc.is_inside(contract(-1, "x"), TODAY))
        self.assertIsNone(cc.is_inside({"id": "x", "label": "x"}, TODAY))


class InputTests(unittest.TestCase):
    def test_infers_day_counts_dates_and_turns_reminders_off(self):
        declared = {"daysAhead": {"type": "integer"}, "asOfDate": {"type": "string"},
                    "sendReminders": {"type": "boolean"}, "dryRun": {"type": "boolean"}, "ownerEmail": {"type": "string"}}
        self.assertEqual(cc.inputs_for(declared, TODAY),
                         {"daysAhead": 30, "asOfDate": "2026-10-08", "sendReminders": False, "dryRun": True})


class VerdictTests(unittest.TestCase):
    def test_returned_matches_short_or_long_ids_numbers_and_labels(self):
        self.assertTrue(cc.returned(CONTRACTS[0], '{"Id": "800AAAAAAAAAAA1QAZ"}'))
        self.assertTrue(cc.returned(CONTRACTS[0], '{"ContractNumber": "00000101"}'))
        self.assertFalse(cc.returned(CONTRACTS[0], '{"ContractNumber": "000001010"}'))
        self.assertTrue(cc.returned(CONTRACTS[0], json.dumps({"d": CONTRACTS[0]["label"]})))

    def test_needs_every_inside_contract_and_no_outside_one(self):
        good = [{"Id": c["id"] + "QAZ"} for c in CONTRACTS if c["days"] in (5, 12, 25)]
        self.assertEqual(cc.verdict(CONTRACTS, {"contracts": good}, TODAY), (True, [], 3))
        passed, problems, _ = cc.verdict(CONTRACTS, {"contracts": good[:2] + [{"Id": CONTRACTS[2]["id"]}]}, TODAY)
        self.assertFalse(passed)
        self.assertEqual(len(problems), 2)

    def test_hardcoding_what_existed_at_authoring_time_misses_the_grading_contract(self):
        authored = [{"Id": c["id"]} for c in CONTRACTS if c["days"] in (5, 25)]
        passed, problems, _ = cc.verdict(CONTRACTS, authored, TODAY)
        self.assertFalse(passed)
        self.assertIn("+12d", problems[0])


if __name__ == "__main__":
    unittest.main()
