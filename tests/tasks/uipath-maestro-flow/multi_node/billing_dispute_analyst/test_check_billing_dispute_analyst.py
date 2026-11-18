"""Checker-level tests for check_billing_dispute_analyst.py.

Only `run_debug` is replaced. The flow on disk is the task's reference flow
(an inline agent wired to the SOP context index), so the source and trace
lookups run for real. Payloads are in the `Data` shape `uip maestro flow debug
--output json` returns; the 2026-11-17 Studio Web run of this task returned
`determination: "needs_review"` with an SOP-citing rationale in that shape.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_dispute_analyst.py"
REFERENCE_FLOW = HERE / "BillingDisputeAnalyst.reference.flow"
AGENT_ID = "disputeAnalyst"  # the reference flow's uipath.agent.autonomous node


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_dispute_analyst", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    project = tmp_path / "BillingDisputeAnalyst" / "BillingDisputeAnalyst"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    shutil.copy(REFERENCE_FLOW, project / "new.flow")
    monkeypatch.chdir(tmp_path)
    return project


def _payload(*, action, credit, agent_status="Completed", rationale="Per SOP §5.4 and §7 ..."):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "status": "Completed"},
            {"elementId": AGENT_ID, "status": agent_status},
            {"elementId": "doneSuccess", "status": "Completed"},
        ],
        "variables": {
            "globals": {
                "invoiceNumber": "MCS-2026-04903",
                "disputeDescription": "90 hours billed at $290 ... contracts $235",
                "determination": "valid_overcharge",
                "recommendedAction": action,
                "creditAmount": credit,
                "rationale": rationale,
            }
        },
    }


def _run(case, payload, monkeypatch):
    checker = _load_checker()
    monkeypatch.setattr(checker, "run_debug", lambda **_: payload)
    monkeypatch.setattr("sys.argv", ["check", case])
    checker.main()


@pytest.mark.parametrize("action", ["manager_review", "escalate_to_manager", "Manager Review"])
def test_rate_error_routed_to_manager_review_with_the_sop_credit_passes(sandbox, monkeypatch, capsys, action):
    _run("overcharge", _payload(action=action, credit=4950), monkeypatch)
    assert "creditAmount=4950" in capsys.readouterr().out


def test_credit_returned_as_text_passes(sandbox, monkeypatch):
    _run("overcharge", _payload(action="manager_review", credit="$4,950.00"), monkeypatch)


def test_rate_error_auto_resolved_fails(sandbox, monkeypatch):
    # $4,950 sits in the SOP's $500-$5,000 band; auto-resolve means the SOP was not read.
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", _payload(action="auto_resolve", credit=4950), monkeypatch)
    assert "recommendedAction" in str(exc.value)


def test_wrong_credit_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", _payload(action="manager_review", credit=26100), monkeypatch)
    assert "creditAmount" in str(exc.value)


def test_agent_that_did_not_complete_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", _payload(action="manager_review", credit=4950, agent_status="Faulted"), monkeypatch)
    assert "did not complete" in str(exc.value)


@pytest.mark.parametrize("credit", [0, None, "0.00"])
def test_line_at_contract_rejected_without_credit_passes(sandbox, monkeypatch, credit):
    _run("reject", _payload(action="reject", credit=credit), monkeypatch)


def test_line_at_contract_with_a_credit_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("reject", _payload(action="reject", credit=2590), monkeypatch)
    assert "contracted rate" in str(exc.value)


def test_line_at_contract_sent_to_review_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("reject", _payload(action="manager_review", credit=0), monkeypatch)
    assert "recommendedAction" in str(exc.value)
