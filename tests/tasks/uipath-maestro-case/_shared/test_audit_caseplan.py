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
    "variables": {
        "inputs": [{"id": "vK3mNp9Qx", "name": "orderId", "type": "string"}],
        "outputs": [],
        # An In-arg is a formal slot AND a root companion (Loop B of
        # global-vars/impl-json.md); the companion is what `=vars.orderId` resolves.
        "inputOutputs": [{"id": "orderId", "name": "orderId", "type": "string"}],
    },
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


# --------------------------------------------------------------------------
# Category -> `variables` group placement
#
# A row's Category decides which arrays it must reach: In and Out need their
# formal slot AND the root companion, a pure-state Variable is companion-only.
# Half a pair passes `uip maestro case validate` and then drops the argument
# from the entry-point contract, so presence-anywhere is not enough.
# --------------------------------------------------------------------------

VARIABLE_ROW = "| orderId | In | string | | Order identifier |"


def _with_variable_row(row):
    return SDD.replace(VARIABLE_ROW, f"{VARIABLE_ROW}\n{row}")


def _companion(name, var_type):
    return {"id": name, "name": name, "type": var_type, "elementId": "root"}


def test_out_variable_without_its_formal_outputs_entry_fails():
    """The io-binding-matrix miss: the companion is written, the formal Out-arg
    slot is not, so the argument never reaches `entry-points.json`."""
    sdd = _with_variable_row("| totalPaid | Out | number | | Amount paid |")
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["inputOutputs"].append(_companion("totalPaid", "number"))
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan)
    )
    assert any("'totalPaid'" in f and "variables.outputs[]" in f for f in missing)


def test_out_variable_with_both_entries_is_clean():
    sdd = _with_variable_row("| totalPaid | Out | number | | Amount paid |")
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["outputs"].append(
        {"id": "vQ7rTz2Wb", "name": "totalPaid", "type": "number", "var": "totalPaid"}
    )
    plan["variables"]["inputOutputs"].append(_companion("totalPaid", "number"))
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan)
    )
    assert missing == []


def test_in_variable_without_its_companion_fails():
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["inputOutputs"] = []
    missing, _ = run(plan)
    assert any("'orderId'" in f and "variables.inputOutputs[]" in f for f in missing)


def test_pure_state_variable_in_the_wrong_group_fails():
    sdd = _with_variable_row("| caseStatus | Variable | string | Open | Current state |")
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["outputs"].append(
        {"id": "vB4hLm6Cd", "name": "caseStatus", "type": "string", "var": "caseStatus"}
    )
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan)
    )
    assert any("'caseStatus'" in f and "variables.inputOutputs[]" in f for f in missing)


def test_a_variable_absent_everywhere_is_reported_once():
    """Absent is the presence finding, not one placement finding per group."""
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["inputs"] = []
    plan["variables"]["inputOutputs"] = []
    missing, _ = run(plan)
    assert [f for f in missing if "'orderId'" in f] == [
        "variable 'orderId': declared in the SDD Case Variables table, absent from caseplan.json"
    ]


def test_case_variables_table_without_a_category_column_is_reported():
    """Without Category the placement class empties silently while the gate
    keeps printing AUDIT OK."""
    parsed = audit_caseplan.parse_sdd(SDD.replace("| Name | Category |", "| Name | Kind |"))
    assert parsed["variables"] == ["orderId"]
    assert any("no Category column" in n for n in parsed["parse_notes"])


def test_unsupported_category_is_not_placement_checked():
    """`InOut` is not supported in v1; the row still has to exist somewhere."""
    sdd = _with_variable_row("| bothWays | InOut | string | | Unsupported |")
    plan = copy.deepcopy(CASEPLAN)
    plan["variables"]["inputOutputs"].append(_companion("bothWays", "string"))
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan)
    )
    assert missing == []


def test_dropped_case_exit_rules_fail():
    plan = copy.deepcopy(CASEPLAN)
    plan["metadata"]["caseExitRules"] = []
    missing, _ = run(plan)
    assert any("caseExitRules" in f for f in missing)


# --------------------------------------------------------------------------
# Row counts, not truthiness
#
# Every condition/trigger check compares an SDD row count against what the
# caseplan kept. A build that keeps 1 of 3 rows is the archetypal lossy build
# this gate exists to catch, so the comparison must be on totals -- but `>=`,
# not `==`: rows legitimately group into one condition's AND-group, and one row
# legitimately fans out into several OR-groups.
# --------------------------------------------------------------------------

STAGE_EXIT_ROW = "| `required-tasks-completed` | \u2014 | exit-only | Yes | Complete Rule 1 |"
CASE_EXIT_ROW = "| `required-stages-completed` | \u2014 | Case exited | Yes | Done |"
TRIGGER_ROW = "| T02 | Manual | Manual | N/A |"
TASK_ENTRY_ROW = "| `runs-sequentially` | \u2014 | Entry Rule 1 |"


def _repeat_row(sdd, row, times):
    return sdd.replace(row, "\n".join(f"{row[:-1]}{n} |" for n in range(1, times + 1)))


def test_partially_kept_stage_exit_rows_fail():
    """1 of 3 exit rows kept: `exitConditions` is truthy, two rows are gone."""
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_repeat_row(SDD, STAGE_EXIT_ROW, 3)),
        audit_caseplan.parse_caseplan(copy.deepcopy(CASEPLAN)),
    )
    assert any("SDD declares 3 exit condition row(s), caseplan keeps 1" in f for f in missing)


def test_partially_kept_case_exit_rules_fail():
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_repeat_row(SDD, CASE_EXIT_ROW, 4)),
        audit_caseplan.parse_caseplan(copy.deepcopy(CASEPLAN)),
    )
    assert any("SDD declares 4 Case Exit Condition row(s)" in f and "keeps 1 rule(s)" in f for f in missing)


def test_partially_kept_triggers_fail():
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_repeat_row(SDD, TRIGGER_ROW, 3)),
        audit_caseplan.parse_caseplan(copy.deepcopy(CASEPLAN)),
    )
    assert any("SDD declares 3 trigger(s), caseplan has 1 trigger node(s)" in f for f in missing)


def test_partially_kept_task_entry_rows_fail():
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_repeat_row(SDD, TASK_ENTRY_ROW, 2)),
        audit_caseplan.parse_caseplan(copy.deepcopy(CASEPLAN)),
    )
    assert any("SDD declares 2 entry condition row(s), caseplan keeps 1" in f for f in missing)


def test_empty_rules_task_entry_envelope_fails():
    """`[{"rules": []}]` is truthy but carries nothing -- it hangs `debug` like `[]`."""
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["entryConditions"] = [{"id": "c1", "rules": []}]
    missing, _ = run(plan)
    assert any("entryConditions carry no rules" in f for f in missing)


def test_empty_rules_task_entry_envelope_fails_without_sdd_rows():
    """The gate must not depend on the SDD declaring an entry table for the task."""
    sdd = SDD.replace(TASK_ENTRY_ROW, "")
    assert audit_caseplan.parse_sdd(sdd)["stages"][0]["tasks"][0]["entry_rows"] == 0
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["entryConditions"] = [{"id": "c1", "rules": []}]
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan)
    )
    assert any("entryConditions carry no rules" in f for f in missing)


def test_rows_grouped_into_one_and_clause_are_clean():
    """Three rows, one condition, three AND-ed rules -- nothing was dropped."""
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"] = []
    plan["nodes"][1]["data"]["exitConditions"] = [
        {"id": "x1", "rules": [[{"rule": "required-tasks-completed"}, {"rule": "a"}, {"rule": "b"}]]}
    ]
    sdd = _repeat_row(SDD, STAGE_EXIT_ROW, 3)
    missing, _ = audit_caseplan.compare(audit_caseplan.parse_sdd(sdd), audit_caseplan.parse_caseplan(plan))
    assert not [f for f in missing if "exit condition row(s)" in f]


def test_one_row_fanned_out_into_or_groups_is_clean():
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["exitConditions"] = [
        {"id": "x1", "rules": [[{"rule": "required-tasks-completed"}], [{"rule": "selected-tasks-completed"}]]}
    ]
    missing, _ = run(plan)
    assert missing == []


def test_stage_condition_with_an_empty_rules_array_fails():
    """A condition object with no rules is truthy but carries nothing."""
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["exitConditions"] = [{"id": "x1", "rules": []}]
    missing, _ = run(plan)
    assert any("caseplan has no exit rules" in f for f in missing)


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


def _run_cli(tmp_path, sdd_text, plan=None):
    plan_path = tmp_path / "caseplan.json"
    sdd_path = tmp_path / "sdd.md"
    plan_path.write_text(json.dumps(plan if plan is not None else CASEPLAN))
    sdd_path.write_text(sdd_text)
    argv = sys.argv
    sys.argv = ["audit_caseplan.py", str(plan_path), "--sdd", str(sdd_path)]
    try:
        return audit_caseplan.main()
    finally:
        sys.argv = argv


def test_cli_fails_when_the_sdd_parses_to_nothing(tmp_path, capsys):
    """Every check is 'SDD declares X -> caseplan has X', so a zero-element parse
    passes vacuously. An unrecognized SDD must fail, not print AUDIT OK."""
    with pytest.raises(SystemExit) as excinfo:
        _run_cli(tmp_path, "# Notes\n\nUnrelated prose with no stages at all.\n")
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "AUDIT FAIL" in err
    assert "stages=0" in err


def test_cli_fails_when_stage_headings_are_the_wrong_level(tmp_path, capsys):
    """`#### Stage 1: Intake` is invisible to the level-3 stage matcher."""
    with pytest.raises(SystemExit) as excinfo:
        _run_cli(tmp_path, SDD.replace("### Stage 1: Intake", "#### Stage 1: Intake"))
    assert excinfo.value.code == 1
    assert "stages=0" in capsys.readouterr().err


def test_ok_line_carries_the_parse_census(tmp_path, capsys):
    """A zero in the census is the reader's signal that the parse degraded."""
    _run_cli(tmp_path, SDD)
    out = capsys.readouterr().out
    assert "AUDIT OK" in out
    assert "stages=1" in out and "tasks=1" in out and "vars=1" in out


def test_fail_output_also_carries_the_census(tmp_path, capsys):
    plan = copy.deepcopy(CASEPLAN)
    plan["nodes"][1]["data"]["tasks"][0][0]["entryConditions"] = []
    with pytest.raises(SystemExit):
        _run_cli(tmp_path, SDD, plan)
    assert "stages=1" in capsys.readouterr().err


TASK_ROW = "| 1 | Check Order | api-workflow | sequential | Yes |"


def _two_task_sdd(first, second):
    return SDD.replace(
        TASK_ROW,
        f"| 1 | {first} | api-workflow | sequential | Yes |\n"
        f"| 2 | {second} | api-workflow | sequential | Yes |",
    )


def _renamed_plan(*display_names):
    plan = copy.deepcopy(CASEPLAN)
    template = plan["nodes"][1]["data"]["tasks"][0][0]
    plan["nodes"][1]["data"]["tasks"] = [[
        {**copy.deepcopy(template), "id": f"t{i}", "displayName": name}
        for i, name in enumerate(display_names)
    ]]
    return plan


def test_prefix_match_does_not_double_bind_an_exact_match():
    """'Check' resolves through the suffix branch to 'Check Order', which then
    exact-matches the same node -- the dropped task must still be reported."""
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_two_task_sdd("Check", "Check Order")),
        audit_caseplan.parse_caseplan(copy.deepcopy(CASEPLAN)),
    )
    assert any("'Check': declared in the SDD" in f for f in missing)


def test_tasks_sharing_a_normalized_key_do_not_double_bind():
    """`norm` drops trailing parentheticals, so both SDD rows key to 'approve'."""
    missing, _ = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_two_task_sdd("Approve (initial)", "Approve (final)")),
        audit_caseplan.parse_caseplan(_renamed_plan("Approve (final)")),
    )
    assert any("'Approve (initial)': declared in the SDD" in f for f in missing)


def test_tasks_sharing_a_normalized_key_both_match_when_both_are_present():
    missing, warn = audit_caseplan.compare(
        audit_caseplan.parse_sdd(_two_task_sdd("Approve (initial)", "Approve (final)")),
        audit_caseplan.parse_caseplan(_renamed_plan("Approve (initial)", "Approve (final)")),
    )
    assert missing == []
    assert not [w for w in warn if "no matching SDD task row" in w]


# --------------------------------------------------------------------------
# Heading and column-header dialects
#
# Every check reads "the SDD declares X, so caseplan.json must have X". A
# heading or column header the parser does not recognize therefore deletes a
# whole check class silently -- the gate keeps printing AUDIT OK while nothing
# in that class is audited. These pin the accepted dialects and, where a dialect
# cannot be accepted, that the drop is reported instead of skipped.
# --------------------------------------------------------------------------

def test_numbered_section_headings_are_matched():
    """`### 1.5 Case Variables` used to normalize to '1 5 case variables' and
    miss, taking all seven declared variables with it."""
    numbered = (
        SDD.replace("### Case Triggers", "### 1.3 Case Triggers")
        .replace("### Case Exit Conditions", "### 1.4 Case Exit Conditions")
        .replace("### Case Variables", "### 1.5 Case Variables")
    )
    parsed = audit_caseplan.parse_sdd(numbered)
    assert parsed["parse_notes"] == []
    assert parsed["variables"] == ["orderId"]
    assert parsed["triggers"] == 1 and parsed["case_exit_rows"] == 1


def test_letter_suffixed_section_number_is_matched():
    parsed = audit_caseplan.parse_sdd(
        SDD.replace("### Case Exit Conditions", "### 1.4a Case Exit Conditions")
    )
    assert parsed["parse_notes"] == [] and parsed["case_exit_rows"] == 1


def test_completion_conditions_spelling_is_matched():
    parsed = audit_caseplan.parse_sdd(
        SDD.replace("### Case Exit Conditions", "### Case Completion Conditions")
        .replace("#### Stage Exit Conditions", "#### Stage Completion Conditions")
    )
    assert parsed["parse_notes"] == []
    assert parsed["case_exit_rows"] == 1
    assert parsed["stages"][0]["exit_rows"] == 1


def test_bare_triggers_heading_is_matched():
    parsed = audit_caseplan.parse_sdd(SDD.replace("### Case Triggers", "### Triggers"))
    assert parsed["parse_notes"] == [] and parsed["triggers"] == 1


def test_tasks_table_without_a_name_column_is_reported():
    """A `| # | Task Title | ...` header parses zero tasks; deleting every task
    from the caseplan would otherwise yield MISSING: []."""
    parsed = audit_caseplan.parse_sdd(SDD.replace("| Task Name |", "| Task Title |"))
    assert parsed["stages"][0]["tasks"] == []
    assert any("no Task Name/Task/Name column" in n for n in parsed["parse_notes"])


def test_case_variables_table_without_a_name_column_is_reported():
    parsed = audit_caseplan.parse_sdd(SDD.replace("| Name | Category |", "| Key | Category |"))
    assert parsed["variables"] == []
    assert any("no Name/Variable/Variable Name column" in n for n in parsed["parse_notes"])


def test_renamed_tasks_heading_is_reported():
    parsed = audit_caseplan.parse_sdd(SDD.replace("#### Tasks", "#### Stage Task Summary"))
    assert parsed["stages"][0]["tasks"] == []
    assert any("'Stage Task Summary'" in n for n in parsed["parse_notes"])


def test_lookalike_heading_is_quiet_when_its_class_is_already_populated():
    """An appendix `### Process Variables` next to a parsed `### Case Variables`
    feeds nothing and must not be reported."""
    parsed = audit_caseplan.parse_sdd(
        SDD + "\n### Process Variables\n\n| Variable | Type |\n|---|---|\n| tmp | string |\n"
    )
    assert parsed["parse_notes"] == [] and parsed["variables"] == ["orderId"]


def test_lookalike_heading_is_reported_when_its_class_is_empty():
    parsed = audit_caseplan.parse_sdd(SDD.replace("### Case Variables", "### Process Variables"))
    assert parsed["variables"] == []
    assert any("'Process Variables'" in n for n in parsed["parse_notes"])


def test_cli_fails_on_a_degraded_parse(tmp_path, capsys):
    with pytest.raises(SystemExit) as excinfo:
        _run_cli(tmp_path, SDD.replace("| Task Name |", "| Task Title |"))
    assert excinfo.value.code == 1
    err = capsys.readouterr().err
    assert "did not parse cleanly" in err
    assert "Repair the SDD, not caseplan.json" in err
