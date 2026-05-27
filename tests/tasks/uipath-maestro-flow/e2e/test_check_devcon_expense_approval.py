"""Tests for the DevCon expense approval semantic checker."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


CHECKER = Path(__file__).with_name("check_devcon_expense_approval.py")


def _flow_doc(
    *,
    fields: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    script_body: str = "return $vars.reviewExpense.output.rejectionreason;",
) -> dict[str, Any]:
    return {
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
                        "fields": fields,
                        "outcomes": outcomes,
                    }
                },
            },
            {
                "id": "logOutcome",
                "type": "core.action.script",
                "inputs": {"script": script_body},
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


def _write_flow(tmp_path: Path, doc: dict[str, Any]) -> None:
    project = tmp_path / "ExpenseApproval" / "ExpenseApproval"
    project.mkdir(parents=True)
    (project / "ExpenseApproval.flow").write_text(json.dumps(doc), encoding="utf-8")


def _approve_reject_fields(binding: str) -> list[dict[str, Any]]:
    return [
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
    ]


_APPROVE_REJECT_OUTCOMES: list[dict[str, Any]] = [
    {"id": "approve", "name": "Approve"},
    {"id": "reject", "name": "Reject"},
]


def _write_approve_reject_flow(tmp_path: Path, binding: str) -> None:
    _write_flow(
        tmp_path,
        _flow_doc(
            fields=_approve_reject_fields(binding),
            outcomes=_APPROVE_REJECT_OUTCOMES,
        ),
    )


def _run_checker(tmp_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )


def test_accepts_documented_raw_hitl_input_binding(tmp_path: Path) -> None:
    _write_approve_reject_flow(tmp_path, "vars.fetchExpense.output.amount")

    result = _run_checker(tmp_path)

    assert result.returncode == 0, result.stderr


def test_accepts_expression_hitl_input_binding(tmp_path: Path) -> None:
    _write_approve_reject_flow(tmp_path, "=js:$vars.fetchExpense.output.amount")

    result = _run_checker(tmp_path)

    assert result.returncode == 0, result.stderr


def test_rejects_hardcoded_hitl_input_binding(tmp_path: Path) -> None:
    _write_approve_reject_flow(tmp_path, "hardcoded-value")

    result = _run_checker(tmp_path)

    assert result.returncode != 0
    assert "HITL input bindings must use" in result.stderr


def test_rejects_hitl_input_binding_without_output_segment(tmp_path: Path) -> None:
    _write_approve_reject_flow(tmp_path, "vars.fetchExpense.amount")

    result = _run_checker(tmp_path)

    assert result.returncode != 0
    assert "HITL input bindings must use" in result.stderr


def test_accepts_boolean_decision_with_single_submit_outcome(tmp_path: Path) -> None:
    """The docstring promises the boolean-decision pattern is valid; lock it in.

    Mirrors the HITL skill's data-enrichment example (single Submit outcome with
    a boolean output field carrying the decision). Used by agents that translate
    "approved yes/no" literally from the user's prompt.
    """
    fields = [
        {
            "id": "amount",
            "label": "Amount",
            "type": "number",
            "direction": "input",
            "binding": "vars.fetchExpense.output.amount",
        },
        {
            "id": "approved",
            "label": "Approved",
            "type": "boolean",
            "direction": "output",
            "required": True,
        },
        {
            "id": "rejectionreason",
            "label": "Rejection Reason",
            "type": "text",
            "direction": "output",
        },
    ]
    _write_flow(
        tmp_path,
        _flow_doc(
            fields=fields,
            outcomes=[
                {
                    "id": "submit",
                    "name": "Submit",
                    "type": "string",
                    "isPrimary": True,
                    "action": "Continue",
                }
            ],
            script_body=(
                "return { approved: $vars.reviewExpense.output.approved, "
                "reason: $vars.reviewExpense.output.rejectionreason };"
            ),
        ),
    )

    result = _run_checker(tmp_path)

    assert result.returncode == 0, result.stderr


def test_rejects_empty_outcomes(tmp_path: Path) -> None:
    _write_flow(
        tmp_path,
        _flow_doc(
            fields=_approve_reject_fields("vars.fetchExpense.output.amount"),
            outcomes=[],
        ),
    )

    result = _run_checker(tmp_path)

    assert result.returncode != 0
    assert "HITL schema must define outcomes" in result.stderr


def test_rejects_single_submit_outcome_without_decision_capture(tmp_path: Path) -> None:
    """One outcome named Submit + no boolean decision field must still fail —
    the disjunctive decision-capture check at the bottom of the script enforces this."""
    _write_flow(
        tmp_path,
        _flow_doc(
            fields=_approve_reject_fields("vars.fetchExpense.output.amount"),
            outcomes=[
                {
                    "id": "submit",
                    "name": "Submit",
                    "type": "string",
                    "isPrimary": True,
                    "action": "Continue",
                }
            ],
        ),
    )

    result = _run_checker(tmp_path)

    assert result.returncode != 0
    assert "manager decision" in result.stderr
