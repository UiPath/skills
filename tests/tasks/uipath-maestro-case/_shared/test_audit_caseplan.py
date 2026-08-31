"""Unit tests for the caseplan-vs-SDD completeness gate.

The gate lives in the skill (not the test tree) because agents run it as the
Step 12 loop; these tests pin the failure classes it must never stop catching.
"""

import copy
import importlib.util
import json
import os
import sys

import pytest

SCRIPT = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "..", "..",
        "skills", "uipath-maestro-case", "scripts", "audit_caseplan.py",
    )
)
_spec = importlib.util.spec_from_file_location("audit_caseplan", SCRIPT)
audit_caseplan = importlib.util.module_from_spec(_spec)
sys.modules["audit_caseplan"] = audit_caseplan
_spec.loader.exec_module(audit_caseplan)


SDD = """
# SDD — Widgets

## Section 1: Case Definition

### Case Triggers

| T# | Trigger Type | Source | Configuration |
|----|-------------|--------|---------------|
| T02 | Manual | Manual | N/A |

### Case Exit Conditions

| WHEN | IF | THEN | Marks Case Complete | Display Name |
|------|-----|------|---------------------|--------------|
| `required-stages-completed` | — | Case exited | Yes | Done |

### Case Variables

| Name | Category | Type | Default | Description |
|------|----------|------|---------|-------------|
| orderId | In | string | | Order identifier |

## Section 2: Stages & Tasks

### Stage 1: Intake

**Required for Case Completion:** Yes

#### Stage Entry Conditions

| WHEN | IF | Interrupting | Display Name |
|------|-----|-------------|--------------|
| `case-entered` | — | No | Entry Rule 1 |

#### Stage Exit Conditions

| WHEN | IF | Exit Type | Marks Stage Complete | Display Name |
|------|-----|-----------|---------------------|--------------|
| `required-tasks-completed` | — | exit-only | Yes | Complete Rule 1 |

#### Tasks

| # | Task Name | Type | Activation Mode | Required |
|---|-----------|------|-----------------|----------|
| 1 | Check Order | api-workflow | sequential | Yes |

---

##### Task 1.1: Check Order

**Type:** api-workflow

**Entry Condition:**

| WHEN | IF | Display Name |
|------|-----|--------------|
| `runs-sequentially` | — | Entry Rule 1 |

###### Process / Agent / RPA / API Workflow Task Detail

**Resolved Resource:** OrderCheckWorkflow
**Folder Path:** `Shared/widgets`
**Resource Identity:** `wf-1`
"""

CASEPLAN = {
    "metadata": {"caseExitRules": [{"id": "c1", "rules": [[{"rule": "required-stages-completed"}]]}]},
    "bindings": [
        {"id": "bNm", "resource": "process", "resourceSubType": "Api",
         "resourceKey": "Shared/widgets/Order Check.API Workflow"},
        {"id": "bFp", "resource": "process", "resourceSubType": "Api",
         "resourceKey": "Shared/widgets/Order Check.API Workflow"},
    ],
    "variables": {"inputs": [{"name": "orderId", "type": "string"}], "outputs": [], "inputOutputs": []},
    "nodes": [
        {"id": "trigger1", "type": "uipath.case.trigger", "data": {}},
        {
            "id": "Stage_Intake",
            "type": "case-management:Stage",
            "data": {
                "label": "Intake",
                "entryConditions": [{"id": "e1", "rules": [[{"rule": "case-entered"}]]}],
                "exitConditions": [{"id": "x1", "rules": [[{"rule": "required-tasks-completed"}]]}],
                "slaRules": [],
                "tasks": [[{
                    "id": "t1",
                    "type": "api-workflow",
                    "displayName": "Check Order",
                    "entryConditions": [{"id": "c1", "rules": [[{"rule": "runs-sequentially"}]]}],
                    "data": {"name": "=bindings.bNm", "folderPath": "=bindings.bFp"},
                }]],
            },
        },
    ],
}


def run(plan):
    return audit_caseplan.compare(audit_caseplan.parse_sdd(SDD), audit_caseplan.parse_caseplan(plan))


def test_matched_pair_is_clean():
    missing, _ = run(copy.deepcopy(CASEPLAN))
    assert missing == []


def test_missing_task_entry_conditions_fail():
    """`validate` only warns here; a real miss hangs `case debug` forever."""
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["entryConditions"] = []
    missing, _ = run(plan)
    assert any("no entryConditions" in f for f in missing)


def test_dropped_task_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"] = [[]]
    missing, _ = run(plan)
    assert any("'Check Order': declared in the SDD" in f for f in missing)


def test_dropped_stage_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"] = [plan["nodes"][0]]
    missing, _ = run(plan)
    assert any("stage 'Intake': declared in the SDD" in f for f in missing)


def test_bare_resource_key_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["bindings"][0]["resourceKey"] = "Shared/widgets/Order Check"
    missing, _ = run(plan)
    assert any("bare resourceKey" in f for f in missing)


def test_api_workflow_binding_without_resource_sub_type_fails():
    plan = copy.deepcopy(CASEPLAN)
    del plan["bindings"][0]["resourceSubType"]
    missing, _ = run(plan)
    assert any("resourceSubType" in f for f in missing)


def test_placeholder_for_a_resolved_resource_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["data"] = {}
    missing, _ = run(plan)
    assert any("placeholder" in f and "SDD resolved the resource" in f for f in missing)


def test_placeholder_for_an_unresolved_resource_only_warns():
    sdd = SDD.replace("**Resource Identity:** `wf-1`", "**Resource Identity:** `<UNRESOLVED>`") \
             .replace("**Folder Path:** `Shared/widgets`", "**Folder Path:** `<UNRESOLVED>`")
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["data"] = {}
    missing, warn = audit_caseplan.compare(audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan))
    assert missing == []
    assert any("placeholder task" in w for w in warn)


def test_dropped_variable_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["inputs"] = []
    missing, _ = run(plan)
    assert any("variable 'orderId'" in f for f in missing)


def test_dropped_case_exit_rules_fail():
    plan = copy.deepcopy(CASEPLAN)
    plan["metadata"]["caseExitRules"] = []
    missing, _ = run(plan)
    assert any("caseExitRules" in f for f in missing)


def test_type_mismatch_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["type"] = "action"
    missing, _ = run(plan)
    assert any("SDD type 'api-workflow'" in f for f in missing)


def test_task_named_only_by_its_binding_still_matches():
    """Some builds carry the display name only on the `name` binding."""
    plan = copy.deepcopy(CASEPLAN)
    del plan["nodes"][1]["data"]["tasks"][0][0]["displayName"]
    plan["bindings"][0]["default"] = "Check Order"
    missing, _ = run(plan)
    assert missing == []


def test_renamed_duplicate_task_still_matches():
    """Same SDD task name in several stages needs unique caseplan displayNames."""
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["displayName"] = "Check Order — Intake"
    missing, _ = run(plan)
    assert missing == []


def test_secondary_stage_heading_is_parsed():
    sdd = SDD.replace("### Stage 1: Intake", "### Secondary Stage: Intake")
    parsed = audit_caseplan.parse_sdd(sdd)
    assert [s["name"] for s in parsed["stages"]] == ["Intake"]


def test_sla_status_change_arity_is_checked():
    findings = audit_caseplan.sla_reference_findings('`sla-status-change("root")`', "sdd.md")
    assert any("2 (breach) or 3 (at-risk)" in f for f in findings)
    assert audit_caseplan.sla_reference_findings('`sla-status-change("root", "X")`', "sdd.md") == []


def test_sla_status_change_case_target_is_rejected():
    findings = audit_caseplan.sla_reference_findings('`sla-status-change("Case", "X")`', "sdd.md")
    assert any("literal 'root'" in f for f in findings)


def test_stage_sla_with_no_table_is_not_required():
    """`#### Stage SLA` + `> None.` must not demand slaRules in the caseplan."""
    sdd = SDD.replace(
        "#### Stage Exit Conditions",
        "#### Stage SLA\n\n> None.\n\n#### Stage Exit Conditions",
    )
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(copy.deepcopy(CASEPLAN))
    )
    assert missing == []


def test_cli_exits_nonzero_on_missing(tmp_path, capsys):
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["entryConditions"] = []
    plan_path = tmp_path / "caseplan.json"
    sdd_path = tmp_path / "sdd.md"
    plan_path.write_text(json.dumps(plan))
    sdd_path.write_text(SDD)
    argv = sys.argv
    sys.argv = ["audit_caseplan.py", str(plan_path), "--sdd", str(sdd_path)]
    try:
        with pytest.raises(SystemExit) as excinfo:
            audit_caseplan.main()
    finally:
        sys.argv = argv
    assert excinfo.value.code == 1
    assert "AUDIT FAIL" in capsys.readouterr().err


def test_cli_exits_zero_when_clean(tmp_path, capsys):
    plan_path = tmp_path / "caseplan.json"
    sdd_path = tmp_path / "sdd.md"
    plan_path.write_text(json.dumps(CASEPLAN))
    sdd_path.write_text(SDD)
    argv = sys.argv
    sys.argv = ["audit_caseplan.py", str(plan_path), "--sdd", str(sdd_path)]
    try:
        audit_caseplan.main()
    finally:
        sys.argv = argv
    assert "AUDIT OK" in capsys.readouterr().out
