"""Behavioral tests for Maestro BPMN Alpha solution cleanup."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("cleanup_solutions.py")
SPEC = importlib.util.spec_from_file_location("bpmn_cleanup_solutions", SCRIPT)
assert SPEC and SPEC.loader
cleanup_solutions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup_solutions)


class CleanupSolutionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temporary.name)
        self.previous_cwd = Path.cwd()
        os.chdir(self.workdir)

    def tearDown(self) -> None:
        os.chdir(self.previous_cwd)
        self.temporary.cleanup()

    def write_manifest(self, name: str, solution_id: str) -> None:
        path = self.workdir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"SolutionId": solution_id}),
            encoding="utf-8",
        )

    @mock.patch.object(cleanup_solutions.subprocess, "run")
    def test_cleanup_finds_hidden_manifest_and_deduplicates_id(
        self, run: mock.Mock
    ) -> None:
        solution_id = "11111111-2222-4333-8444-555555555555"
        self.write_manifest("project/..uipx", solution_id)
        self.write_manifest("copy/duplicate.uipx", solution_id)
        run.return_value = mock.Mock(returncode=0, stdout="{}", stderr="")

        with mock.patch.dict(os.environ, {"BPMN_E2E_CLEANUP": "always"}):
            self.assertEqual(cleanup_solutions.main(), 0)

        run.assert_called_once_with(
            [
                "uip",
                "solution",
                "delete",
                solution_id,
                "--yes",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )

    @mock.patch.object(cleanup_solutions.subprocess, "run")
    def test_cleanup_accepts_already_absent_solution(self, run: mock.Mock) -> None:
        self.write_manifest(
            "project.uipx",
            "11111111-2222-4333-8444-555555555555",
        )
        run.return_value = mock.Mock(
            returncode=1,
            stdout=json.dumps(
                {
                    "Result": "Failure",
                    "Message": "Delete failed (404): Not Found",
                }
            ),
            stderr="",
        )

        with mock.patch.dict(os.environ, {"BPMN_E2E_CLEANUP": "always"}):
            self.assertEqual(cleanup_solutions.main(), 0)

        run.assert_called_once()

    @mock.patch.object(cleanup_solutions.subprocess, "run")
    def test_timeout_is_best_effort(self, run: mock.Mock) -> None:
        self.write_manifest(
            "project.uipx",
            "11111111-2222-4333-8444-555555555555",
        )
        run.side_effect = subprocess.TimeoutExpired(["uip"], 180)

        with mock.patch.dict(os.environ, {"BPMN_E2E_CLEANUP": "always"}):
            self.assertEqual(cleanup_solutions.main(), 0)

    @mock.patch.object(cleanup_solutions.subprocess, "run")
    def test_never_policy_preserves_solution(self, run: mock.Mock) -> None:
        self.write_manifest(
            "project.uipx",
            "11111111-2222-4333-8444-555555555555",
        )

        with mock.patch.dict(os.environ, {"BPMN_E2E_CLEANUP": "never"}):
            self.assertEqual(cleanup_solutions.main(), 0)

        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
