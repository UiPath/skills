#!/usr/bin/env python3
"""Offline tests for check_release_notes.py's fixture handling: the committed fixture,
status drift, and the grading-time ticket (created, closed, searchable, deleted), with
Jira stubbed out.

Run: python3 -m unittest discover -s <this directory>
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes_fakes import FIXTURE, GRADING, UNSEEDED, crn, seeded  # noqa: E402


class FixtureTests(unittest.TestCase):
    def test_committed_fixture_marks_each_child(self):
        for child in crn.children(UNSEEDED):
            self.assertIn(child["status"], crn.CATEGORY)
            self.assertTrue(child["markers"])
        self.assertTrue(any(c["status"] == "done" for c in crn.children(UNSEEDED)))
        self.assertTrue(any(c["status"] != "done" for c in crn.children(UNSEEDED)))

    def test_unseeded_fixture_is_infrastructure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(UNSEEDED))
            with self.assertRaisesRegex(crn.InfraError, "not seeded"):
                crn.load_fixture(path)
            path.write_text(json.dumps(FIXTURE))
            self.assertEqual(crn.load_fixture(path)["epics"][0]["key"], "A-1")

    def test_status_drift_names_moved_tickets(self):
        found = {"issues": [{"key": "A-11", "fields": {"status": {"statusCategory": {"key": "indeterminate"}}}},
                            {"key": "A-14", "fields": {"status": {"statusCategory": {"key": "indeterminate"}}}}]}
        self.assertEqual(crn.status_drift(FIXTURE, found), ["A-11 is indeterminate, fixture.json says done"])


class GradingTicketTests(unittest.TestCase):
    def test_waits_until_the_search_sees_the_new_ticket(self):
        answers = [{"issues": []}, {"issues": [{"key": "A-19"}]}]
        with mock.patch.object(crn, "data", side_effect=answers) as data, mock.patch.object(crn.time, "sleep"):
            crn.wait_until_searchable("conn", "A-1", "A-19")
        self.assertEqual(data.call_count, 2)
        self.assertIn("parent = A-1 AND key = A-19", data.call_args.args[-1])

    def test_a_connection_that_cannot_search_gets_a_fixed_pause(self):
        with mock.patch.object(crn, "data", side_effect=crn.InfraError("no search")), \
                mock.patch.object(crn.time, "sleep") as sleep:
            crn.wait_until_searchable("conn", "A-1", "A-19")
        sleep.assert_called_once()

    def test_a_ticket_that_never_shows_up_is_infrastructure(self):
        with mock.patch.object(crn, "data", return_value={"issues": []}), mock.patch.object(crn.time, "sleep"):
            with self.assertRaisesRegex(crn.InfraError, "never showed up"):
                crn.wait_until_searchable("conn", "A-1", "A-19")

    def test_adds_a_closed_child_under_the_first_epic(self):
        fixture = seeded()
        fixture["task_type_id"] = "10001"
        with mock.patch.object(crn, "connection_id", return_value="conn"), \
                mock.patch.object(crn.seed, "create_issue", return_value="A-19") as create, \
                mock.patch.object(crn.seed, "transition") as transition, \
                mock.patch.object(crn, "wait_until_searchable"):
            self.assertEqual(crn.add_grading_ticket(fixture), ("conn", "A-19"))
        fields = create.call_args.args[1]
        self.assertEqual((fields["parent"], fields["issuetype"]), ({"key": "A-1"}, {"id": "10001"}))
        transition.assert_called_once_with("conn", "A-19", "done")
        self.assertEqual(fixture["epics"][0]["children"][-1], GRADING)

    def test_a_ticket_that_cannot_be_closed_is_deleted_again(self):
        fixture = seeded()
        with mock.patch.object(crn, "connection_id", return_value="conn"), \
                mock.patch.object(crn.seed, "project_id", return_value="1"), \
                mock.patch.object(crn.seed, "issue_type_id", return_value="10001"), \
                mock.patch.object(crn.seed, "create_issue", return_value="A-19"), \
                mock.patch.object(crn.seed, "transition", side_effect=crn.InfraError("no transition to done")), \
                mock.patch.object(crn.seed, "delete_issue") as delete:
            with self.assertRaisesRegex(crn.InfraError, "no transition"):
                crn.add_grading_ticket(fixture)
        delete.assert_called_once_with("conn", "A-19")
        self.assertEqual(len(fixture["epics"][0]["children"]), len(seeded()["epics"][0]["children"]))


if __name__ == "__main__":
    unittest.main()
