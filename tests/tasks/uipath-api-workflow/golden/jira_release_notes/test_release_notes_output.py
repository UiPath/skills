#!/usr/bin/env python3
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

    def test_marker_words_may_be_joined_by_spaces_hyphens_or_nothing(self):
        for text in ("unlock with faceid", "unlock with face-id", "unlock with face \u2013 id", "face  id"):
            self.assertTrue(crn.mentions(text, "Face ID"), text)
        self.assertFalse(crn.mentions("the surface id", "Face ID"))
        self.assertFalse(crn.mentions("faceidentity", "Face ID"))

    def test_a_ticket_is_named_by_its_key_or_a_marker(self):
        ticket = {"key": "A-11", "markers": ["CSV"]}
        self.assertTrue(crn.names(ticket, "shipped in a-11."))
        self.assertTrue(crn.names(ticket, "the csv export"))
        self.assertFalse(crn.names(ticket, "shipped in a-110 and xa-11"))


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

    def test_notes_that_reword_every_ticket_pass_when_they_carry_its_key(self):
        reworded = [{"summary": f"Improvement {c['key']}", "description": "Now available."} for c in CLOSED]
        passed, problems, _ = crn.verdict(reworded, FIXTURE)
        self.assertTrue(passed, problems)

    def test_an_open_ticket_named_only_by_its_key_is_included(self):
        others = [c for c in crn.children(FIXTURE) if c["status"] != "done"]
        notes = notes_for(CLOSED) + [{"summary": f"Coming soon: {others[0]['key']}", "description": "Later."}]
        passed, problems, _ = crn.verdict(notes, FIXTURE)
        self.assertFalse(passed)
        self.assertIn(f"tickets that are not closed included: {others[0]['key']}", problems)

    def test_the_first_epic_alone_must_leave_out_the_other_epic(self):
        first_closed = [c for c in FIXTURE["epics"][0]["children"] if c["status"] == "done"]
        self.assertEqual(crn.first_epic_verdict(notes_for(first_closed), FIXTURE), (True, []))
        passed, problems = crn.first_epic_verdict(notes_for(CLOSED), FIXTURE)
        self.assertFalse(passed)
        self.assertEqual(problems, ["tickets of another epic included: A-21, A-22"])

    def test_prose_without_a_list_of_notes_fails(self):
        prose = " ".join(f"{c['summary']}." for c in CLOSED)
        passed, problems, _ = crn.verdict({"notes": prose}, FIXTURE)
        self.assertFalse(passed)
        self.assertIn("no list of release notes with a summary and a description", problems)


class CopiedTicketTests(unittest.TestCase):
    def test_a_ticket_key_summary_or_description_in_the_workflow_is_caught(self):
        first = CLOSED[0]
        for copied in (first["summary"], first["description"], f"see {first['key']}"):
            self.assertEqual(crn.copied_tickets(json.dumps({"notes": copied}), FIXTURE), [first["key"]], copied)

    def test_epic_keys_and_marker_words_are_not_copied_notes(self):
        text = json.dumps({"epicKeys": ["A-1", "A-2"], "format": "CSV", "example": "A-110"})
        self.assertEqual(crn.copied_tickets(text, FIXTURE), [])


if __name__ == "__main__":
    unittest.main()
