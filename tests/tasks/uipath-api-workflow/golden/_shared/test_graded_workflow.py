#!/usr/bin/env python3
"""Offline tests for graded_workflow.py: the path it prints for each scenario, the project
listing of `--single`, and a sandbox without a project.

Run: python3 -m unittest discover -s <this directory>
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import graded_workflow  # noqa: E402

HELPER = {"output": {"schema": {"document": {"properties": {"epics": {"type": "array"}}}}}}
RELEASE_NOTES = {"input": {"schema": {"document": {"properties": {"epicKeys": {"type": "array"}}}}},
                 "output": {"schema": {"document": {"properties": {"releaseNotes": {"type": "array"}}}}}}
VAT_CHECK = {"input": {"schema": {"document": {"properties": {"vatNumber": {"type": "string"}}}}},
             "output": {"schema": {"document": {"properties": {"isValid": {"type": "boolean"}}}}}}
EXPIRING_CONTRACTS = {"output": {"schema": {"document": {"properties": {"contracts": {"type": "array"}}}}}}


class GradedWorkflowTests(unittest.TestCase):
    def run_script(self, projects, *args):
        """(exit code, stdout, stderr) of graded_workflow.py in a working directory holding
        {folder: workflow}."""
        with tempfile.TemporaryDirectory() as tmp:
            for folder, workflow in projects.items():
                (Path(tmp) / folder).mkdir()
                (Path(tmp) / folder / "Workflow.json").write_text(json.dumps(workflow))
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                with contextlib.redirect_stdout(io.StringIO()) as out, \
                        contextlib.redirect_stderr(io.StringIO()) as err:
                    code = graded_workflow.main(list(args))
            finally:
                os.chdir(cwd)
        return code, out.getvalue(), err.getvalue()

    def test_each_scenario_prints_the_project_its_grader_grades(self):
        projects = {"a-release-notes": RELEASE_NOTES, "b-vat-check": VAT_CHECK, "c-expiring": EXPIRING_CONTRACTS}
        graded = {"jira_release_notes": "a-release-notes", "vat_check": "b-vat-check",
                  "salesforce_expiring_contracts": "c-expiring"}
        self.assertEqual(set(graded), set(graded_workflow.GRADERS))
        for scenario, folder in graded.items():
            with self.subTest(scenario=scenario):
                self.assertEqual(self.run_script(projects, scenario), (0, f"./{folder}/Workflow.json\n", ""))

    def test_every_scenario_grades_a_lone_project(self):
        for scenario in graded_workflow.GRADERS:
            with self.subTest(scenario=scenario):
                self.assertEqual(self.run_script({"Only": {}}, scenario), (0, "./Only/Workflow.json\n", ""))

    def test_single_lists_every_project_and_marks_the_graded_one(self):
        code, out, _ = self.run_script({"epic-discovery": HELPER, "release-notes": RELEASE_NOTES},
                                       "jira_release_notes", "--single")
        self.assertEqual(code, 1)
        self.assertEqual(out.splitlines(),
                         ["./epic-discovery/Workflow.json", "./release-notes/Workflow.json  (graded)"])
        self.assertEqual(self.run_script({"release-notes": RELEASE_NOTES}, "jira_release_notes", "--single"),
                         (0, "./release-notes/Workflow.json  (graded)\n", ""))

    def test_without_a_project_nothing_is_printed(self):
        for args in (["vat_check"], ["vat_check", "--single"]):
            with self.subTest(args=args):
                code, out, err = self.run_script({}, *args)
                self.assertEqual((code, out), (1, ""))
                self.assertIn("no Workflow.json inside a project folder", err)

    def test_an_unknown_scenario_is_a_usage_error(self):
        with self.assertRaises(SystemExit) as raised, contextlib.redirect_stderr(io.StringIO()):
            graded_workflow.main(["release_notes"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
