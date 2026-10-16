#!/usr/bin/env python3
"""Offline tests for check_release_notes.py's run flow, with the workflow runner and Jira
stubbed out: input-shape fallbacks, provider refusals, the time budget, and main() with the
grading-time ticket and the judge's file.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes_fakes import (  # noqa: E402
    CLOSED, FIXTURE, GRADING, Runner, crn, notes_for, per_epic, sandbox, seeded, workflow_with_inputs,
)


class GradeTests(unittest.TestCase):
    def test_falls_back_to_one_epic_per_run_and_merges(self):
        runner = Runner(lambda inputs: per_epic(inputs) if "," not in inputs["epicKey"] else (False, None, "bad key"))
        plans = crn.epic_plans({"epicKey": {"type": "string"}}, ["A-1", "A-2"])
        with mock.patch.object(crn, "run_workflow", runner):
            passed, message, raw = crn.grade("W.json", plans, FIXTURE, deadline=crn.time.monotonic() + 300)
        self.assertTrue(passed, message)
        self.assertEqual(runner.calls, [{"epicKey": "A-1, A-2"}, {"epicKey": "A-1"}, {"epicKey": "A-2"}])
        self.assertEqual(len(raw), 2)

    def test_provider_refusal_is_infrastructure(self):
        runner = Runner(lambda inputs: (False, None, 'run failed: {"Message": "429 Too Many Requests"}'))
        with mock.patch.object(crn, "run_workflow", runner):
            with self.assertRaisesRegex(crn.InfraError, "provider refused"):
                crn.grade("W.json", [[{"epics": ["A-1"]}]], FIXTURE, deadline=crn.time.monotonic() + 300)

    def test_nothing_runs_once_the_budget_is_used_up(self):
        runner = Runner(per_epic)
        with mock.patch.object(crn, "run_workflow", runner):
            passed, message, raw = crn.grade("W.json", [[{"epicKey": "A-1"}]], FIXTURE, deadline=crn.time.monotonic())
        self.assertFalse(passed)
        self.assertIn("budget", message)
        self.assertEqual(runner.calls, [])


class MainTests(unittest.TestCase):
    def run_main(self, workflow_text, runner, statuses_ok=True):
        fixture = seeded()
        drift = None if statuses_ok else crn.InfraError("fixture tickets changed status: A-11")

        def add_grading_ticket(fx):
            fx["epics"][0]["children"].append(dict(GRADING))
            return "conn", GRADING["key"]

        with sandbox(workflow_text) as root, \
                mock.patch.object(crn, "load_fixture", return_value=fixture), \
                mock.patch.object(crn, "check_fixture_statuses", side_effect=drift), \
                mock.patch.object(crn, "add_grading_ticket", side_effect=add_grading_ticket), \
                mock.patch.object(crn, "remove_grading_ticket") as remove, \
                mock.patch.object(crn, "run_workflow", runner), \
                contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                code = crn.main()
            except SystemExit as exc:
                code = exc.code
            judged = root / crn.OUTPUT_FILE
            payload = json.loads(judged.read_text()) if judged.exists() else None
        self.removed = remove.call_args_list
        return code, out.getvalue() + err.getvalue(), payload

    def test_correct_workflow_passes_and_hands_its_output_to_the_judge(self):
        code, log, payload = self.run_main(workflow_with_inputs(epicKeys={"type": "array"}),
                                           Runner(lambda inputs: (True, notes_for(CLOSED + [GRADING]), None)))
        self.assertEqual(code, 0, log)
        self.assertIn("OK:", log)
        self.assertEqual(len(payload["workflow_output"]), len(CLOSED) + 1)
        self.assertEqual(len(payload["closed_tickets"]), len(CLOSED) + 1)
        self.assertEqual(self.removed, [mock.call("conn", "A-19")])

    def test_notes_hardcoded_at_authoring_time_miss_the_grading_ticket(self):
        code, log, _ = self.run_main(workflow_with_inputs(epicKeys={"type": "array"}),
                                     Runner(lambda inputs: (True, notes_for(CLOSED), None)))
        self.assertIn("closed tickets missing: A-19", str(code))
        self.assertEqual(self.removed, [mock.call("conn", "A-19")])

    def test_workflow_without_an_epic_input_fails(self):
        code, log, payload = self.run_main(workflow_with_inputs(a={}, b={}), Runner(per_epic))
        self.assertIn("declares no input for the epic keys", str(code))
        self.assertIsNone(payload["workflow_output"])

    def test_fixture_problems_are_infrastructure(self):
        code, log, _ = self.run_main(workflow_with_inputs(epicKey={"type": "string"}), Runner(per_epic),
                                     statuses_ok=False)
        self.assertEqual(code, crn.INFRA_EXIT)
        self.assertIn("INFRA: fixture tickets changed status", log)


if __name__ == "__main__":
    unittest.main()
