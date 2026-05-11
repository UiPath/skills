"""Tests for the DevCon expense approval semantic checker."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


CHECKER = Path(__file__).with_name("check_devcon_expense_approval.py")


def _write_flow(tmp_path: Path, binding: str) -> Path:
    project = tmp_path / "ExpenseApproval" / "ExpenseApproval"
    project.mkdir(parents=True)
    flow = project / "ExpenseApproval.flow"
    flow.write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "id": "fetchExpense",
                        "type": "core.action.script",
                        "inputs": {
                            "script": "return { amount: 42, category: 'Travel' };"
                        },
                    },
                    {
                        "id": "reviewExpense",
                        "type": "uipath.human-in-the-loop",
                        "typeVersion": "1.0",
                        "inputs": {
                            "schema": {
                                "fields": [
                                    {
                                        "id": "amount",
                                        "label": "Amount",
                                        "type": "number",
                                        "direction": "input",
                                        "binding": binding,
                                    },
                                    {
                                        "id": "rejectionreason",
                                        "label": "Rejection Reason",
                                        "type": "text",
                                        "direction": "output",
                                    },
                                ],
                                "outcomes": [
                                    {"id": "approve", "name": "Approve"},
                                    {"id": "reject", "name": "Reject"},
                                ],
                            }
                        },
                    },
                    {
                        "id": "logOutcome",
                        "type": "core.action.script",
                        "inputs": {
                            "script": "return $vars.reviewExpense.output.rejectionreason;"
                        },
                    },
                ],
                "edges": [
                    {
                        "sourceNodeId": "reviewExpense",
                        "sourcePort": "completed",
                        "targetNodeId": "logOutcome",
                        "targetPort": "input",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return flow


def _run_checker(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_accepts_documented_raw_hitl_input_binding(tmp_path: Path) -> None:
    _write_flow(tmp_path, "vars.fetchExpense.output.amount")

    result = _run_checker(tmp_path)

    assert result.returncode == 0, result.stderr


def test_accepts_expression_hitl_input_binding(tmp_path: Path) -> None:
    _write_flow(tmp_path, "=js:$vars.fetchExpense.output.amount")

    result = _run_checker(tmp_path)

    assert result.returncode == 0, result.stderr
