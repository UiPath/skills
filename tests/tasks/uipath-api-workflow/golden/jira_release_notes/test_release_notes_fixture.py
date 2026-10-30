#!/usr/bin/env python3
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes_fakes import COMMITTED, FIXTURE, crn, unseeded  # noqa: E402


def issue(key, category="done", summary=None, parent="A-1"):
    known = {child["key"]: child["summary"] for child in crn.children(FIXTURE)}
    fields = {"status": {"statusCategory": {"key": category}}, "summary": summary or known.get(key, "New ticket"),
              "parent": {"key": parent, "fields": {"summary": "Epic", "status": {"statusCategory": {"key": "new"}}}}}
    return {"key": key, "fields": fields}


def unchanged():
    return {"issues": [issue(child["key"], crn.CATEGORY[child["status"]], parent=epic["key"])
                       for epic in FIXTURE["epics"] for child in epic["children"]]}


class FixtureTests(unittest.TestCase):
    def test_committed_fixture_marks_each_child(self):
        for child in crn.children(COMMITTED):
            self.assertIn(child["status"], crn.CATEGORY)
            self.assertTrue(child["markers"])
        self.assertTrue(any(c["status"] == "done" for c in crn.children(COMMITTED)))
        self.assertTrue(any(c["status"] != "done" for c in crn.children(COMMITTED)))

    def test_unseeded_fixture_is_infrastructure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(unseeded()))
            with self.assertRaisesRegex(crn.InfraError, "not seeded"):
                crn.load_fixture(path)
            path.write_text(json.dumps(FIXTURE))
            self.assertEqual(crn.load_fixture(path)["epics"][0]["key"], "A-1")

    def test_status_drift_names_moved_tickets(self):
        found = {"issues": [{"key": "A-11", "fields": {"status": {"statusCategory": {"key": "indeterminate"}}}},
                            {"key": "A-14", "fields": {"status": {"statusCategory": {"key": "indeterminate"}}}}]}
        self.assertEqual(crn.fixture_drift(FIXTURE, found), ["A-11 is indeterminate, fixture.json says done"])

    def test_the_fixture_as_seeded_has_no_drift_or_extra_issues(self):
        self.assertEqual(crn.fixture_drift(FIXTURE, unchanged()), [])
        self.assertEqual(crn.extra_children(FIXTURE, unchanged()), [])

    def test_a_renamed_or_moved_ticket_is_drift(self):
        found = {"issues": [issue("A-11", summary="Export to Excel"), issue("A-12", parent="A-2")]}
        self.assertEqual(crn.fixture_drift(FIXTURE, found),
                         ["A-11 is titled 'Export to Excel', fixture.json says 'Export the invoice list to CSV'",
                          "A-12 is under A-2, fixture.json says A-1"])

    def test_issues_under_a_fixture_epic_that_fixture_json_does_not_list_are_extra(self):
        found = unchanged()
        found["issues"] += [issue("A-99", parent="A-2"), issue("B-1", parent="B-0")]
        self.assertEqual(crn.extra_children(FIXTURE, found), ["A-99"])


class CheckFixtureTests(unittest.TestCase):
    def check(self, found):
        with mock.patch.object(crn, "connection_id", return_value="conn"), \
                mock.patch.object(crn, "data", side_effect=[found] if not isinstance(found, Exception) else found) \
                as data, contextlib.redirect_stderr(io.StringIO()) as err:
            crn.check_fixture(FIXTURE)
        args = data.call_args.args
        return err.getvalue(), json.loads(args[args.index("--query") + 1])["jql"]

    def test_searches_the_fixture_tickets_and_everything_under_its_epics(self):
        warnings, jql = self.check(unchanged())
        self.assertEqual(warnings, "")
        self.assertTrue(jql.startswith("key in (A-11, "))
        self.assertTrue(jql.endswith(" OR parent in (A-1, A-2)"))

    def test_drift_is_infrastructure_and_says_how_to_fix_it(self):
        found = unchanged()
        found["issues"][0]["fields"]["status"]["statusCategory"]["key"] = "indeterminate"
        with self.assertRaisesRegex(crn.InfraError, "A-11 is indeterminate.*set them back"):
            self.check(found)

    def test_an_extra_issue_only_warns(self):
        found = unchanged()
        found["issues"].append(issue("A-99", parent="A-1"))
        warnings, _ = self.check(found)
        self.assertIn("WARNING: A-99 sit under the fixture epics", warnings)

    def test_a_search_that_cannot_run_only_warns(self):
        warnings, _ = self.check(crn.InfraError("uip is resources run list failed"))
        self.assertIn("could not verify the fixture tickets", warnings)


if __name__ == "__main__":
    unittest.main()
