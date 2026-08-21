#!/usr/bin/env python3
"""Offline behavioral tests for the ContractExecution deterministic graders.

Builds a synthetic caseplan that restates the SDD's topology independently of
the graders' own tables, asserts the graders accept it, then mutates one fact
at a time and asserts each mutation is caught. The field-name grader gets its
own minimal plan covering the three runtime-only regressions it exists for.

Run: python3 -m unittest discover -s <this directory>
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parent
TOPOLOGY_CHECKER = ROOT / "check_contract_exec_case.py"
FIELDNAME_CHECKER = ROOT / "check_contract_exec_fieldnames.py"

CHECKING = "Checking the request"
COUNSEL = "Counsel review"
SENIOR = "Senior counsel review"
SIGNATURE = "Signature and filing"
EXECUTED = "Contract executed"
REJECTED = "Contract rejected"
WITHDRAWN = "Contract withdrawn"
INTERVENTION = "Overall SLA Intervention"

STAGE_IDS = {
    CHECKING: "stage-checking",
    COUNSEL: "stage-counsel",
    SENIOR: "stage-senior",
    SIGNATURE: "stage-signature",
    EXECUTED: "stage-executed",
    REJECTED: "stage-rejected",
    WITHDRAWN: "stage-withdrawn",
    INTERVENTION: "stage-intervention",
}
SLA_IDS = {
    "case": "sla-case",
    CHECKING: "sla-checking",
    COUNSEL: "sla-counsel",
    SENIOR: "sla-senior",
    SIGNATURE: "sla-signature",
    EXECUTED: "sla-executed",
    REJECTED: "sla-rejected",
    WITHDRAWN: "sla-withdrawn",
}
# (duration, unit, at-risk recipient, breach recipient). Union of recipients
# must equal the "Notify: ..." names in fixtures/sdd.md.
SLA_SPECS = {
    "case": (10, "d", "Legal Team", "Legal Operations"),
    CHECKING: (1, "d", "Legal Operations", "Legal Operations Lead"),
    COUNSEL: (4, "d", "Assigned Counsel", "Senior Counsel"),
    SENIOR: (2, "d", "Senior Counsel", "Legal Operations Lead"),
    SIGNATURE: (2, "d", "Legal Operations", "Legal Operations Lead"),
    EXECUTED: (1, "d", "Legal Operations", "Legal Operations Lead"),
    REJECTED: (1, "d", "Legal Operations", "Legal Operations Lead"),
    WITHDRAWN: (1, "d", "Legal Operations", "Legal Operations Lead"),
}

# stage -> [(display name, type, required, run-once, entry rule)]
STAGE_TASKS = {
    CHECKING: [
        ("Validate Request Details", "action", True, False, "current-stage-entered"),
        ("Pull Counterparty Records", "api-workflow", True, False, "current-stage-entered"),
        ("Analyze Draft for Unusual Clauses", "agent", False, False, "current-stage-entered"),
        ("Add More Documents", "action", False, False, "adhoc"),
        ("Handle Checking SLA Breach", "api-workflow", False, False, "sla"),
    ],
    COUNSEL: [
        ("Notify Assigned Counsel", "api-workflow", True, False, "runs-sequentially"),
        ("Counsel Decision", "action", True, False, "runs-sequentially"),
        ("Ask Business Team a Question", "api-workflow", False, False, "adhoc"),
        ("Order Outside Opinion", "action", False, False, "adhoc"),
        ("Handle Counsel SLA Breach", "api-workflow", False, False, "sla"),
    ],
    SENIOR: [
        ("Run Policy and Authority Check", "api-workflow", True, False, "current-stage-entered"),
        ("Compare Historical Positions", "agent", False, False, "adhoc"),
        ("Pull In Finance Controller", "action", False, False, "adhoc"),
        ("Senior Counsel Decision", "action", True, False, "selected-tasks-completed"),
        ("Handle Senior Counsel SLA Breach", "api-workflow", False, False, "sla"),
    ],
    SIGNATURE: [
        ("Prepare and Send Signature Packet", "api-workflow", True, True, "runs-sequentially"),
        ("Wait for Signature Result", "wait-for-connector", True, False, "runs-sequentially"),
        ("Open Obligation Tracking", "case-management", False, True, "adhoc"),
        ("Handle Signature SLA Breach", "api-workflow", False, False, "sla"),
    ],
    EXECUTED: [
        ("Deliver Executed Copy", "api-workflow", True, True, "runs-sequentially"),
        ("File Contract", "api-workflow", True, True, "runs-sequentially"),
        ("Handle Executed Wrap Up SLA Breach", "api-workflow", False, False, "sla"),
    ],
    REJECTED: [
        ("Notify Requester of Rejection", "api-workflow", True, True, "runs-sequentially"),
        ("Log Rejection Decision", "api-workflow", True, True, "runs-sequentially"),
        ("Handle Rejected Wrap Up SLA Breach", "api-workflow", False, False, "sla"),
    ],
    WITHDRAWN: [
        ("Confirm Withdrawal", "api-workflow", True, True, "runs-sequentially"),
        ("Tidy Up Open Work", "api-workflow", True, True, "runs-sequentially"),
        ("Handle Withdrawn Wrap Up SLA Breach", "api-workflow", False, False, "sla"),
    ],
    INTERVENTION: [
        ("Handle Overall SLA Breach", "api-workflow", True, True, "runs-sequentially"),
        ("General Counsel Review", "action", True, True, "runs-sequentially"),
    ],
}
# stage -> [(rule, source stage or None, interrupting)]
STAGE_ENTRIES = {
    CHECKING: [("case-entered", None, False), ("selected-stage-exited", COUNSEL, False)],
    COUNSEL: [("selected-stage-completed", CHECKING, False)],
    SENIOR: [("selected-stage-completed", COUNSEL, False)],
    SIGNATURE: [("selected-stage-completed", SENIOR, False)],
    EXECUTED: [("selected-stage-completed", SIGNATURE, False)],
    REJECTED: [
        ("selected-stage-exited", COUNSEL, True),
        ("selected-stage-exited", SENIOR, True),
        ("selected-stage-exited", SIGNATURE, True),
    ],
    WITHDRAWN: [("wait-for-connector", None, True)],
    INTERVENTION: [("sla-status-change", None, True)],
}


def _condition(rule: str, **fields: object) -> dict:
    return {"rules": [[{"id": f"rule-{rule}", "rule": rule, **fields}]]}


def _sla(key: str) -> dict:
    count, unit, at_risk, breached = SLA_SPECS[key]
    return {
        "id": SLA_IDS[key],
        "displayName": f"{key} SLA",
        "expression": "=js:true",
        "count": count,
        "unit": unit,
        "escalationRule": [
            {
                "action": {
                    "type": "notification",
                    "recipients": [{"scope": "UserGroup", "value": at_risk}],
                },
                "triggerInfo": {"type": "at-risk", "atRiskPercentage": 70},
            },
            {
                "action": {
                    "type": "notification",
                    "recipients": [{"scope": "UserGroup", "value": breached}],
                },
                "triggerInfo": {"type": "sla-breached"},
            },
        ],
    }


def _task(stage: str, spec: tuple) -> dict:
    name, task_type, required, run_once, entry = spec
    if entry == "sla":
        entry_condition = _condition("sla-status-change", slaId=SLA_IDS[stage])
    elif entry == "selected-tasks-completed":
        entry_condition = _condition("selected-tasks-completed", selectedTasksIds=["task-policy"])
    else:
        entry_condition = _condition(entry)
    return {
        "id": f"task-{abs(hash((stage, name))) % 10**10}",
        "type": task_type,
        "displayName": name,
        "isRequired": required,
        "shouldRunOnlyOnce": run_once,
        "data": {"name": "=bindings.b1", "folderPath": "=bindings.b2", "inputs": []},
        "entryConditions": [entry_condition],
        "exitConditions": [],
    }


def expected_caseplan() -> dict:
    nodes = [
        {
            "id": "trigger_1",
            "type": "uipath.case.trigger",
            "data": {"typeVersion": "1.0.0", "inputs": {"serviceType": "None"}},
        }
    ]
    for stage, task_specs in STAGE_TASKS.items():
        entries = []
        for rule, source, interrupting in STAGE_ENTRIES[stage]:
            fields: dict[str, object] = {}
            if source is not None:
                fields["selectedStageId"] = STAGE_IDS[source]
            if rule == "sla-status-change":
                fields["slaId"] = SLA_IDS["case"]
            entries.append(
                {**_condition(rule, **fields), "isInterrupting": interrupting}
            )
        exit_type = "return-to-origin" if stage == INTERVENTION else "exit-only"
        data: dict[str, object] = {
            "label": stage,
            "tasks": [[_task(stage, spec)] for spec in task_specs],
            "entryConditions": entries,
            "exitConditions": [
                {
                    **_condition("required-tasks-completed"),
                    "type": exit_type,
                    "marksStageComplete": True,
                }
            ],
        }
        if stage in SLA_SPECS:
            data["slaRules"] = [_sla(stage)]
        if stage in (REJECTED, WITHDRAWN, INTERVENTION):
            data["stageType"] = "secondary"
        nodes.append({"id": STAGE_IDS[stage], "type": "case-management:Stage", "data": data})

    return {
        "metadata": {
            "caseIdentifier": "CTR",
            "caseIdentifierType": "constant",
            "caseDirectlyPassTaskOutputs": True,
            "intsvcActivityConfig": "v2",
            "slaRules": [_sla("case")],
            "caseExitRules": [
                {**_condition("required-stages-completed"), "marksCaseComplete": True},
                {
                    **_condition(
                        "selected-stage-completed", selectedStageId=STAGE_IDS[REJECTED]
                    ),
                    "marksCaseComplete": False,
                },
                {
                    **_condition(
                        "selected-stage-completed", selectedStageId=STAGE_IDS[WITHDRAWN]
                    ),
                    "marksCaseComplete": False,
                },
            ],
        },
        "edges": [],
        "nodes": nodes,
    }


def fieldname_caseplan() -> dict:
    """Minimal plan exercising the three field-name / null-guard regressions."""
    signed_gate = (
        "=js:(String((vars.response2 || {}).request_body).indexOf('Declined') < 0) && "
        "(String((vars.response2 || {}).request_body).indexOf('Expired') < 0)"
    )
    webhook = {
        "id": "task-webhook",
        "type": "wait-for-connector",
        "displayName": "Wait for Signature Result",
        "data": {
            "serviceType": "Intsvc.WaitForEvent",
            "inputs": [],
            "outputs": [
                {
                    "name": "response",
                    "type": "jsonSchema",
                    "id": "response2",
                    "var": "response2",
                    "source": "=response",
                    "body": {
                        "type": "object",
                        "properties": {
                            "request_body": {"title": "Body", "type": "string"},
                            "request_headers": {"title": "Headers", "type": "string"},
                        },
                    },
                }
            ],
        },
        "entryConditions": [],
        "exitConditions": [],
    }
    decision = {
        "id": "task-senior-decision",
        "type": "action",
        "displayName": "Senior Counsel Decision",
        "data": {
            "inputs": [
                {
                    "name": "authorityLevel",
                    "value": "=js:(vars.response || {}).authorityLevel",
                },
                {
                    "name": "historicalDeviationFlags",
                    "value": "=js:(vars.analysisResult2 || {}).deviationFlags",
                },
                {
                    "name": "unusualClauses",
                    "value": "=js:(vars.analysisResult || {}).unusualClauses",
                },
            ],
            "outputs": [
                {"name": "riskFlags", "id": "riskFlags", "var": "policyRiskFlags",
                 "source": "=response.riskFlags"},
                {"name": "counterpartyProfile", "id": "counterpartyProfile",
                 "var": "counterpartyProfile", "source": "=response.counterpartyProfile"},
            ],
        },
        "entryConditions": [],
        "exitConditions": [],
    }
    return {
        "metadata": {"caseExitRules": []},
        "edges": [],
        "nodes": [
            {
                "id": "stage-signature",
                "type": "case-management:Stage",
                "data": {
                    "label": "Signature and filing",
                    "tasks": [[webhook], [decision]],
                    "entryConditions": [],
                    "exitConditions": [
                        {
                            "displayName": "Contract signed",
                            "rules": [
                                [
                                    {
                                        "rule": "required-tasks-completed",
                                        "conditionExpression": signed_gate,
                                    }
                                ]
                            ],
                            "type": "exit-only",
                            "marksStageComplete": True,
                        }
                    ],
                },
            }
        ],
    }


def run_checker(checker: Path, plan: dict) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as temporary:
        caseplan = (
            Path(temporary) / "ContractExecution" / "ContractExecution" / "caseplan.json"
        )
        caseplan.parent.mkdir(parents=True)
        caseplan.write_text(json.dumps(plan), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(checker)],
            cwd=temporary,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class TopologyCheckerTests(unittest.TestCase):
    def _run(self, plan: dict) -> subprocess.CompletedProcess:
        return run_checker(TOPOLOGY_CHECKER, plan)

    def _stage(self, plan: dict, label: str) -> dict:
        return next(
            node for node in plan["nodes"] if (node.get("data") or {}).get("label") == label
        )

    def test_accepts_expected_structure(self) -> None:
        result = self._run(copy.deepcopy(expected_caseplan()))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_missing_stage(self) -> None:
        plan = expected_caseplan()
        plan["nodes"] = [
            node
            for node in plan["nodes"]
            if (node.get("data") or {}).get("label") != WITHDRAWN
        ]

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(f"missing stage {WITHDRAWN!r}", result.stdout + result.stderr)

    def test_rejects_extra_task(self) -> None:
        plan = expected_caseplan()
        stage = self._stage(plan, EXECUTED)
        stage["data"]["tasks"].append(
            [_task(EXECUTED, ("Unexpected Task", "api-workflow", False, False, "adhoc"))]
        )

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected exactly 30 tasks, got 31", result.stdout + result.stderr)

    def test_rejects_missing_corrections_loop(self) -> None:
        plan = expected_caseplan()
        stage = self._stage(plan, CHECKING)
        stage["data"]["entryConditions"] = [
            condition
            for condition in stage["data"]["entryConditions"]
            if condition["rules"][0][0]["rule"] != "selected-stage-exited"
        ]

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            f"missing condition-derived transition {COUNSEL!r} -> {CHECKING!r}",
            result.stdout + result.stderr,
        )

    def test_rejects_non_interrupting_secondary_entry(self) -> None:
        plan = expected_caseplan()
        stage = self._stage(plan, REJECTED)
        stage["data"]["entryConditions"][0]["isInterrupting"] = False

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must be interrupting", result.stdout + result.stderr)

    def test_rejects_completing_withdrawn_case_exit(self) -> None:
        plan = expected_caseplan()
        plan["metadata"]["caseExitRules"][2]["marksCaseComplete"] = True

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("marksCaseComplete must be false", result.stdout + result.stderr)

    def test_rejects_intervention_lane_without_return_to_origin(self) -> None:
        plan = expected_caseplan()
        stage = self._stage(plan, INTERVENTION)
        stage["data"]["exitConditions"][0]["type"] = "exit-only"

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exactly one return-to-origin exit", result.stdout + result.stderr)

    def test_rejects_sla_handler_pointing_at_another_stages_sla(self) -> None:
        plan = expected_caseplan()
        stage = self._stage(plan, EXECUTED)
        handler = next(
            lane[0]
            for lane in stage["data"]["tasks"]
            if lane[0]["displayName"] == "Handle Executed Wrap Up SLA Breach"
        )
        handler["entryConditions"][0]["rules"][0][0]["slaId"] = SLA_IDS[CHECKING]

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must trigger on its own stage's SLA", result.stdout + result.stderr)

    def test_rejects_dropped_run_once_flag(self) -> None:
        plan = expected_caseplan()
        stage = self._stage(plan, SIGNATURE)
        packet = next(
            lane[0]
            for lane in stage["data"]["tasks"]
            if lane[0]["displayName"] == "Prepare and Send Signature Packet"
        )
        packet["shouldRunOnlyOnce"] = False

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("run-once task set differs", result.stdout + result.stderr)

    def test_rejects_dropped_direct_task_output_passing(self) -> None:
        plan = expected_caseplan()
        plan["metadata"]["caseDirectlyPassTaskOutputs"] = False

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("caseDirectlyPassTaskOutputs", result.stdout + result.stderr)

    def test_rejects_wrong_case_identifier(self) -> None:
        plan = expected_caseplan()
        plan["metadata"]["caseIdentifier"] = "EXP"

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("constant prefix 'CTR'", result.stdout + result.stderr)

    def test_rejects_case_id_reference_used_as_identifier(self) -> None:
        """The SDD's task-input case-ID reference is not the case identifier."""
        plan = expected_caseplan()
        plan["metadata"]["caseIdentifier"] = "=metadata.ExternalId"
        plan["metadata"]["caseIdentifierType"] = "external"

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("does not configure the case identifier", result.stdout + result.stderr)


class FieldNameCheckerTests(unittest.TestCase):
    def _run(self, plan: dict) -> subprocess.CompletedProcess:
        return run_checker(FIELDNAME_CHECKER, plan)

    def test_accepts_sdd_casing_and_guards(self) -> None:
        result = self._run(copy.deepcopy(fieldname_caseplan()))

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_pascal_cased_condition_property(self) -> None:
        plan = fieldname_caseplan()
        rule = plan["nodes"][0]["data"]["exitConditions"][0]["rules"][0][0]
        rule["conditionExpression"] = rule["conditionExpression"].replace(
            ").request_body", ").RequestBody"
        )

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the SDD declares 'request_body'", result.stdout + result.stderr)

    def test_accepts_optional_chaining(self) -> None:
        """`vars.X?.Y` is the preferred guard form; the older `(vars.X || {}).Y`
        must keep passing too (existing plans use it)."""
        plan = fieldname_caseplan()
        decision = plan["nodes"][0]["data"]["tasks"][1][0]
        decision["data"]["inputs"][0]["value"] = "=js:vars.response?.authorityLevel"
        decision["data"]["inputs"][1]["value"] = "=js:vars.analysisResult2?.deviationFlags"
        rule = plan["nodes"][0]["data"]["exitConditions"][0]["rules"][0][0]
        rule["conditionExpression"] = rule["conditionExpression"].replace(
            "(vars.response2 || {}).request_body", "vars.response2?.request_body"
        )

        result = self._run(plan)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_unguarded_dotted_access(self) -> None:
        plan = fieldname_caseplan()
        decision = plan["nodes"][0]["data"]["tasks"][1][0]
        decision["data"]["inputs"][1]["value"] = "=js:vars.analysisResult2.deviationFlags"

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unguarded dotted access", result.stdout + result.stderr)

    def test_rejects_pascal_cased_extract_source(self) -> None:
        plan = fieldname_caseplan()
        decision = plan["nodes"][0]["data"]["tasks"][1][0]
        decision["data"]["outputs"][0]["source"] = "=response.RiskFlags"

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the SDD declares 'riskFlags'", result.stdout + result.stderr)

    def test_rejects_pascal_cased_event_schema_keys(self) -> None:
        plan = fieldname_caseplan()
        webhook = plan["nodes"][0]["data"]["tasks"][0][0]
        properties = webhook["data"]["outputs"][0]["body"]["properties"]
        webhook["data"]["outputs"][0]["body"]["properties"] = {
            "RequestBody": properties["request_body"],
            "RequestHeaders": properties["request_headers"],
        }

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("event output schema property keys differ", result.stdout + result.stderr)

    def test_rejects_dropped_gate_expression(self) -> None:
        plan = fieldname_caseplan()
        rule = plan["nodes"][0]["data"]["exitConditions"][0]["rules"][0][0]
        rule.pop("conditionExpression")

        result = self._run(plan)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("the caseplan never does", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
