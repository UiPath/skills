"""Unit tests for check_connector_stub_halt.py — the Check 15 grader.

Run with ``pytest`` from any directory; CI runs them via the
``maestro-case checker unit tests`` job (``pytest tests/tasks/uipath-maestro-case/``).

Every fixture here is a MINIMAL SYNTHETIC STUB built inline — the smallest
caseplan that carries the fatal shape (root + one stage + one placeholder
`wait-for-connector` rule). No real or captured build artifact is involved, so
these run anywhere, need no tenant, and cannot rot when a sample case changes.

What the grader must get right
------------------------------
A surviving placeholder connector-rule stub makes the ENTIRE case non-startable:
subscriptions register at case start, so one stub anywhere kills the case's own
start event even when it sits on a stage nothing routes to. `uip maestro case
validate` reports `Valid` either way, so the grader is the only signal.

  branch A  no stub survives, plan coherent      -> pass
  branch B  stub survives AND BLOCKED marker     -> pass (the build halted)
  FAIL      stub survives, no BLOCKED marker     -> the pre-fix regression
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

CHECKER = Path(__file__).with_name("check_connector_stub_halt.py")

BLOCKED_LINE = (
    "BLOCKED: case is not startable — 1 unresolved wait-for-connector rule(s) "
    "still carry the placeholder stub."
)

STUB_UIPATH = {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [
        {"name": "connectorKey", "value": "placeholder", "type": "string"},
        {"name": "operation", "value": "placeholder", "type": "string"},
    ],
    "inputs": [],
    "outputs": [],
    "bindings": [],
}

RESOLVED_UIPATH = {
    "serviceType": "Intsvc.WaitForEvent",
    "context": [
        {"name": "connectorKey", "value": "uipath-mock-element", "type": "string"},
        {"name": "connection", "value": "=bindings.bA1B2C3D4", "type": "string"},
        {"name": "objectName", "value": "tokens", "type": "string"},
        {"name": "operation", "value": "TOKEN_CREATED", "type": "string"},
    ],
    "inputs": [],
    "outputs": [],
    "bindings": [],
}


def connector_rule(uipath):
    return {"id": "Rule_aaaaaa", "rule": "wait-for-connector", "uipath": uipath}


def caseplan(*, stage_entry=None, stage_exit=None, task_entry=None, case_exit=None):
    """Smallest caseplan that can carry a rule in any of the four scopes."""
    task = {"id": "tAAAAAAAA", "type": "wait-for-timer", "displayName": "Hold"}
    if task_entry is not None:
        task["entryConditions"] = [
            {"id": "cAAAAAAAA", "displayName": "Task entry", "rules": [[task_entry]]}
        ]

    stage = {
        "id": "Stage_aaaaaa",
        "type": "case-management:Stage",
        "data": {
            "label": "Watch",
            "isRequired": False,
            "stageType": "secondary",
            "tasks": [[task]],
        },
    }
    if stage_entry is not None:
        stage["data"]["entryConditions"] = [
            {"id": "Condition_aaaaaa", "displayName": "Entry", "rules": [[stage_entry]]}
        ]
    if stage_exit is not None:
        stage["data"]["exitConditions"] = [
            {
                "id": "Condition_bbbbbb",
                "displayName": "Exit",
                "type": "exit-only",
                "marksStageComplete": True,
                "rules": [[stage_exit]],
            }
        ]

    metadata = {"caseIdentifier": "STB"}
    if case_exit is not None:
        metadata["caseExitRules"] = [
            {
                "id": "Condition_cccccc",
                "displayName": "Done",
                "marksCaseComplete": True,
                "rules": [[case_exit]],
            }
        ]

    return {
        "id": "case-Stub000001",
        "version": "27.0.0",
        "name": "Stub",
        "metadata": metadata,
        "bindings": [],
        "variables": {"inputs": [], "outputs": [], "inputOutputs": []},
        "nodes": [stage],
        "edges": [],
        "layout": {},
    }


def run_checker(tmp_path, case=None, issues=None, nested="Sol/Proj"):
    """Lay the stub out on disk the way a real build would, then grade it."""
    if case is not None:
        project = tmp_path / nested
        project.mkdir(parents=True, exist_ok=True)
        (project / "caseplan.json").write_text(json.dumps(case, indent=2))
    if issues is not None:
        tasks_dir = tmp_path / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        (tasks_dir / "build-issues.md").write_text(issues)

    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )


# --- the regression this test exists for --------------------------------------------

def test_surviving_stub_without_marker_fails(tmp_path):
    """Pre-fix behaviour: emit the dead case, report it complete. Must FAIL."""
    res = run_checker(tmp_path, case=caseplan(stage_entry=connector_rule(STUB_UIPATH)))
    assert res.returncode == 1, res.stdout
    assert "no Check 15 BLOCKED marker" in res.stdout


def test_surviving_stub_with_marker_passes(tmp_path):
    """Post-fix branch B: the stub is still there, but the build halted."""
    res = run_checker(
        tmp_path,
        case=caseplan(stage_entry=connector_rule(STUB_UIPATH)),
        issues=f"# Build Issues\n\n{BLOCKED_LINE}\n\n## Open Items for User\n",
    )
    assert res.returncode == 0, res.stdout
    assert "PASS (branch B)" in res.stdout


def test_resolved_connector_passes(tmp_path):
    """Post-fix branch A: the connector resolved, so nothing is fatal."""
    res = run_checker(tmp_path, case=caseplan(stage_entry=connector_rule(RESOLVED_UIPATH)))
    assert res.returncode == 0, res.stdout
    assert "PASS (branch A)" in res.stdout


def test_rule_removed_entirely_passes(tmp_path):
    """Branch A via removal: no connector rule at all."""
    case = caseplan()
    case["nodes"][0]["data"]["entryConditions"] = [
        {
            "id": "Condition_aaaaaa",
            "displayName": "Entry",
            "rules": [[{"id": "Rule_bbbbbb", "rule": "case-entered"}]],
        }
    ]
    res = run_checker(tmp_path, case=case)
    assert res.returncode == 0, res.stdout
    assert "PASS (branch A)" in res.stdout


# --- scope coverage: a stub in ANY of the four scopes is fatal -----------------------

@pytest.mark.parametrize("scope", ["stage_entry", "stage_exit", "task_entry", "case_exit"])
def test_stub_detected_in_every_condition_scope(tmp_path, scope):
    res = run_checker(tmp_path, case=caseplan(**{scope: connector_rule(STUB_UIPATH)}))
    assert res.returncode == 1, f"{scope} stub went undetected:\n{res.stdout}"
    assert "surviving placeholder connector-rule stubs: 1" in res.stdout


def test_partial_stub_counts_as_a_stub(tmp_path):
    """Only `operation` left as placeholder — still not runnable, still fatal."""
    half = dict(RESOLVED_UIPATH)
    half["context"] = [
        {"name": "connectorKey", "value": "uipath-mock-element", "type": "string"},
        {"name": "operation", "value": "placeholder", "type": "string"},
    ]
    res = run_checker(tmp_path, case=caseplan(stage_entry=connector_rule(half)))
    assert res.returncode == 1, res.stdout


# --- the marker must be the real one, not any mention of the problem ----------------

def test_open_item_mention_is_not_a_halt(tmp_path):
    """The pre-fix skill DID log the stub — as a routine Open Item. Not a halt."""
    res = run_checker(
        tmp_path,
        case=caseplan(stage_entry=connector_rule(STUB_UIPATH)),
        issues=(
            "# Build Issues\n\n## Open Items for User\n\n"
            "- The withdrawal lane can't fire; replace the placeholder connector "
            "values before debug / publish-to-run.\n"
        ),
    )
    assert res.returncode == 1, (
        "an Open Item mentioning the placeholder must NOT satisfy Check 15 — "
        "that is exactly the pre-fix output:\n" + res.stdout
    )


def test_missing_build_issues_file_is_not_a_halt(tmp_path):
    res = run_checker(tmp_path, case=caseplan(stage_entry=connector_rule(STUB_UIPATH)))
    assert res.returncode == 1
    assert "build-issues.md (missing)" in res.stdout


# --- removal must not mean gutting the plan ------------------------------------------

def test_removal_leaving_dangling_stage_reference_fails(tmp_path):
    case = caseplan()
    case["nodes"][0]["data"]["entryConditions"] = [
        {
            "id": "Condition_aaaaaa",
            "displayName": "Entry",
            "rules": [
                [
                    {
                        "id": "Rule_bbbbbb",
                        "rule": "selected-stage-exited",
                        "selectedStageId": "Stage_deleted",
                    }
                ]
            ],
        }
    ]
    res = run_checker(tmp_path, case=case)
    assert res.returncode == 1, res.stdout
    assert "points at a removed stage" in res.stdout


def test_removal_leaving_empty_rules_array_fails(tmp_path):
    case = caseplan()
    case["nodes"][0]["data"]["entryConditions"] = [
        {"id": "Condition_aaaaaa", "displayName": "Entry", "rules": []}
    ]
    res = run_checker(tmp_path, case=case)
    assert res.returncode == 1, res.stdout
    assert "empty rules array" in res.stdout


# --- environment guards ---------------------------------------------------------------

def test_no_caseplan_fails(tmp_path):
    res = run_checker(tmp_path)
    assert res.returncode == 1
    assert "no caseplan.json" in res.stdout


def test_unparseable_caseplan_fails(tmp_path):
    project = tmp_path / "Sol" / "Proj"
    project.mkdir(parents=True)
    (project / "caseplan.json").write_text("{ not json")
    res = subprocess.run(
        [sys.executable, str(CHECKER)], cwd=tmp_path, capture_output=True, text=True
    )
    assert res.returncode == 1
    assert "unreadable/unparseable" in res.stdout


def test_venv_copies_are_ignored(tmp_path):
    """A caseplan inside .venv must not be mistaken for the build output."""
    venv_project = tmp_path / ".venv" / "share" / "sample"
    venv_project.mkdir(parents=True)
    (venv_project / "caseplan.json").write_text(
        json.dumps(caseplan(stage_entry=connector_rule(STUB_UIPATH)))
    )
    res = run_checker(tmp_path, case=caseplan(stage_entry=connector_rule(RESOLVED_UIPATH)))
    assert res.returncode == 0, res.stdout
    assert ".venv" not in res.stdout
