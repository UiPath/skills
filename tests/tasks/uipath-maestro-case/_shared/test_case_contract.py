"""Behavior tests for the read-only SDD -> Case contract checker."""

from __future__ import annotations

import json
import subprocess
import sys
from itertools import count
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
CHECKER = ROOT / "skills" / "uipath-maestro-case" / "scripts" / "check_case_contract.py"
SDD = (
    ROOT
    / "tests"
    / "tasks"
    / "uipath-maestro-case"
    / "build_from_planner_sdd"
    / "fixtures"
    / "sdd.md"
)


def run_checker(*args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    result = subprocess.run(
        [sys.executable, str(CHECKER), *args, "--output", "json"],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    return result, payload


def matching_caseplan() -> dict:
    sequence = count(1)

    def rule(rule_type: str, **extra: object) -> dict:
        return {"id": f"rule-{next(sequence)}", "rule": rule_type, **extra}

    task_one = {
        "id": "task-post-invoice",
        "type": "api-workflow",
        "displayName": "Post Invoice",
        "elementId": "stage-resolve-task-post-invoice",
        "isRequired": True,
        "shouldRunOnlyOnce": False,
        "entryConditions": [
            {
                "id": "condition-post-invoice",
                "displayName": "Entry Rule 1",
                "rules": [[rule("current-stage-entered")]],
            }
        ],
        "data": {},
    }
    task_two = {
        "id": "task-draft-notification",
        "type": "agent",
        "displayName": "Draft Notification",
        "elementId": "stage-resolve-task-draft-notification",
        "isRequired": True,
        "shouldRunOnlyOnce": False,
        "entryConditions": [
            {
                "id": "condition-draft-notification",
                "displayName": "Entry Rule 1",
                "rules": [[rule("current-stage-entered")]],
            }
        ],
        "data": {},
    }
    return {
        "id": "case-planner-returned",
        "version": "27.0.0",
        "name": "PlannerReturnedInvoiceCase",
        "description": (
            "Runs two existing tenant resources from a planner-authored SDD; "
            "identities deferred to the build."
        ),
        "metadata": {
            "caseIdentifier": "PRI",
            "caseIdentifierType": "constant",
            "caseAppEnabled": False,
            "caseDirectlyPassTaskOutputs": True,
            "caseExitRules": [
                {
                    "id": "case-exit",
                    "displayName": "Complete Rule 1",
                    "marksCaseComplete": True,
                    "rules": [[rule("required-stages-completed")]],
                }
            ],
        },
        "bindings": [],
        "variables": {
            "inputs": [],
            "outputs": [],
            "inputOutputs": [
                {
                    "id": "invoiceNumber",
                    "name": "invoiceNumber",
                    "type": "string",
                    "default": "INV-1042",
                    "custom": True,
                    "elementId": "root",
                },
                {
                    "id": "emailSubject",
                    "name": "emailSubject",
                    "type": "string",
                    "default": "Planner handoff",
                    "custom": True,
                    "elementId": "root",
                },
            ],
        },
        "nodes": [
            {
                "id": "stage-resolve",
                "type": "case-management:Stage",
                "data": {
                    "label": "Resolve Resources",
                    "description": (
                        "Invokes two resources after the build resolves them by the "
                        "names preserved in this SDD."
                    ),
                    "stageType": "primary",
                    "isRequired": True,
                    "entryConditions": [
                        {
                            "id": "stage-entry",
                            "displayName": "Entry Rule 1",
                            "isInterrupting": False,
                            "rules": [[rule("case-entered")]],
                        }
                    ],
                    "exitConditions": [
                        {
                            "id": "stage-exit",
                            "displayName": "Complete Rule 1",
                            "type": "exit-only",
                            "marksStageComplete": True,
                            "rules": [[rule("required-tasks-completed")]],
                        }
                    ],
                    "parentElement": {"id": "root", "type": "case-management:root"},
                    "tasks": [[task_one, task_two]],
                },
            },
            {
                "id": "trigger-manual",
                "type": "uipath.case.trigger",
                "data": {
                    "display": {"label": "User starts case"},
                    "parentElement": {"id": "root", "type": "case-management:root"},
                },
            },
        ],
        "edges": [],
        "layout": {},
    }


def test_inspect_sdd_returns_ordered_build_contract():
    result, payload = run_checker("inspect-sdd", "--sdd", str(SDD))

    assert result.returncode == 0, result.stderr
    assert payload["ok"] is True
    assert payload["contract"]["case"]["name"] == "PlannerReturnedInvoiceCase"
    assert [stage["name"] for stage in payload["contract"]["stages"]] == [
        "Resolve Resources"
    ]
    assert [task["name"] for task in payload["contract"]["stages"][0]["tasks"]] == [
        "Post Invoice",
        "Draft Notification",
    ]
    assert payload["contract"]["resources"] == [
        {
            "folder": None,
            "identity": None,
            "name": "FinancialPostingFunction",
            "stage": "Resolve Resources",
            "task": "Post Invoice",
            "taskType": "api-workflow",
        },
        {
            "folder": None,
            "identity": None,
            "name": "EmailDrafter",
            "stage": "Resolve Resources",
            "task": "Draft Notification",
            "taskType": "agent",
        },
    ]


def test_check_sdd_accepts_a_ready_planner_case_sdd():
    result, payload = run_checker("check-sdd", "--sdd", str(SDD))

    assert result.returncode == 0, result.stderr
    assert payload == {
        "command": "check-sdd",
        "findings": [],
        "ok": True,
        "summary": {
            "case": "PlannerReturnedInvoiceCase",
            "resources": 2,
            "stages": 1,
            "tasks": 2,
            "triggers": 1,
            "variables": 2,
        },
    }


def test_check_sdd_reports_stable_code_and_path_for_an_invalid_task_type(tmp_path: Path):
    broken = tmp_path / "sdd.md"
    broken.write_text(
        SDD.read_text(encoding="utf-8").replace(
            "**Type:** api-workflow", "**Type:** imaginary-workflow", 1
        ),
        encoding="utf-8",
    )

    result, payload = run_checker("check-sdd", "--sdd", str(broken))

    assert result.returncode == 1
    assert payload["ok"] is False
    assert {
        "code": "SDD-TASK-TYPE",
        "message": "unsupported task type 'imaginary-workflow'",
        "path": "stages[Resolve Resources].tasks[Post Invoice].type",
        "severity": "error",
    } in payload["findings"]


def test_check_sdd_rejects_an_intermediate_build_handoff(tmp_path: Path):
    broken = tmp_path / "sdd.md"
    broken.write_text(
        SDD.read_text(encoding="utf-8").replace(
            "| **Build handoff** | direct to `uipath-maestro-case` — no intermediate task file |",
            "| **Tasks file** | tasks/tasks.md |",
        ),
        encoding="utf-8",
    )

    result, payload = run_checker("check-sdd", "--sdd", str(broken))

    assert result.returncode == 1
    assert {
        "code": "SDD-HANDOFF-DIRECT",
        "message": "Case SDD must hand off directly to uipath-maestro-case",
        "path": "plannerHandoff.buildHandoff",
        "severity": "error",
    } in payload["findings"]


def test_check_sdd_rejects_numbered_and_duplicate_trigger_names(tmp_path: Path):
    broken = tmp_path / "sdd.md"
    broken.write_text(
        SDD.read_text(encoding="utf-8").replace(
            "| User starts case | Manual | User-initiated | N/A |",
            "| T02 | Manual | User-initiated | N/A |\n"
            "| T02 | Timer | Schedule | R/PT1H |",
        ),
        encoding="utf-8",
    )

    result, payload = run_checker("check-sdd", "--sdd", str(broken))

    assert result.returncode == 1
    codes = {finding["code"] for finding in payload["findings"]}
    assert {"SDD-TRIGGER-DUPLICATE", "SDD-TRIGGER-NAME"} <= codes


def test_check_sdd_enforces_variable_trigger_direction(tmp_path: Path):
    broken = tmp_path / "sdd.md"
    broken.write_text(
        SDD.read_text(encoding="utf-8").replace(
            '| emailSubject | Variable | string | | | "Planner handoff" | Subject passed to the agent. |',
            '| emailSubject | Out | string | User starts case | response.subject | "Planner handoff" | Subject passed to the agent. |',
        ),
        encoding="utf-8",
    )

    result, payload = run_checker("check-sdd", "--sdd", str(broken))

    assert result.returncode == 1
    assert {
        "code": "SDD-VARIABLE-SOURCE-DIRECTION",
        "message": "Out variables cannot declare sourceTriggers or sourceFields",
        "path": "variables[emailSubject]",
        "severity": "error",
    } in payload["findings"]


def test_check_parity_accepts_a_semantically_equivalent_caseplan(tmp_path: Path):
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(matching_caseplan()), encoding="utf-8")

    result, payload = run_checker(
        "check-parity", "--sdd", str(SDD), "--caseplan", str(plan_path)
    )

    assert result.returncode == 0, payload
    assert payload["ok"] is True
    assert payload["findings"] == []


def test_check_parity_reports_missing_and_changed_task_semantics(tmp_path: Path):
    plan = matching_caseplan()
    stage = plan["nodes"][0]["data"]
    stage["tasks"][0][0]["type"] = "process"
    stage["tasks"][0].pop()
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result, payload = run_checker(
        "check-parity", "--sdd", str(SDD), "--caseplan", str(plan_path)
    )

    assert result.returncode == 1
    assert payload["ok"] is False
    assert {
        "code": "PARITY-TASK-TYPE",
        "message": "expected 'api-workflow'; found 'process'",
        "path": "stages[Resolve Resources].tasks[Post Invoice].type",
        "severity": "error",
    } in payload["findings"]
    assert {
        "code": "PARITY-TASK-MISSING",
        "message": "task declared by the SDD is missing from caseplan.json",
        "path": "stages[Resolve Resources].tasks[Draft Notification]",
        "severity": "error",
    } in payload["findings"]


def test_check_parity_reports_trigger_type_and_extra_trigger(tmp_path: Path):
    plan = matching_caseplan()
    plan["nodes"][1]["data"]["inputs"] = {"serviceType": "timer"}
    plan["nodes"].append(
        {
            "id": "trigger-extra",
            "type": "uipath.case.trigger",
            "data": {"display": {"label": "Unexpected start"}},
        }
    )
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result, payload = run_checker(
        "check-parity", "--sdd", str(SDD), "--caseplan", str(plan_path)
    )

    assert result.returncode == 1
    assert {
        "code": "PARITY-TRIGGER-TYPE",
        "message": "expected 'manual'; found 'timer'",
        "path": "triggers[User starts case].type",
        "severity": "error",
    } in payload["findings"]
    assert {
        "code": "PARITY-TRIGGER-EXTRA",
        "message": "caseplan.json contains a trigger not declared by the SDD",
        "path": "triggers[Unexpected start]",
        "severity": "error",
    } in payload["findings"]


def test_check_parity_maps_planner_timer_type_to_runtime_timer(tmp_path: Path):
    timer_sdd = tmp_path / "sdd.md"
    timer_sdd.write_text(
        SDD.read_text(encoding="utf-8").replace(
            "| User starts case | Manual | User-initiated | N/A |",
            "| User starts case | Intsvc.TimerTrigger | Schedule | R/PT1H |",
        ),
        encoding="utf-8",
    )
    plan = matching_caseplan()
    plan["nodes"][1]["data"]["inputs"] = {"serviceType": "timer"}
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result, payload = run_checker(
        "check-parity", "--sdd", str(timer_sdd), "--caseplan", str(plan_path)
    )

    assert result.returncode == 0, payload
    assert payload["findings"] == []


def test_check_parity_rejects_parallel_tasks_split_across_task_sets(tmp_path: Path):
    plan = matching_caseplan()
    tasks = plan["nodes"][0]["data"]["tasks"][0]
    plan["nodes"][0]["data"]["tasks"] = [[tasks[0]], [tasks[1]]]
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result, payload = run_checker(
        "check-parity", "--sdd", str(SDD), "--caseplan", str(plan_path)
    )

    assert result.returncode == 1
    assert {
        "code": "PARITY-TASK-GROUP",
        "message": "parallel tasks with the same entry behavior must share one task set",
        "path": "stages[Resolve Resources].tasks",
        "severity": "error",
    } in payload["findings"]


def test_check_caseplan_rejects_authored_edges_and_duplicate_ids(tmp_path: Path):
    plan = matching_caseplan()
    plan["edges"] = [{"id": "edge-1", "source": "a", "target": "b"}]
    plan["nodes"][1]["id"] = plan["nodes"][0]["id"]
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result, payload = run_checker(
        "check-caseplan", "--caseplan", str(plan_path)
    )

    assert result.returncode == 1
    codes = {finding["code"] for finding in payload["findings"]}
    assert {"CASEPLAN-EDGES", "CASEPLAN-ID-DUPLICATE"} <= codes


def test_check_caseplan_rejects_illegal_rules_layout_and_formal_argument_ids(
    tmp_path: Path,
):
    plan = matching_caseplan()
    plan["nodes"][0]["position"] = {"x": 0, "y": 0}
    plan["nodes"][0]["data"]["entryConditions"][0]["rules"][0][0]["rule"] = (
        "current-stage-entered"
    )
    plan["variables"]["inputs"] = [
        {"id": "3invalid", "name": "incoming", "type": "string"}
    ]
    plan_path = tmp_path / "caseplan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    result, payload = run_checker("check-caseplan", "--caseplan", str(plan_path))

    assert result.returncode == 1
    codes = {finding["code"] for finding in payload["findings"]}
    assert {
        "CASEPLAN-LAYOUT-FIELD",
        "CASEPLAN-RULE-LEGALITY",
        "CASEPLAN-ARGUMENT-ID",
    } <= codes
