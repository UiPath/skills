#!/usr/bin/env python3
"""Offline behavioral tests for the CM-Golden deterministic graders."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
TOPOLOGY_CHECKER = ROOT / "check_cm_golden_case.py"


def condition(rule_name: str, **rule_fields: object) -> dict:
    return {"rules": [[{"rule": rule_name, **rule_fields}]]}


def task(
    task_id: str,
    task_type: str,
    display_name: str,
    *,
    duration: str | None = None,
    run_once: bool = False,
) -> dict:
    data = {"duration": duration} if duration else {}
    return {
        "id": task_id,
        "type": task_type,
        "displayName": display_name,
        "shouldRunOnlyOnce": run_once,
        "data": data,
        "entryConditions": [],
        "exitConditions": [],
    }


def stage(
    number: int,
    tasks: list[dict],
    *,
    label: str | None = None,
    secondary: bool = False,
    entry_conditions: list[dict] | None = None,
) -> dict:
    data = {
        "label": label or f"Stage {number}",
        "tasks": [[item] for item in tasks],
        "entryConditions": entry_conditions or [],
        "exitConditions": [],
    }
    if secondary:
        data["stageType"] = "secondary"
    return {
        "id": f"stage-{number}",
        "type": "case-management:Stage",
        "data": data,
    }


def expected_caseplan() -> dict:
    stages = [
        stage(
            1,
            [
                task("task-1-agent", "agent", "Analyze Expense Request"),
                task("task-1-process", "process", "Process Expense Request"),
                task("task-1-rpa", "rpa", "Record Expense via RPA"),
            ],
        ),
        stage(
            2,
            [
                task("task-2-action", "action", "Manager Approval"),
                task(
                    "task-2-timer-once",
                    "wait-for-timer",
                    "Wait for timer - S2 run once",
                    duration="PT20S",
                    run_once=True,
                ),
                task("task-2-api", "api-workflow", "Call Expense API"),
                task(
                    "task-2-timer-adhoc",
                    "wait-for-timer",
                    "Wait for timer - S2 adhoc",
                    duration="PT10S",
                ),
            ],
            entry_conditions=[
                condition("selected-stage-completed", selectedStageId="stage-1")
            ],
        ),
        stage(
            3,
            [
                task("task-3-webhook", "wait-for-connector", "Wait for HTTP Webhook"),
                task("task-3-email", "execute-connector-activity", "List Emails"),
                task("task-3-case", "case-management", "Start Child Case"),
            ],
            entry_conditions=[
                condition("selected-stage-completed", selectedStageId="stage-2")
            ],
        ),
        stage(
            4,
            [task("task-4-action", "action", "Rework Approval")],
            label="Stage 4 - return to origin",
            secondary=True,
            entry_conditions=[
                condition("selected-stage-exited", selectedStageId="stage-2")
            ],
        ),
        stage(
            5,
            [
                task(
                    "task-5-timer",
                    "wait-for-timer",
                    "Wait for timer - S5",
                    duration="PT20M",
                )
            ],
            label="Stage 5 - connector entry",
        ),
        stage(
            6,
            [
                task(
                    "task-6-timer",
                    "wait-for-timer",
                    "Timer to be interrupted",
                    duration="PT5S",
                )
            ],
            label="Stage 6 - to be interrupted",
            entry_conditions=[
                condition("selected-stage-completed", selectedStageId="stage-3")
            ],
        ),
        stage(
            7,
            [task("task-7-timer", "wait-for-timer", "Wait for timer - S7")],
            label="Stage 7 - user select",
        ),
        stage(
            8,
            [task("task-8-timer", "wait-for-timer", "Wait for timer - S8")],
            entry_conditions=[
                condition("selected-stage-completed", selectedStageId="stage-7")
            ],
        ),
    ]
    return {
        "metadata": {
            "caseIdentifier": "EXP",
            "caseDirectlyPassTaskOutputs": True,
            "intsvcActivityConfig": "v2",
            "caseExitRules": [
                {
                    **condition("required-stages-completed"),
                    "marksCaseComplete": True,
                },
                {
                    **condition(
                        "selected-stage-completed", selectedStageId="stage-4"
                    ),
                    "marksCaseComplete": False,
                },
            ],
            "slaRules": [
                {
                    "count": 1,
                    "unit": "h",
                    "escalationRule": [
                        {
                            "triggerInfo": {
                                "type": "at-risk",
                                "atRiskPercentage": 70,
                            },
                            "recipient": "song.zhao@uipath.com",
                        },
                        {"triggerInfo": {"type": "breached"}},
                    ],
                }
            ],
        },
        "nodes": [
            {
                "id": "manual-trigger",
                "type": "case-management:Trigger",
                "data": {"uipath": {"serviceType": "Manual"}},
            },
            *stages,
        ],
    }


def run_topology_checker(plan: dict) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary:
        caseplan = (
            Path(temporary)
            / "CMGoldenExpense"
            / "CMGoldenExpense"
            / "caseplan.json"
        )
        caseplan.parent.mkdir(parents=True)
        caseplan.write_text(json.dumps(plan), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(TOPOLOGY_CHECKER)],
            cwd=temporary,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class CMGoldenCheckerTests(unittest.TestCase):
    def test_topology_checker_accepts_expected_structure(self) -> None:
        result = run_topology_checker(copy.deepcopy(expected_caseplan()))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_topology_checker_rejects_missing_stage(self) -> None:
        plan = expected_caseplan()
        plan["nodes"] = [
            node
            for node in plan["nodes"]
            if (node.get("data") or {}).get("label") != "Stage 8"
        ]

        result = run_topology_checker(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing stage 'Stage 8'", result.stdout + result.stderr)

    def test_topology_checker_rejects_missing_task(self) -> None:
        plan = expected_caseplan()
        stage_1 = next(
            node
            for node in plan["nodes"]
            if (node.get("data") or {}).get("label") == "Stage 1"
        )
        stage_1["data"]["tasks"].pop()

        result = run_topology_checker(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected exactly 15 tasks, got 14", result.stdout + result.stderr)

    def test_topology_checker_rejects_extra_task(self) -> None:
        plan = expected_caseplan()
        stage_1 = next(
            node
            for node in plan["nodes"]
            if (node.get("data") or {}).get("label") == "Stage 1"
        )
        stage_1["data"]["tasks"].append(
            [task("unexpected-task", "agent", "Unexpected Task")]
        )

        result = run_topology_checker(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected exactly 15 tasks, got 16", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
