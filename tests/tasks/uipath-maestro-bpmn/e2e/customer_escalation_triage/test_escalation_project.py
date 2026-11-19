"""Unit tests for escalation_project: the CLI layout the prompt states, or the Studio Web export."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import escalation_project  # noqa: E402


def _project(root: Path, relative: str) -> Path:
    file = root / relative
    file.parent.mkdir(parents=True)
    file.write_text("<definitions/>", encoding="utf-8")
    (file.parent / "project.uiproj").write_text("{}", encoding="utf-8")
    return file


class BpmnFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._cwd = os.getcwd()
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        os.chdir(self.root)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self._tmp.cleanup()

    def test_cli_layout_the_prompt_states(self) -> None:
        _project(self.root, "CustomerEscalationTriageSolution/CustomerEscalationTriage/CustomerEscalationTriage.bpmn")
        self.assertEqual(escalation_project.bpmn_file(), escalation_project.CLI_BPMN_FILE)

    def test_studio_web_export(self) -> None:
        _project(self.root, "CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn")
        # The Studio Web flavor's undo copy is scratch and never graded.
        _project(self.root, "CustomerEscalationTriage/CustomerEscalationTriage/.flow-sdk/original/Process.bpmn")
        self.assertEqual(
            escalation_project.bpmn_file(),
            Path("CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn"),
        )

    def test_cli_named_file_off_the_stated_layout_still_fails(self) -> None:
        _project(self.root, "Elsewhere/CustomerEscalationTriage/CustomerEscalationTriage.bpmn")
        with self.assertRaises(SystemExit) as raised:
            escalation_project.bpmn_file()
        self.assertIn("layout the prompt states", str(raised.exception.code))

    def test_live_run_copy_is_excluded(self) -> None:
        _project(self.root, "CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn")
        _project(self.root, "customer-escalation-live/Eval/CustomerEscalationTriage/Process.bpmn")
        self.assertEqual(
            escalation_project.bpmn_file(exclude_under=[Path("customer-escalation-live")]),
            Path("CustomerEscalationTriage/CustomerEscalationTriage/Process.bpmn"),
        )

    def test_nothing_submitted(self) -> None:
        with self.assertRaises(SystemExit):
            escalation_project.bpmn_file()


if __name__ == "__main__":
    unittest.main()
