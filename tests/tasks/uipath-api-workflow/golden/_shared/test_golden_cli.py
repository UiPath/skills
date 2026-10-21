#!/usr/bin/env python3
"""Offline tests for golden_connectors.py's CLI side, with `uip` stubbed out: reading the
JSON envelope and picking the run user's one connection per connector.

Run: python3 -m unittest discover -s <this directory>
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import golden_connectors as gc  # noqa: E402


def completed(stdout, returncode=0):
    return mock.Mock(stdout=stdout, returncode=returncode)


class UipTests(unittest.TestCase):
    def test_reads_only_the_json_envelope(self):
        with mock.patch.object(gc.subprocess, "run", return_value=completed('{"Result": "Success", "Data": [1]}')) as run:
            self.assertEqual(gc.data("is", "connections", "list"), [1])
        self.assertEqual(run.call_args.args[0][-2:], ["--output", "json"])

    def test_non_json_and_failure_envelopes_are_infrastructure(self):
        with mock.patch.object(gc.subprocess, "run", return_value=completed("Checking today's update", 1)):
            with self.assertRaisesRegex(gc.InfraError, "printed no JSON"):
                gc.data("is", "connections", "list")
        failure = json.dumps({"Result": "Failure", "ErrorCode": "not_found", "Message": "no such connector"})
        with mock.patch.object(gc.subprocess, "run", return_value=completed(failure)):
            with self.assertRaisesRegex(gc.InfraError, "no such connector"):
                gc.data("is", "connections", "list")

    def test_missing_uip_is_infrastructure(self):
        with mock.patch.object(gc.subprocess, "run", side_effect=FileNotFoundError("uip")):
            with self.assertRaisesRegex(gc.InfraError, "FileNotFoundError"):
                gc.uip("--version")


class ConnectionTests(unittest.TestCase):
    rows = [
        {"Id": "a", "ConnectorKey": "uipath-atlassian-jira", "State": "Enabled"},
        {"Id": "b", "ConnectorKey": "uipath-atlassian-jira", "State": "Failed"},
        {"Id": "c", "ConnectorKey": "uipath-salesforce-sfdc", "State": "Enabled"},
    ]

    def test_picks_the_single_enabled_connection_for_the_connector(self):
        with mock.patch.object(gc, "data", return_value=self.rows):
            self.assertEqual(gc.connection_id("uipath-atlassian-jira"), "a")

    def test_none_or_several_enabled_is_infrastructure(self):
        with mock.patch.object(gc, "data", return_value=self.rows):
            with self.assertRaisesRegex(gc.InfraError, "found 0 of 0"):
                gc.connection_id("uipath-openai-openai")
        doubled = self.rows + [{"id": "d", "connectorKey": "uipath-atlassian-jira", "state": "enabled"}]
        with mock.patch.object(gc, "data", return_value=doubled):
            with self.assertRaisesRegex(gc.InfraError, "found 2 of 3"):
                gc.connection_id("uipath-atlassian-jira")

    @staticmethod
    def listing(workspace, all_folders):
        def data(*args):
            rows = all_folders if "--all-folders" in args else workspace
            if isinstance(rows, Exception):
                raise rows
            return rows
        return data

    def test_the_personal_workspace_connection_wins_over_other_folders(self):
        mine = {"Id": "mine", "ConnectorKey": "uipath-salesforce-sfdc", "State": "Enabled"}
        with mock.patch.object(gc, "data", side_effect=self.listing([mine], self.rows + [mine])):
            self.assertEqual(gc.connection_id("uipath-salesforce-sfdc"), "mine")

    def test_falls_back_to_all_folders_when_the_workspace_has_none_or_cannot_be_listed(self):
        for workspace in ([], gc.InfraError("Personal workspace not available")):
            with self.subTest(workspace=workspace), \
                    mock.patch.object(gc, "data", side_effect=self.listing(workspace, self.rows)):
                self.assertEqual(gc.connection_id("uipath-atlassian-jira"), "a")

    def test_several_enabled_in_the_workspace_is_infrastructure_even_with_one_elsewhere(self):
        both = [{"Id": i, "ConnectorKey": "uipath-atlassian-jira", "State": "Enabled"} for i in ("x", "y")]
        with mock.patch.object(gc, "data", side_effect=self.listing(both, self.rows)):
            with self.assertRaisesRegex(gc.InfraError, "in the personal workspace, found 2 of 2"):
                gc.connection_id("uipath-atlassian-jira")

    def test_an_all_folders_failure_is_infrastructure(self):
        for workspace in ([], gc.InfraError("Personal workspace not available")):
            with self.subTest(workspace=workspace), \
                    mock.patch.object(gc, "data", side_effect=self.listing(workspace, gc.InfraError("all folders down"))):
                with self.assertRaisesRegex(gc.InfraError, "all folders down"):
                    gc.connection_id("uipath-atlassian-jira")


if __name__ == "__main__":
    unittest.main()
