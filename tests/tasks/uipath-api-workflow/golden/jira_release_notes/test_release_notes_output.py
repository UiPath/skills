#!/usr/bin/env python3
"""Offline tests for check_release_notes.py's reading of the workflow: how the epic keys
are handed in, what counts as release notes, the marker rule, and the verdict.

Run: python3 -m unittest discover -s <this directory>
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes_fakes import CLOSED, FIXTURE, crn, notes_for  # noqa: E402


class EpicPlanTests(unittest.TestCase):
    keys = ["A-1", "A-2"]

    def test_array_input_gets_the_list(self):
        self.assertEqual(crn.epic_plans({"epicKeys": {"type": "array"}}, self.keys), [[{"epicKeys": self.keys}]])

    def test_string_input_gets_the_joined_keys_then_one_epic_per_run(self):
        plans = crn.epic_plans({"epicKey": {"type": "string"}}, self.keys)
        self.assertEqual(plans, [[{"epicKey": "A-1, A-2"}], [{"epicKey": "A-1"}, {"epicKey": "A-2"}]])

    def test_input_is_found_by_name_or_as_the_only_input(self):
        plans = crn.epic_plans({"model": {"type": "string"}, "epics": {}}, self.keys)
        self.assertEqual(plans[0], [{"epics": self.keys}])
        self.assertEqual(crn.epic_plans({"items": {"type": "array"}}, self.keys), [[{"items": self.keys}]])
        self.assertEqual(crn.epic_plans({"a": {}, "b": {}}, self.keys), [])
        self.assertEqual(crn.epic_plans({}, self.keys), [])


class NotesTests(unittest.TestCase):
    def test_a_note_needs_a_summary_and_a_separate_description(self):
        self.assertTrue(crn.is_note({"title": "CSV export", "details": "Export the list"}))
        self.assertFalse(crn.is_note({"summary": "CSV export"}))
        self.assertFalse(crn.is_note({"summary": "CSV export", "description": " "}))
        self.assertFalse(crn.is_note("CSV export"))

    def test_finds_the_longest_list_anywhere_including_json_strings(self):
        raw = {"releaseNotes": json.dumps(notes_for(CLOSED)), "other": [{"summary": "x", "description": "y"}]}
        self.assertEqual(len(crn.note_entries(raw)), len(CLOSED))

    def test_markers_match_whole_words_only(self):
        self.assertTrue(crn.mentions("the vat breakdown", "VAT"))
        self.assertFalse(crn.mentions("contracts are activated", "VAT"))
        self.assertTrue(crn.mentions("unlock with face id.", "Face ID"))


class VerdictTests(unittest.TestCase):
    def test_complete_notes_for_closed_tickets_pass(self):
        passed, problems, count = crn.verdict(notes_for(CLOSED), FIXTURE)
        self.assertTrue(passed, problems)
        self.assertEqual(count, len(CLOSED))

    def test_missing_closed_and_included_open_tickets_fail(self):
        others = [c for c in crn.children(FIXTURE) if c["status"] != "done"]
        passed, problems, _ = crn.verdict(notes_for(CLOSED[1:] + others[:1]), FIXTURE)
        self.assertFalse(passed)
        self.assertIn(f"closed tickets missing: {CLOSED[0]['key']}", problems)
        self.assertIn(f"tickets that are not closed included: {others[0]['key']}", problems)

    def test_prose_without_a_list_of_notes_fails(self):
        prose = " ".join(f"{c['summary']}." for c in CLOSED)
        passed, problems, _ = crn.verdict({"notes": prose}, FIXTURE)
        self.assertFalse(passed)
        self.assertIn("no list of release notes with a summary and a description", problems)


if __name__ == "__main__":
    unittest.main()
