#!/usr/bin/env python3
"""Behavioral tests for the Athena CM event-case grader scripts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
SDD_CHECK = ROOT / "check_athena_cm_event_sdd.py"
CASE_CHECK = ROOT / "check_athena_cm_event_case.py"


def run(script: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def task(
    task_id: str,
    process_name: str,
    *,
    required: bool,
    run_once: bool,
    entry_conditions: list[dict] | None = None,
) -> dict:
    return {
        "id": task_id,
        "type": "process",
        "isRequired": required,
        "shouldRunOnlyOnce": run_once,
        "data": {"name": f"=bindings.{task_id}_name", "folderPath": f"=bindings.{task_id}_folder"},
        "entryConditions": entry_conditions or [],
    }


def stage(
    stage_id: str,
    label: str,
    tasks: list[dict],
    *,
    entry_conditions: list[dict] | None = None,
    exit_conditions: list[dict] | None = None,
) -> dict:
    return {
        "id": stage_id,
        "type": "case-management:Stage",
        "data": {
            "label": label,
            "entryConditions": entry_conditions or [],
            "exitConditions": exit_conditions or [],
            "tasks": [[item] for item in tasks],
        },
    }


class AthenaCheckersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workdir = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_sdd(self, path: Path) -> None:
        path.write_text(
            """# Athena Event Case

## Case Arguments

| Name | Direction | Type |
|---|---|---|
| InstanceExternalId | In | string |
| eventPayload | In | object |

### Stage A: StageA

| Task | Required | Run only once |
|---|---|---|
| StageATask1 | Yes | No |
| StageATask2 | Yes | Yes |

StageATask2 uses selected-tasks-completed after StageATask1.

### Stage B: StageB

| Task | Required | Run only once |
|---|---|---|
| StageBTask1 | No | No |
| StageBTask2 | Yes | No |

Stage B exits on required-tasks-completed.

### Stage C: StageC

| Task | Required | Run only once |
|---|---|---|
| StageCTask1 | No | Yes |
| StageCTask2 | No | Yes |
| StageCTask3 | Yes | Yes |

Stage C enters after selected-stage-completed StageB; StageCTask1 uses
current-stage-entered; Stage C exits on required-tasks-completed. The case
closes on required-stages-completed.

""",
            encoding="utf-8",
        )

    def write_caseplan(self, *, stage_c_task_3_once: bool = True) -> None:
        a1 = task("a1", "StageATask1", required=True, run_once=False)
        a2 = task(
            "a2",
            "StageATask2",
            required=True,
            run_once=True,
            entry_conditions=[
                {"rules": [[{"rule": "selected-tasks-completed", "selectedTasksIds": ["a1"]}]]}
            ],
        )
        b1 = task("b1", "StageBTask1", required=False, run_once=False)
        b2 = task("b2", "StageBTask2", required=True, run_once=False)
        c1 = task(
            "c1",
            "StageCTask1",
            required=False,
            run_once=True,
            entry_conditions=[{"rules": [[{"rule": "current-stage-entered"}]]}],
        )
        c2 = task("c2", "StageCTask2", required=False, run_once=True)
        c3 = task("c3", "StageCTask3", required=True, run_once=stage_c_task_3_once)
        stage_a = stage("stage-a", "StageA", [a1, a2])
        stage_b = stage(
            "stage-b",
            "StageB",
            [b1, b2],
            exit_conditions=[
                {"rules": [[{"rule": "required-tasks-completed"}]], "marksStageComplete": True}
            ],
        )
        stage_c = stage(
            "stage-c",
            "StageC",
            [c1, c2, c3],
            entry_conditions=[
                {"rules": [[{"rule": "selected-stage-completed", "selectedStageId": "stage-b"}]]}
            ],
            exit_conditions=[
                {"rules": [[{"rule": "required-tasks-completed"}]], "marksStageComplete": True}
            ],
        )
        bindings = []
        for task_id, name in {
            "a1": "StageATask1", "a2": "StageATask2", "b1": "StageBTask1",
            "b2": "StageBTask2", "c1": "StageCTask1", "c2": "StageCTask2",
            "c3": "StageCTask3",
        }.items():
            bindings.extend([
                {"id": f"{task_id}_name", "default": name},
                {"id": f"{task_id}_folder", "default": "Shared"},
            ])
        plan = {
            "version": "27.0.0",
            "name": "AthenaCMEventCase",
            "metadata": {
                "caseIdentifier": "=vars.instanceExternalId",
                "caseIdentifierType": "external",
                "caseExitRules": [
                    {"rules": [[{"rule": "required-stages-completed"}]], "marksCaseComplete": True}
                ],
            },
            "bindings": bindings,
            "variables": {
                "inputs": [
                    {"id": "instanceExternalId", "name": "InstanceExternalId", "type": "string"},
                    {"id": "eventPayload", "name": "eventPayload", "type": "jsonSchema"},
                ],
                "outputs": [],
                "inputOutputs": [],
            },
            "nodes": [
                {
                    "id": "trigger",
                    "type": "uipath.case.trigger",
                    "data": {"inputs": {"serviceType": "Intsvc.EventTrigger"}},
                },
                stage_a,
                stage_b,
                stage_c,
            ],
            "edges": [],
            "layout": {},
        }
        caseplan = self.workdir / "AthenaCMEventCase" / "AthenaCMEventCase" / "caseplan.json"
        caseplan.parent.mkdir(parents=True)
        caseplan.write_text(json.dumps(plan), encoding="utf-8")

    def test_sdd_checker_accepts_complete_fixture(self) -> None:
        self.write_sdd(self.workdir / "sdd.md")
        result = run(SDD_CHECK, self.workdir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_sdd_checker_accepts_topology_without_external_router(self) -> None:
        self.write_sdd(self.workdir / "sdd.md")
        result = run(SDD_CHECK, self.workdir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_case_checker_accepts_expected_structure(self) -> None:
        self.write_caseplan()
        result = run(CASE_CHECK, self.workdir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_case_checker_rejects_wrong_run_only_once_flag(self) -> None:
        self.write_caseplan(stage_c_task_3_once=False)
        result = run(CASE_CHECK, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("StageCTask3", result.stdout + result.stderr)

    def test_case_checker_rejects_completion_mark_on_a_different_rule(self) -> None:
        self.write_caseplan()
        caseplan = self.workdir / "AthenaCMEventCase" / "AthenaCMEventCase" / "caseplan.json"
        plan = json.loads(caseplan.read_text(encoding="utf-8"))
        stage_b = next(node for node in plan["nodes"] if node["id"] == "stage-b")
        stage_b["data"]["exitConditions"][0]["marksStageComplete"] = False
        stage_b["data"]["exitConditions"].append(
            {"rules": [[{"rule": "selected-tasks-completed"}]], "marksStageComplete": True}
        )
        caseplan.write_text(json.dumps(plan), encoding="utf-8")
        result = run(CASE_CHECK, self.workdir)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("StageB", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
