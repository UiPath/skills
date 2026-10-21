#!/usr/bin/env python3
"""Offline tests for check_release_notes.py's run flow, with the workflow runner and Jira
stubbed out: input-shape fallbacks, the run on the first epic alone, provider refusals, the
time budget, the project picked among helper projects, and main() with the workflow-file
scan, the refusal to run a workflow that would change Jira, and the judge's file.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_notes_fakes import (  # noqa: E402
    CLOSED, FIXTURE, Runner, crn, notes_for, per_epic, per_epic_list, sandbox, seeded, workflow_declaring,
    workflow_with_inputs,
)

EPIC_DISCOVERY = workflow_declaring(outputs={"epics": {"type": "array"}})
TICKET_INSPECTION = workflow_declaring({"epicKey": {"type": "string"}}, {"tickets": {"type": "array"}})
RELEASE_NOTES = workflow_declaring({"epicKeys": {"type": "array"}}, {"releaseNotes": {"type": "array"}})


class GradeTests(unittest.TestCase):
    def grade(self, plans, runner, budget=300):
        with mock.patch.object(crn, "run_workflow", runner):
            return crn.grade("W.json", plans, FIXTURE, deadline=crn.time.monotonic() + budget)

    def test_falls_back_to_one_epic_per_run_and_merges(self):
        runner = Runner(lambda inputs: per_epic(inputs) if "," not in inputs["epicKey"] else (False, None, "bad key"))
        passed, message, raw = self.grade(crn.epic_plans({"epicKey": {"type": "string"}}, ["A-1", "A-2"]), runner)
        self.assertTrue(passed, message)
        self.assertEqual(runner.calls, [{"epicKey": "A-1, A-2"}, {"epicKey": "A-1"}, {"epicKey": "A-2"}])
        self.assertEqual(len(raw), 2)

    def test_a_list_input_is_run_again_on_the_first_epic_alone(self):
        runner = Runner(per_epic_list)
        passed, message, _ = self.grade(crn.epic_plans({"epicKeys": {"type": "array"}}, ["A-1", "A-2"]), runner)
        self.assertTrue(passed, message)
        self.assertEqual(runner.calls, [{"epicKeys": ["A-1", "A-2"]}, {"epicKeys": ["A-1"]}])

    def test_notes_that_ignore_the_epics_passed_in_fail(self):
        passed, message, raw = self.grade([[{"epicKeys": ["A-1", "A-2"]}]],
                                          Runner(lambda inputs: (True, notes_for(CLOSED), None)))
        self.assertFalse(passed)
        self.assertIn("on A-1 alone: tickets of another epic included: A-21, A-22", message)
        self.assertEqual(len(raw), len(CLOSED))

    def test_provider_refusal_is_infrastructure(self):
        runner = Runner(lambda inputs: (False, None, 'run failed: {"Message": "429 Too Many Requests"}'))
        with self.assertRaisesRegex(crn.InfraError, "provider refused"):
            self.grade([[{"epics": ["A-1"]}]], runner)

    def test_nothing_runs_once_the_budget_is_used_up(self):
        runner = Runner(per_epic)
        passed, message, raw = self.grade([[{"epicKey": "A-1"}]], runner, budget=0)
        self.assertFalse(passed)
        self.assertIn("budget", message)
        self.assertEqual(runner.calls, [])


class MainTests(unittest.TestCase):
    def run_main(self, workflow_text, runner, statuses_ok=True):
        drift = None if statuses_ok else crn.InfraError("fixture tickets changed: A-11 is indeterminate")
        with sandbox(workflow_text) as root, \
                mock.patch.object(crn, "load_fixture", return_value=seeded()), \
                mock.patch.object(crn, "check_fixture", side_effect=drift), \
                mock.patch.object(crn, "run_workflow", runner), \
                contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            try:
                code = crn.main()
            except SystemExit as exc:
                code = exc.code
            judged = root / crn.OUTPUT_FILE
            payload = json.loads(judged.read_text()) if judged.exists() else None
        return code, out.getvalue() + err.getvalue(), payload

    def test_correct_workflow_passes_and_hands_its_output_to_the_judge(self):
        code, log, payload = self.run_main(workflow_with_inputs(epicKeys={"type": "array"}), Runner(per_epic_list))
        self.assertEqual(code, 0, log)
        self.assertIn("OK:", log)
        self.assertEqual(len(payload["workflow_output"]), len(CLOSED))
        self.assertEqual(len(payload["closed_tickets"]), len(CLOSED))

    def test_notes_copied_into_the_workflow_file_fail_without_a_run(self):
        workflow = json.loads(workflow_with_inputs(epicKeys={"type": "array"}))
        workflow["notes"] = notes_for(CLOSED[:1])
        runner = Runner(per_epic_list)
        code, log, payload = self.run_main(json.dumps(workflow), runner)
        self.assertIn(f"holds the key, summary or description of {CLOSED[0]['key']}", str(code))
        self.assertEqual(runner.calls, [])
        self.assertIsNone(payload["workflow_output"])

    def test_a_workflow_that_would_change_jira_fails_without_a_run(self):
        workflow = json.loads(workflow_with_inputs(epicKeys={"type": "array"}))
        search = {"call": "UiPath.IntSvc", "with": {"connector": crn.JIRA, "method": "GET", "endpoint": "/search"}}
        model = {"call": "UiPath.IntSvc", "with": {"connector": "uipath-uipath-airdk", "method": "POST",
                                                   "endpoint": "/v1/llmCall"}}
        comment = {"call": "UiPath.IntSvc", "with": {"connector": crn.JIRA, "method": "POST",
                                                     "endpoint": "/issue_comments"}}
        workflow["do"] = [{"Sequence_1": {"do": [{"Search_1": search}, {"Notes_1": model}, {"Comment_1": comment}]}}]
        runner = Runner(per_epic_list)
        code, log, payload = self.run_main(json.dumps(workflow), runner)
        self.assertIn(f"would change Jira or send something on every run (Comment_1 ({crn.JIRA} POST /issue_comments))",
                      str(code))
        self.assertEqual(runner.calls, [])
        self.assertIsNone(payload["workflow_output"])

    def test_workflow_without_an_epic_input_fails(self):
        code, log, payload = self.run_main(workflow_with_inputs(a={}, b={}), Runner(per_epic))
        self.assertIn("declares no input for the epic keys", str(code))
        self.assertIsNone(payload["workflow_output"])

    def test_the_project_taking_the_epic_keys_is_graded_beside_helper_projects(self):
        projects = {"epic-discovery": EPIC_DISCOVERY, "release-notes": RELEASE_NOTES,
                    "ticket-inspection": TICKET_INSPECTION}
        code, log, payload = self.run_main(projects, Runner(per_epic_list))
        self.assertEqual(code, 0, log)
        self.assertIn(f"OK: {os.path.join('release-notes', 'Workflow.json')}:", log)
        self.assertEqual(len(payload["workflow_output"]), len(CLOSED))

    def test_without_a_project_taking_the_epic_keys_the_first_fails_as_before(self):
        projects = {"epic-discovery": EPIC_DISCOVERY, "summary": workflow_with_inputs(a={}, b={})}
        runner = Runner(per_epic)
        code, log, payload = self.run_main(projects, runner)
        self.assertIn(f"{os.path.join('epic-discovery', 'Workflow.json')} declares no input for the epic keys",
                      str(code))
        self.assertEqual(runner.calls, [])
        self.assertIsNone(payload["workflow_output"])

    def test_fixture_problems_are_infrastructure(self):
        code, log, _ = self.run_main(workflow_with_inputs(epicKey={"type": "string"}), Runner(per_epic),
                                     statuses_ok=False)
        self.assertEqual(code, crn.INFRA_EXIT)
        self.assertIn("INFRA: fixture tickets changed: A-11 is indeterminate", log)


class PickWorkflowTests(unittest.TestCase):
    def test_a_helper_taking_an_epic_key_loses_to_the_project_declaring_release_notes(self):
        with sandbox({"epic-tickets": TICKET_INSPECTION, "release-notes": RELEASE_NOTES}) as root:
            self.assertEqual(crn.pick_workflow(), (root / "release-notes" / "Workflow.json").resolve())

    def test_a_sole_input_with_any_name_takes_the_epic_keys(self):
        with sandbox({"a-discovery": EPIC_DISCOVERY, "b-notes": workflow_with_inputs(items={"type": "array"})}) as root:
            self.assertEqual(crn.pick_workflow(), (root / "b-notes" / "Workflow.json").resolve())


if __name__ == "__main__":
    unittest.main()
