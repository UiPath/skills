"""Regression tests for high-level uipath-maestro-case eval contracts."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_SKILL = ROOT / "skills" / "uipath-maestro-case"
TASKS = ROOT / "tests" / "tasks" / "uipath-maestro-case"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class EvalContractTests(unittest.TestCase):
    def test_phase_zero_draft_only_path_is_explicit(self) -> None:
        skill = read(CASE_SKILL / "SKILL.md")
        phase_zero = read(CASE_SKILL / "references" / "phase-0-interview.md")
        loan_eval = read(
            TASKS / "phase_0_to_case" / "loan_origination" / "loan_origination.yaml"
        )

        for text in (skill, phase_zero, loan_eval):
            self.assertIn("draft-only", text)
            self.assertIn("sdd.draft.md", text)
            self.assertIn("do not read implementation docs", text.lower())

    def test_event_placeholder_preserves_authored_source_object(self) -> None:
        planning = read(
            CASE_SKILL / "references" / "plugins" / "triggers" / "event" / "planning.md"
        )
        implementation = read(
            CASE_SKILL
            / "references"
            / "plugins"
            / "triggers"
            / "event"
            / "impl-json.md"
        )

        for text in (planning, implementation):
            self.assertIn("preserve the authored source object", text)
            self.assertIn("source object: <object-name>", text)

    def test_registry_handoff_covers_all_non_connector_resource_tasks(self) -> None:
        planning = read(CASE_SKILL / "references" / "planning.md")

        for task_type in (
            "process",
            "agent",
            "rpa",
            "api-workflow",
            "action",
            "case-management",
        ):
            self.assertIn(f"`{task_type}`", planning)

        self.assertIn("selected.name", planning)
        self.assertIn("selected.folders[0].fullyQualifiedName", planning)
        self.assertIn("selected.entityKey", planning)
        self.assertIn("SDD aliases are search keys only", planning)

    def test_long_running_build_evals_stop_after_validate_passes(self) -> None:
        for task_file in (
            TASKS / "aged_invoice_structural" / "aged_invoice_structural.yaml",
            TASKS / "athena_cm_event" / "athena_cm_event.yaml",
            TASKS / "e2e_expense_runnable" / "expense_runnable_e2e.yaml",
        ):
            with self.subTest(task_file=task_file.name):
                task = read(task_file)
                self.assertIn("After the validate command passes, stop immediately", task)
                self.assertIn("do not continue into phase 5 or phase 6", task.lower())


if __name__ == "__main__":
    unittest.main()
