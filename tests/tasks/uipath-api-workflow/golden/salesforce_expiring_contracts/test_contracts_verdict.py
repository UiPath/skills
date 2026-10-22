#!/usr/bin/env python3
"""Offline tests for check_contracts.py's reading of the workflow: the 30-day window, the
inputs it infers, the project it picks among helper projects, what counts as a returned
contract, and the verdict.

Run: python3 -m unittest discover -s <this directory>
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts_fakes import (  # noqa: E402
    CONTRACTS, EXPIRING_CONTRACTS, FIELD_LISTER, REMINDER_SENDER, TODAY, cc, contract, sandbox, workflow_declaring,
)


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


class PickWorkflowTests(unittest.TestCase):
    def pick(self, projects):
        """The folder pick_workflow grades among {folder: Workflow.json text}."""
        with sandbox(projects):
            chosen = cc.pick_workflow(today=TODAY)
        return chosen.parent.name if chosen else None

    def test_helper_projects_lose_to_the_project_listing_contracts(self):
        self.assertEqual(self.pick({"contract-fields": FIELD_LISTER, "expiring-contracts": EXPIRING_CONTRACTS,
                                    "send-reminders": REMINDER_SENDER}), "expiring-contracts")

    def test_a_required_input_the_grader_cannot_fill_rules_a_project_out_unless_it_has_a_default(self):
        listing = {"contracts": {"type": "array"}}
        by_owner = workflow_declaring({"ownerId": {"type": "string"}}, listing, required=["ownerId"])
        owner_default = workflow_declaring({"ownerId": {"type": "string", "default": "any"}}, listing,
                                           required=["ownerId"])
        self.assertEqual(self.pick({"a-by-owner": by_owner, "b-fields": FIELD_LISTER}), "b-fields")
        self.assertEqual(self.pick({"a-by-owner": owner_default, "b-fields": FIELD_LISTER}), "a-by-owner")

    def test_an_optional_input_the_grader_cannot_fill_does_not_rule_a_project_out(self):
        expiring = workflow_declaring({"daysAhead": {"type": "integer"}, "ownerId": {"type": "string"}},
                                      {"contracts": {"type": "array"}}, required=["daysAhead"])
        self.assertEqual(self.pick({"contract-fields": FIELD_LISTER, "expiring": expiring}), "expiring")

    def test_only_a_list_counts_as_the_contracts_output(self):
        one = workflow_declaring(outputs={"contract": {"type": "object"}})
        listed = workflow_declaring(outputs={"expiringContracts": {"type": "array"}})
        self.assertEqual(self.pick({"a-one": one, "b-listed": listed}), "b-listed")


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
