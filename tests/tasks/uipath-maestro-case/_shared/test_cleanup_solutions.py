"""Behavioral tests for Case e2e Studio Web solution cleanup."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("cleanup_solutions.py")
SPEC = importlib.util.spec_from_file_location("case_cleanup_solutions", SCRIPT)
assert SPEC and SPEC.loader
cleanup_solutions = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup_solutions)


class CleanupSolutionsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temporary.name)
        self.previous_cwd = Path.cwd()
        os.chdir(self.workdir)
        (self.workdir / "Case.uipx").write_text(
            json.dumps({"SolutionId": "11111111-2222-4333-8444-555555555555"}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        os.chdir(self.previous_cwd)
        self.temporary.cleanup()

    @mock.patch.object(cleanup_solutions.subprocess, "run")
    def test_cleanup_confirms_non_interactive_delete(self, run: mock.Mock) -> None:
        run.return_value = mock.Mock(returncode=0, stdout="{}", stderr="")

        with mock.patch.dict(os.environ, {"CASE_E2E_CLEANUP": "always"}):
            self.assertEqual(cleanup_solutions.main(), 0)

        run.assert_called_once_with(
            [
                "uip",
                "solution",
                "delete",
                "11111111-2222-4333-8444-555555555555",
                "--yes",
                "--output",
                "json",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

    @mock.patch.object(cleanup_solutions.subprocess, "run")
    def test_never_policy_preserves_solution(self, run: mock.Mock) -> None:
        with mock.patch.dict(os.environ, {"CASE_E2E_CLEANUP": "never"}):
            self.assertEqual(cleanup_solutions.main(), 0)

        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
