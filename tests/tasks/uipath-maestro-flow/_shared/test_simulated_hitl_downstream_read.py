"""Regression tests for the `expense` check's "downstream reads the HITL answer" rule.

Fixture `testdata/expense_hitl_variable_updates.flow` is the verbatim `.flow`
from v2 run 2026-09-24_05-12-05, skill-flow-expense-approval-simulated/02.
`uip maestro flow validate` accepts it. It captures the HITL answer through
`variables.variableUpdates` (`rejectionReason: $vars.managerReview.output.rejectionReason`)
and the downstream script reads `$vars.rejectionReason` — the shape preview
hitl.md recommends and the SDK emits for `{ updates }`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
SCRIPT = SHARED / "check_simulated_hitl.py"
FIXTURE = SHARED / "testdata" / "expense_hitl_variable_updates.flow"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def run_expense(flow: dict, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    (tmp_path / "ExpenseApproval.flow").write_text(json.dumps(flow))
    return subprocess.run(
        [sys.executable, str(SCRIPT), "expense"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def node(flow: dict, node_id: str) -> dict:
    return next(n for n in flow["nodes"] if n["id"] == node_id)


def test_variable_updates_capture_read_by_script_passes(tmp_path: Path) -> None:
    result = run_expense(load_fixture(), tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: expense HITL" in result.stdout


def test_variable_updates_capture_read_by_end_mapping_passes(tmp_path: Path) -> None:
    flow = load_fixture()
    # Script no longer reads the captured variable; only the end mapping does.
    node(flow, "logDecision")["inputs"]["script"] = "return { decision: $vars.decision };"
    result = run_expense(flow, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr


def test_no_read_of_hitl_output_fails(tmp_path: Path) -> None:
    flow = load_fixture()
    # Control: drop every capture of $vars.managerReview.output.
    for entries in flow["variables"]["variableUpdates"].values():
        entries[:] = [
            e for e in entries
            if "$vars.managerReview.output" not in e["expression"]["expression"]
        ]
    result = run_expense(flow, tmp_path)
    assert result.returncode != 0
    assert "must read HITL output" in result.stdout + result.stderr


def test_captured_variable_never_read_downstream_fails(tmp_path: Path) -> None:
    flow = load_fixture()
    # The capture exists, but nothing downstream reads `rejectionReason`.
    node(flow, "logDecision")["inputs"]["script"] = "return { decision: $vars.decision };"
    del node(flow, "end")["outputs"]["rejectionReason"]
    result = run_expense(flow, tmp_path)
    assert result.returncode != 0
    assert "must read HITL output" in result.stdout + result.stderr


def test_prefix_named_variable_does_not_count_as_a_read(tmp_path: Path) -> None:
    flow = load_fixture()
    node(flow, "logDecision")["inputs"]["script"] = "return $vars.rejectionReasonOld;"
    del node(flow, "end")["outputs"]["rejectionReason"]
    result = run_expense(flow, tmp_path)
    assert result.returncode != 0


def test_direct_script_read_still_passes(tmp_path: Path) -> None:
    flow = load_fixture()
    del flow["variables"]["variableUpdates"]
    node(flow, "logDecision")["inputs"]["script"] = (
        "return $vars.managerReview.output.rejectionReason;"
    )
    result = run_expense(flow, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
