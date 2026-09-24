#!/usr/bin/env python3
"""Behavioral tests for the SupplierOnboarding grader scripts.

Builds a synthetic caseplan that satisfies every grader, then mutates one fact
at a time to prove each grader actually rejects the defect it claims to catch.
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import supplier_onboarding_expected as E  # noqa: E402

TOPOLOGY = ROOT / "check_supplier_onboarding_topology.py"
TASKS = ROOT / "check_supplier_onboarding_tasks.py"
SLA = ROOT / "check_supplier_onboarding_sla.py"
BINDINGS = ROOT / "check_supplier_onboarding_bindings.py"
SDD = ROOT / "check_supplier_onboarding_sdd.py"
FIXTURE_SDD = ROOT / "fixtures" / "sdd.md"

VARIABLE_TYPES = {
    "expectedAnnualSpend": "float",
    "submissionDate": "datetime",
    **{name: "file" for name in E.FILE_VARIABLES},
}


def condition(cid: str, rule: str, *, expression: str | None = None, **fields) -> dict:
    rule_body = {"id": f"Rule_{cid}", "rule": rule, **fields}
    body: dict = {
        "id": f"Condition_{cid}",
        "displayName": f"{rule} {cid}",
        "rules": [[rule_body]],
    }
    if expression is not None:
        body["conditionExpression"] = f"=js:{expression}"
    return body


def escalations(prefix: str, title: str) -> list[dict]:
    recipients = [{"scope": "UserGroup", "target": "group-uuid", "value": "Procurement"}]
    return [
        {
            "id": f"esc_{prefix}_risk",
            "displayName": f"{title} at risk",
            "triggerInfo": {"type": "at-risk", "atRiskPercentage": E.AT_RISK_PERCENTAGE},
            "action": {"type": "notification", "recipients": recipients},
        },
        {
            "id": f"esc_{prefix}_breach",
            "displayName": f"{title} breached",
            "triggerInfo": {"type": "sla-breached"},
            "action": {"type": "notification", "recipients": recipients},
        },
    ]


def build_plan() -> dict:
    stage_ids = {label: f"Stage_{index}" for index, label in enumerate(E.ALL_STAGES)}
    sla_ids = {label: f"sla_{index}" for index, label in enumerate(E.ALL_STAGES)}
    root_sla = "sla_root"

    bindings: list[dict] = []
    binding_ids: dict[str, tuple[str, str]] = {}
    for index, (resource_name, kind) in enumerate(sorted(_resource_kinds().items())):
        resource, sub_type = E.BINDING_CONTRACT[kind]
        folder = E.RESOURCE_FOLDERS[resource_name]
        key = f"{folder}.{resource_name}"
        name_id, folder_id = f"bn{index}", f"bf{index}"
        binding_ids[resource_name] = (name_id, folder_id)
        for binding_id, attribute, default in (
            (name_id, "name", resource_name),
            (folder_id, "folderPath", folder),
        ):
            entry = {
                "id": binding_id,
                "name": attribute,
                "type": "string",
                "resource": resource,
                "resourceKey": key,
                "default": default,
                "propertyAttribute": attribute,
            }
            if sub_type:
                entry["resourceSubType"] = sub_type
            bindings.append(entry)
    bindings.extend(
        [
            {
                "id": "bconn",
                "name": "ConnectionId",
                "type": "string",
                "resource": "Connection",
                "resourceKey": E.CONNECTION_ID,
                "default": E.CONNECTION_ID,
                "propertyAttribute": "ConnectionId",
            },
            {
                "id": "bconnf",
                "name": "folderKey",
                "type": "string",
                "resource": "Connection",
                "resourceKey": E.CONNECTION_ID,
                "default": "Shared/uipath-maestro-case",
                "propertyAttribute": "folderKey",
            },
        ]
    )

    # -- tasks: ids first so sibling selectors resolve ------------------------
    counter = 0
    tasks: dict[str, dict[str, dict]] = {}
    for label in E.ALL_STAGES:
        tasks[label] = {}
        for spec in E.TASKS[label]:
            counter += 1
            task_id = f"t{counter:08d}"
            tasks[label][spec["name"]] = {
                "id": task_id,
                "elementId": f"{stage_ids[label]}-{task_id}",
                "displayName": spec["name"],
                "type": spec["type"],
                "isRequired": spec["required"],
                "shouldRunOnlyOnce": spec["run_once"],
                "data": _task_data(spec, binding_ids),
                "entryConditions": [],
            }

    for label in E.ALL_STAGES:
        for spec in E.TASKS[label]:
            task = tasks[label][spec["name"]]
            task["entryConditions"] = _entry_conditions(
                spec, tasks[label], sla_ids[label], root_sla
            )

    nodes: list[dict] = [
        {
            "id": "trigger_1",
            "type": "uipath.case.trigger",
            "data": {
                "display": {"label": "Manual"},
                "inputs": {"serviceType": "None"},
            },
        }
    ]
    for label in E.ALL_STAGES:
        count, unit = E.STAGE_SLA[label]
        node = {
            "id": stage_ids[label],
            "type": "case-management:Stage",
            "data": {
                "label": label,
                "entryConditions": _stage_entry(label, stage_ids),
                "exitConditions": _stage_exit(label, tasks),
                "slaRules": [
                    {
                        "id": sla_ids[label],
                        "displayName": f"{label} SLA",
                        "expression": "=js:true",
                        "count": count,
                        "unit": unit,
                        "escalationRule": escalations(E.norm(label), f"{label} SLA"),
                    }
                ],
                "tasks": [[task] for task in tasks[label].values()],
            },
        }
        if label in E.SECONDARY_STAGES:
            node["data"]["stageType"] = "secondary"
        nodes.append(node)

    return {
        "id": "case-supplier1",
        "version": "27.0.0",
        "name": E.SOLUTION,
        "metadata": {
            "caseIdentifier": "SUP",
            "caseIdentifierType": "constant",
            "caseAppEnabled": True,
            "slaRules": [
                {
                    "id": root_sla,
                    "displayName": E.CASE_SLA_TITLE,
                    "expression": "=js:true",
                    "count": E.CASE_SLA[0],
                    "unit": E.CASE_SLA[1],
                    "escalationRule": escalations("root", E.CASE_SLA_TITLE),
                }
            ],
            "caseExitRules": [
                {
                    "id": "Condition_case1",
                    "displayName": "Application resolved",
                    "marksCaseComplete": True,
                    "rules": [[{"id": "Rule_case1", "rule": "required-stages-completed"}]],
                },
                {
                    "id": "Condition_case2",
                    "displayName": "Rejected Exit",
                    "marksCaseComplete": False,
                    "rules": [
                        [
                            {
                                "id": "Rule_case2",
                                "rule": "selected-stage-completed",
                                "selectedStageId": stage_ids[E.REJECTED],
                            }
                        ]
                    ],
                },
                {
                    "id": "Condition_case3",
                    "displayName": "Withdrawn Exit",
                    "marksCaseComplete": False,
                    "rules": [
                        [
                            {
                                "id": "Rule_case3",
                                "rule": "selected-stage-completed",
                                "selectedStageId": stage_ids[E.WITHDRAWN],
                            }
                        ]
                    ],
                },
            ],
        },
        "bindings": bindings,
        "variables": {
            "inputs": [
                {
                    "id": name,
                    "name": name,
                    "type": VARIABLE_TYPES.get(name, "string"),
                    "elementId": "root",
                }
                for name in E.IN_VARIABLES
            ],
            "outputs": [],
            "inputOutputs": [
                {"id": name, "name": name, "type": "string", "elementId": "root"}
                for name in E.GATE_VARIABLES
            ],
        },
        "nodes": nodes,
        "edges": [],
    }


def _resource_kinds() -> dict[str, str]:
    return {
        **{name: "api-workflow" for name in E.API_WORKFLOWS},
        **{name: "agent" for name in E.AGENTS},
        **{name: "process" for name in E.PROCESSES},
        **{name: "case-management" for name in E.CHILD_CASES},
        **{name: "action" for name in E.ACTION_APPS},
        E.SHARED_ESCALATION_APP: "action",
    }


def _task_data(spec: dict, binding_ids: dict[str, tuple[str, str]]) -> dict:
    if spec["type"] == E.CONNECTOR_TASK:
        return {
            "serviceType": "Intsvc.ActivityExecution",
            "connectionId": E.CONNECTION_ID,
            "typeId": E.ACTIVITY_TYPE_ID,
            "context": [
                {"name": "connectorKey", "value": E.CONNECTOR_KEY, "type": "string"}
            ],
            "inputs": [],
            "outputs": [],
        }
    name_id, folder_id = binding_ids[E.TASK_RESOURCE[spec["name"]]]
    data = {
        "name": f"=bindings.{name_id}",
        "folderPath": f"=bindings.{folder_id}",
        "inputs": [],
        "outputs": [],
    }
    if spec["type"] == "action":
        data["taskTitle"] = f"{spec['name']}: {{{{companyName}}}}"
        data["priority"] = "Medium"
        recipient = E.EXPRESSION_RECIPIENTS.get(spec["name"])
        if recipient:
            data["recipient"] = {"Type": 3, "Value": recipient}
    return data


def _entry_conditions(
    spec: dict, siblings: dict[str, dict], stage_sla: str, root_sla: str
) -> list[dict]:
    name = spec["name"]
    kind = spec["entry"]
    if kind == "stage-entered":
        return [condition(f"e{name[:4]}", "current-stage-entered")]
    if kind == "adhoc":
        return [condition(f"a{name[:4]}", "adhoc")]
    if kind == "sequential":
        expression = E.BANK_VERIFIED if name == E.PORTAL_GATE["task"] else None
        return [condition(f"s{name[:4]}", "runs-sequentially", expression=expression)]
    if kind in ("sla-stage", "sla-root"):
        return [
            condition(
                f"l{name[:4]}",
                "sla-status-change",
                slaId=stage_sla if kind == "sla-stage" else root_sla,
            )
        ]
    if name == E.SIGN_OFF_GATE["task"]:
        return [
            condition(
                "gsign",
                "selected-tasks-completed",
                expression=E.SIGN_OFF_REQUIRED,
                selectedTasksIds=[siblings[t]["id"] for t in E.SIGN_OFF_GATE["selected"]],
            )
        ]
    return [
        condition(
            "gcomp1",
            "selected-tasks-completed",
            expression=E.SIGN_OFF_NOT_REQUIRED,
            selectedTasksIds=[
                siblings[t]["id"] for t in E.COMPLIANCE_GATE["selected_without"]
            ],
        ),
        condition(
            "gcomp2",
            "selected-tasks-completed",
            expression=E.SIGN_OFF_REQUIRED,
            selectedTasksIds=[
                siblings[t]["id"] for t in E.COMPLIANCE_GATE["selected_with"]
            ],
        ),
    ]


def _stage_entry(label: str, stage_ids: dict[str, str]) -> list[dict]:
    if label == E.CHECKING:
        return [
            condition("en1", "case-entered"),
            condition(
                "en2",
                "selected-stage-exited",
                expression=E.SEND_BACK,
                selectedStageId=stage_ids[E.BUYER],
            ),
        ]
    linear = {
        E.BUYER: E.CHECKING,
        E.COMPLIANCE: E.BUYER,
        E.SETUP: E.COMPLIANCE,
        E.ONBOARDED: E.SETUP,
    }
    if label in linear:
        return [
            condition(
                f"en{E.norm(label)[:4]}",
                "selected-stage-completed",
                selectedStageId=stage_ids[linear[label]],
            )
        ]
    if label == E.REJECTED:
        rows = [
            (E.BUYER, E.BUYER_DECLINE),
            (E.COMPLIANCE, E.COMPLIANCE_REJECT),
            (E.SETUP, E.BANK_NOT_VERIFIED),
        ]
        out = []
        for index, (source, guard) in enumerate(rows):
            entry = condition(
                f"enrej{index}",
                "selected-stage-exited",
                expression=guard,
                selectedStageId=stage_ids[source],
            )
            entry["isInterrupting"] = True
            out.append(entry)
        return out
    entry = condition("enwd", "wait-for-connector")
    entry["isInterrupting"] = True
    entry["rules"][0][0]["uipath"] = {
        "serviceType": "Intsvc.WaitForEvent",
        "context": [
            {"name": "connectorKey", "value": E.CONNECTOR_KEY, "type": "string"},
            {"name": "operation", "value": "supplier-withdrawal", "type": "string"},
        ],
    }
    return [entry]


def _stage_exit(label: str, tasks: dict[str, dict[str, dict]]) -> list[dict]:
    def complete(cid: str, expression: str | None = None) -> dict:
        entry = condition(cid, "required-tasks-completed", expression=expression)
        entry["type"] = "exit-only"
        entry["marksStageComplete"] = True
        return entry

    def route(cid: str, task_name: str, expression: str) -> dict:
        entry = condition(
            cid,
            "selected-tasks-completed",
            expression=expression,
            selectedTasksIds=[tasks[label][task_name]["id"]],
        )
        entry["type"] = "exit-only"
        entry["marksStageComplete"] = False
        return entry

    if label == E.BUYER:
        return [
            complete("xbuy0", E.BUYER_APPROVE),
            route("xbuy1", "Buyer Decision", E.BUYER_DECLINE),
            route("xbuy2", "Buyer Decision", E.SEND_BACK),
        ]
    if label == E.COMPLIANCE:
        return [
            complete("xcmp0", E.SEND_TO_SETUP),
            route("xcmp1", "Compliance Decision", E.COMPLIANCE_REJECT),
        ]
    if label == E.SETUP:
        return [
            complete("xset0"),
            route("xset1", "Create Supplier Record in ERP", E.BANK_NOT_VERIFIED),
        ]
    return [complete(f"x{E.norm(label)[:4]}")]


def build_sidecar(plan: dict) -> dict:
    resources = []
    for key in sorted(
        {
            binding["resourceKey"]
            for binding in plan["bindings"]
            if binding.get("resource") != "Connection"
        }
    ):
        resources.append({"key": key, "value": {"metadata": {}}})
    resources.append(
        {"key": f"connection.{E.CONNECTION_ID}", "value": {"connectionId": E.CONNECTION_ID}}
    )
    return {"resources": resources}


class GraderCase(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.plan = build_plan()
        self.write(self.plan)
        shutil.copy(FIXTURE_SDD, self.dir / "sdd.md")

    def write(self, plan: dict) -> None:
        target = self.dir / E.CASEPLAN_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(plan, indent=1))
        (target.parent / "bindings_v2.json").write_text(
            json.dumps(build_sidecar(plan), indent=1)
        )

    def run_checker(self, script: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(script)],
            cwd=self.dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def assert_passes(self, script: Path) -> None:
        result = self.run_checker(script)
        self.assertEqual(
            result.returncode, 0, f"{script.name} failed:\n{result.stdout}{result.stderr}"
        )

    def assert_fails(self, script: Path, needle: str = "") -> str:
        result = self.run_checker(script)
        self.assertNotEqual(
            result.returncode, 0, f"{script.name} unexpectedly passed:\n{result.stdout}"
        )
        output = result.stdout + result.stderr
        if needle:
            self.assertIn(needle.lower(), output.lower(), output)
        return output

    # helpers ---------------------------------------------------------------
    def mutate(self):
        plan = copy.deepcopy(self.plan)
        return plan

    def stage(self, plan: dict, label: str) -> dict:
        for node in plan["nodes"]:
            if (node.get("data") or {}).get("label") == label:
                return node
        raise AssertionError(f"stage {label} missing from synthetic plan")

    def task(self, plan: dict, label: str, name: str) -> dict:
        for lane in self.stage(plan, label)["data"]["tasks"]:
            for task in lane:
                if task["displayName"] == name:
                    return task
        raise AssertionError(f"task {name} missing from synthetic plan")


class ReferencePlanTests(GraderCase):
    def test_all_graders_pass(self) -> None:
        for script in (TOPOLOGY, TASKS, SLA, BINDINGS, SDD):
            with self.subTest(script=script.name):
                self.assert_passes(script)

    def test_missing_caseplan_fails(self) -> None:
        (self.dir / E.CASEPLAN_PATH).unlink()
        self.assert_fails(TOPOLOGY)


class TopologyTests(GraderCase):
    def test_missing_stage(self) -> None:
        plan = self.mutate()
        plan["nodes"] = [
            node for node in plan["nodes"] if (node.get("data") or {}).get("label") != E.ONBOARDED
        ]
        self.write(plan)
        self.assert_fails(TOPOLOGY, "'Onboarded' not found")

    def test_secondary_stage_authored_as_primary(self) -> None:
        plan = self.mutate()
        self.stage(plan, E.REJECTED)["data"].pop("stageType")
        self.write(plan)
        self.assert_fails(TOPOLOGY, "secondary")

    def test_send_back_guard_dropped(self) -> None:
        plan = self.mutate()
        for entry in self.stage(plan, E.CHECKING)["data"]["entryConditions"]:
            entry.pop("conditionExpression", None)
        self.write(plan)
        self.assert_fails(TOPOLOGY, "send-back")

    def test_rejected_entry_not_interrupting(self) -> None:
        plan = self.mutate()
        self.stage(plan, E.REJECTED)["data"]["entryConditions"][0]["isInterrupting"] = False
        self.write(plan)
        self.assert_fails(TOPOLOGY, "interrupting")

    def test_withdrawn_entered_from_a_stage(self) -> None:
        plan = self.mutate()
        entry = self.stage(plan, E.WITHDRAWN)["data"]["entryConditions"][0]
        entry["rules"][0][0] = {"id": "Rule_x", "rule": "selected-stage-completed", "selectedStageId": "Stage_0"}
        self.write(plan)
        self.assert_fails(TOPOLOGY, "wait-for-connector")

    def test_bank_failure_exit_dropped(self) -> None:
        plan = self.mutate()
        setup = self.stage(plan, E.SETUP)["data"]
        setup["exitConditions"] = [setup["exitConditions"][0]]
        self.write(plan)
        self.assert_fails(TOPOLOGY, E.BANK_NOT_VERIFIED.split(" ")[0])

    def test_rejected_case_exit_marks_complete(self) -> None:
        plan = self.mutate()
        plan["metadata"]["caseExitRules"][1]["marksCaseComplete"] = True
        self.write(plan)
        self.assert_fails(TOPOLOGY, "Marks Case Complete")

    def test_document_input_not_file_typed(self) -> None:
        plan = self.mutate()
        for variable in plan["variables"]["inputs"]:
            if variable["name"] == "insuranceDocument":
                variable["type"] = "string"
        self.write(plan)
        self.assert_fails(TOPOLOGY, "file")

    def test_event_trigger_instead_of_manual(self) -> None:
        plan = self.mutate()
        plan["nodes"][0]["data"]["inputs"]["serviceType"] = "Intsvc.EventTrigger"
        self.write(plan)
        self.assert_fails(TOPOLOGY, "Manual")


class TaskMatrixTests(GraderCase):
    def test_wrong_task_type(self) -> None:
        plan = self.mutate()
        self.task(plan, E.CHECKING, "Match Offering to Category")["type"] = "process"
        self.write(plan)
        self.assert_fails(TASKS, "type must be 'agent'")

    def test_required_flag_flipped(self) -> None:
        plan = self.mutate()
        self.task(plan, E.BUYER, "Buyer Decision")["isRequired"] = False
        self.write(plan)
        self.assert_fails(TASKS, "isRequired")

    def test_run_once_inferred(self) -> None:
        plan = self.mutate()
        self.task(plan, E.CHECKING, "Receive Additional Documents")["shouldRunOnlyOnce"] = True
        self.write(plan)
        self.assert_fails(TASKS, "shouldRunOnlyOnce")

    def test_adhoc_task_given_stage_entry(self) -> None:
        plan = self.mutate()
        task = self.task(plan, E.BUYER, "Order Reference Check")
        task["entryConditions"] = [condition("x", "current-stage-entered")]
        self.write(plan)
        self.assert_fails(TASKS, "adhoc")

    def test_task_without_entry_condition(self) -> None:
        plan = self.mutate()
        self.task(plan, E.CHECKING, "Validate Application")["entryConditions"] = []
        self.write(plan)
        self.assert_fails(TASKS, "entryConditions is empty")

    def test_extra_task_in_stage(self) -> None:
        plan = self.mutate()
        self.stage(plan, E.ONBOARDED)["data"]["tasks"].append(
            [{"id": "textra", "displayName": "Extra", "type": "action", "data": {}}]
        )
        self.write(plan)
        self.assert_fails(TASKS, "must carry 5 tasks")

    def test_compliance_gate_missing_sign_off_selector(self) -> None:
        plan = self.mutate()
        task = self.task(plan, E.COMPLIANCE, "Compliance Decision")
        sign_off = self.task(plan, E.COMPLIANCE, "Procurement Director Sign-off")["id"]
        for entry in task["entryConditions"]:
            rule = entry["rules"][0][0]
            rule["selectedTasksIds"] = [
                task_id for task_id in rule["selectedTasksIds"] if task_id != sign_off
            ]
        self.write(plan)
        self.assert_fails(TASKS, "Procurement Director Sign-off")

    def test_sign_off_gate_expression_dropped(self) -> None:
        plan = self.mutate()
        for entry in self.task(plan, E.COMPLIANCE, "Procurement Director Sign-off")["entryConditions"]:
            entry.pop("conditionExpression", None)
        self.write(plan)
        self.assert_fails(TASKS, "directorSignOffRequired")

    def test_portal_gate_expression_dropped(self) -> None:
        plan = self.mutate()
        for entry in self.task(plan, E.SETUP, "Verify Supplier Portal Access")["entryConditions"]:
            entry.pop("conditionExpression", None)
        self.write(plan)
        self.assert_fails(TASKS, "bankDetailsVerified")

    def test_recipient_as_bare_string(self) -> None:
        plan = self.mutate()
        self.task(plan, E.BUYER, "Buyer Decision")["data"]["recipient"] = "=vars.assignedBuyer"
        self.write(plan)
        self.assert_fails(TASKS, "recipient")


class SlaTests(GraderCase):
    def test_stage_sla_duration_wrong(self) -> None:
        plan = self.mutate()
        self.stage(plan, E.BUYER)["data"]["slaRules"][0]["count"] = 2
        self.write(plan)
        self.assert_fails(SLA, "4 d")

    def test_case_sla_missing(self) -> None:
        plan = self.mutate()
        plan["metadata"]["slaRules"] = []
        self.write(plan)
        self.assert_fails(SLA, "root")

    def test_at_risk_percentage_wrong(self) -> None:
        plan = self.mutate()
        rule = self.stage(plan, E.CHECKING)["data"]["slaRules"][0]
        rule["escalationRule"][0]["triggerInfo"]["atRiskPercentage"] = 80
        self.write(plan)
        self.assert_fails(SLA, "70%")

    def test_escalation_task_points_at_other_stage_sla(self) -> None:
        plan = self.mutate()
        task = self.task(
            plan, E.BUYER, "Escalate Buyer Review to Procurement Operations Lead"
        )
        task["entryConditions"][0]["rules"][0][0]["slaId"] = self.stage(plan, E.CHECKING)[
            "data"
        ]["slaRules"][0]["id"]
        self.write(plan)
        self.assert_fails(SLA, "owned by")

    def test_post_mortem_points_at_stage_sla(self) -> None:
        plan = self.mutate()
        task = self.task(
            plan, E.REJECTED, "Procurement Director Post-Mortem Review - Rejected"
        )
        task["entryConditions"][0]["rules"][0][0]["slaId"] = self.stage(plan, E.REJECTED)[
            "data"
        ]["slaRules"][0]["id"]
        self.write(plan)
        self.assert_fails(SLA, "root")

    def test_breach_rule_carries_escalation_id(self) -> None:
        plan = self.mutate()
        task = self.task(
            plan, E.CHECKING, "Send Supplier Delay Notice - Checking the Application"
        )
        rule = task["entryConditions"][0]["rules"][0][0]
        rule["escalationId"] = "esc_checkingtheapplication_breach"
        self.write(plan)
        self.assert_fails(SLA, "escalationId")

    def test_sla_response_as_stage_entry(self) -> None:
        plan = self.mutate()
        stage = self.stage(plan, E.CHECKING)["data"]
        stage["entryConditions"].append(
            condition("slaentry", "sla-status-change", slaId=stage["slaRules"][0]["id"])
        )
        self.write(plan)
        self.assert_fails(SLA, "ENTRY rule")

    def test_any_escalation_sentinel(self) -> None:
        plan = self.mutate()
        task = self.task(
            plan, E.CHECKING, "Escalate Checking the Application to Procurement Operations Lead"
        )
        task["entryConditions"][0]["rules"][0][0]["escalationId"] = "any"
        self.write(plan)
        self.assert_fails(SLA, "any")


class BindingTests(GraderCase):
    def test_placeholder_task(self) -> None:
        plan = self.mutate()
        self.task(plan, E.CHECKING, "Screen Company Records")["data"] = {}
        self.write(plan)
        self.assert_fails(BINDINGS, "placeholder")

    def test_literal_name_instead_of_binding_ref(self) -> None:
        plan = self.mutate()
        self.task(plan, E.CHECKING, "Screen Company Records")["data"]["name"] = "Supplier Master and Screening Lookup"
        self.write(plan)
        self.assert_fails(BINDINGS, "=bindings.")

    def test_resource_key_is_a_tenant_guid(self) -> None:
        plan = self.mutate()
        for binding in plan["bindings"]:
            if binding.get("default") == "OfferingCategoryMatchAgent":
                guid = "ce93a98d-ed40-4b66-afda-33fa9e11b2bb"
                binding["resourceKey"] = guid
        self.write(plan)
        self.assert_fails(BINDINGS, "resourceKey")

    def test_bare_resource_key_without_folder(self) -> None:
        plan = self.mutate()
        for binding in plan["bindings"]:
            if binding.get("resourceKey", "").endswith(".DetermineSupplierSignOffTier"):
                binding["resourceKey"] = "DetermineSupplierSignOffTier"
        self.write(plan)
        self.assert_fails(BINDINGS, "folderPath")

    def test_wrong_resource_sub_type(self) -> None:
        plan = self.mutate()
        for binding in plan["bindings"]:
            if binding.get("resourceKey", "").endswith(".ERP Supplier Setup"):
                binding["resourceSubType"] = "ProcessOrchestration"
        self.write(plan)
        self.assert_fails(BINDINGS, "resourceSubType")

    def test_task_bound_to_the_wrong_resource(self) -> None:
        plan = self.mutate()
        task = self.task(plan, E.COMPLIANCE, "Compliance and Risk Screening")
        other = self.task(plan, E.CHECKING, "Screen Company Records")
        task["data"]["folderPath"] = other["data"]["folderPath"]
        self.write(plan)
        self.assert_fails(BINDINGS, "resolves it to")

    def test_connector_task_without_connection(self) -> None:
        plan = self.mutate()
        task = self.task(plan, E.ONBOARDED, "Send Welcome Message")
        task["data"].pop("connectionId")
        self.write(plan)
        self.assert_fails(BINDINGS, "connection")

    def test_phase_three_context_only_connector_passes(self) -> None:
        """The fully-populated shape reaches the connection through a binding ref."""
        plan = self.mutate()
        task = self.task(plan, E.REJECTED, "Notify Supplier of Rejection")
        task["data"] = {
            "serviceType": "Intsvc.ActivityExecution",
            "context": [
                {"name": "connectorKey", "value": E.CONNECTOR_KEY, "type": "string"},
                {"name": "connection", "value": "=bindings.bconn", "type": "string"},
                {"name": "operation", "value": "Send email", "type": "string"},
            ],
            "inputs": [],
            "outputs": [],
            "bindings": [],
        }
        self.write(plan)
        self.assert_passes(BINDINGS)

    def test_connector_bound_to_another_connection(self) -> None:
        plan = self.mutate()
        task = self.task(plan, E.REJECTED, "Notify Supplier of Rejection")
        task["data"]["connectionId"] = "00000000-0000-0000-0000-000000000000"
        self.write(plan)
        self.assert_fails(BINDINGS, "connection")

    def test_sidecar_out_of_parity(self) -> None:
        plan = self.mutate()
        self.write(plan)
        sidecar_path = self.dir / E.CASEPLAN_PATH
        sidecar_path = sidecar_path.parent / "bindings_v2.json"
        sidecar = json.loads(sidecar_path.read_text())
        sidecar["resources"] = sidecar["resources"][:3]
        sidecar_path.write_text(json.dumps(sidecar))
        self.assert_fails(BINDINGS, "parity")

    def test_sidecar_missing(self) -> None:
        plan = self.mutate()
        self.write(plan)
        (self.dir / E.CASEPLAN_PATH).parent.joinpath("bindings_v2.json").unlink()
        self.assert_fails(BINDINGS, "bindings_v2.json")


class SddGuardTests(GraderCase):
    def test_trimmed_sdd_fails(self) -> None:
        (self.dir / "sdd.md").write_text("# SDD — SupplierOnboarding\n\nnothing left\n")
        self.assert_fails(SDD)

    def test_missing_sdd_fails(self) -> None:
        (self.dir / "sdd.md").unlink()
        self.assert_fails(SDD, "no staged sdd.md")


if __name__ == "__main__":
    unittest.main()
