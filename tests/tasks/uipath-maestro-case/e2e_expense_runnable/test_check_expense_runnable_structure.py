"""Unit tests for the ExpenseReimbursementRunnable structural checker."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

# The checker lives in the suite's `_shared`; `_shared.case_check` resolves from
# the suite root.
SUITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SUITE, "_shared"))
sys.path.insert(0, SUITE)

from check_expense_runnable_structure import (  # noqa: E402
    _assert_required_external_bindings,
)
from _shared.case_check import selected_stage_ids, stage_transitions  # noqa: E402

TURN_TIMEOUT = 4800


class RunLimitTests(unittest.TestCase):
    def test_task_timeout_leaves_grading_room_after_the_full_turn(self) -> None:
        task = yaml.safe_load(
            Path(__file__).with_name("expense_runnable_e2e.yaml").read_text(encoding="utf-8")
        )
        limits = task["run_limits"]
        criteria = sum(
            criterion.get("timeout", 0) for criterion in task["success_criteria"]
        )
        self.assertEqual(limits["turn_timeout"], TURN_TIMEOUT)
        self.assertGreaterEqual(
            limits["task_timeout"], limits["turn_timeout"] + criteria
        )


class StageTransitionTests(unittest.TestCase):
    def test_selected_stage_ids_prefers_v30_plural_and_accepts_legacy_singular(self) -> None:
        self.assertEqual(
            selected_stage_ids({"selectedStageIds": ["first", "second"]}),
            ["first", "second"],
        )
        self.assertEqual(selected_stage_ids({"selectedStageId": "legacy"}), ["legacy"])

    def test_reads_v30_plural_and_legacy_singular_stage_ids(self) -> None:
        plan = {
            "nodes": [
                {
                    "id": "target",
                    "type": "case-management:Stage",
                    "data": {
                        "entryConditions": [
                            {
                                "rules": [
                                    [
                                        {
                                            "rule": "selected-stage-completed",
                                            "selectedStageIds": ["first", "second"],
                                        },
                                        {
                                            "rule": "selected-stage-exited",
                                            "selectedStageId": "legacy",
                                        },
                                    ]
                                ]
                            }
                        ]
                    },
                }
            ]
        }

        self.assertEqual(
            stage_transitions(plan),
            [
                {"source": "first", "target": "target"},
                {"source": "legacy", "target": "target"},
                {"source": "second", "target": "target"},
            ],
        )


def _valid_resources() -> list[dict]:
    """bindings_v2.json resources whose deployed names all match the tenant."""
    return [
        {
            "key": "Shared/uipath-agents/WeatherAPI.WeatherAPI",
            "value": {"name": {"defaultValue": "WeatherAPI"}},
        },
        {
            "key": "Shared/uipath-maestro-flow/CountLetters CodedAgent.CountLetters",
            "value": {"name": {"defaultValue": "CountLetters"}},
        },
        {
            "key": "Shared/uipath-agents/ProcurementProcess.ProcurementProcess",
            "value": {"name": {"defaultValue": "ProcurementProcess"}},
        },
        {
            "key": "Shared/uipath-maestro-flow/HelpDeskLookup RPA.HelpDeskLookup",
            "value": {"name": {"defaultValue": "HelpDeskLookup"}},
        },
        {
            "key": "Shared/uipath-maestro-case/CaseTest.Maestro Case",
            "value": {"name": {"defaultValue": "Maestro Case"}},
        },
    ]


class ResourceBindingTests(unittest.TestCase):
    def test_accepts_runnable_resource_display_names(self) -> None:
        _assert_required_external_bindings({"resources": _valid_resources()})

    def test_rejects_resource_alias_in_place_of_display_name(self) -> None:
        # The SDD alias "CaseTest" is not the deployed name "Maestro Case".
        resources = _valid_resources()
        resources[4]["value"]["name"]["defaultValue"] = "CaseTest"
        with self.assertRaisesRegex(SystemExit, "Maestro Case"):
            _assert_required_external_bindings({"resources": resources})


class BindingsLocationTests(unittest.TestCase):
    def test_bindings_are_read_beside_the_discovered_plan(self) -> None:
        checker = Path(__file__).resolve().parents[1] / "_shared" / "check_expense_runnable_structure.py"
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "ExpenseReimbursementRunnableSolution" / "ExpenseReimbursementRunnable"
            project.mkdir(parents=True)
            (project / "caseplan.json").write_text("{}", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(checker)], cwd=directory, capture_output=True, text=True
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            os.path.join("ExpenseReimbursementRunnableSolution", "ExpenseReimbursementRunnable", "bindings_v2.json"),
            result.stderr,
        )
