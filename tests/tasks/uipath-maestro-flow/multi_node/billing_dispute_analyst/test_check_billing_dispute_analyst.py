"""Checker-level tests for check_billing_dispute_analyst.py.

Only `run_debug` is replaced. The flow on disk is the task's reference flow (an
inline agent wired to the SOP context index), with its variables renamed the
way an agent might name them, so the mapping by meaning and the trace lookups
run for real. Payloads are in the `Data` shape `uip maestro flow debug
--output json` returns, with an agent output and an SOP-citing rationale
("Under SOP §5.1, ...").
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_dispute_analyst.py"
REFERENCE_FLOW = HERE / "BillingDisputeAnalyst.reference.flow"
AGENT_ID = "disputeAnalyst"  # the reference flow's uipath.agent.autonomous node
RENAMES = {"disputeDescription": "customerComplaint", "invoiceNumber": "invoiceRef",
           "determination": "decision", "rationale": "reasoning"}
REASONING = ("Per SOP §5.4 the billed rate of $290 exceeds the contracted $235, a credit of $4,950; "
             "§7 routes credits from $500 to $5,000 to manager review.")


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_dispute_analyst", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    text = REFERENCE_FLOW.read_text()
    for old, new in RENAMES.items():
        text = text.replace(f'"{old}"', f'"{new}"').replace(f".{old}", f".{new}")
    project = tmp_path / "BillingDisputeAnalyst" / "BillingDisputeAnalyst"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (project / "new.flow").write_text(text)
    monkeypatch.chdir(tmp_path)
    return project


def _payload(inputs, outputs, *, agent_status="Completed"):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "status": "Completed"},
            {"elementId": AGENT_ID, "status": agent_status},
            {"elementId": "doneSuccess", "status": "Completed"},
        ],
        "variables": {"globals": {**inputs, f"{AGENT_ID}.output": outputs, **outputs}},
    }


def _run(case, outputs, monkeypatch, **kw):
    checker = _load_checker()
    sent = {}

    def fake(*, inputs, **_):
        sent.update(inputs)
        return _payload(inputs, outputs, **kw)

    monkeypatch.setattr(checker, "run_debug", fake)
    monkeypatch.setattr("sys.argv", ["check", case])
    checker.main()
    return sent


def test_inputs_are_mapped_by_meaning(sandbox, monkeypatch):
    sent = _run("overcharge", {"decision": "manager_review", "reasoning": REASONING}, monkeypatch)
    assert sent["invoiceRef"] == "MCS-2026-04903"
    assert "90 hours billed at $290" in sent["customerComplaint"]


def test_rate_error_routed_to_manager_review_passes(sandbox, monkeypatch, capsys):
    _run("overcharge", {"decision": "manager_review", "reasoning": REASONING}, monkeypatch)
    assert "OK: the reasoning names an SOP rule" in capsys.readouterr().out


def test_a_decision_inside_an_object_output_passes(sandbox, monkeypatch):
    _run("overcharge", {"decision": {"action": "manager_review", "why": REASONING}, "reasoning": ""}, monkeypatch)


@pytest.mark.parametrize("decision", ["reject", "Manager Review", "escalate_to_manager"])
def test_rate_error_with_another_or_misspelled_decision_fails(sandbox, monkeypatch, decision):
    # The dispute is valid, so reject fails; the prompt spells the values exactly.
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", {"decision": decision, "reasoning": REASONING}, monkeypatch)
    assert "no declared output is the decision 'manager_review' or 'credit'" in str(exc.value)


def test_rate_error_routed_straight_to_credit_passes_the_gate_but_not_the_band(sandbox, monkeypatch):
    """The SOP's confidence rule decides credit vs manager review, a judgment call: the
    gate accepts either, and the advisory band check scores manager review."""
    _run("overcharge", {"decision": "credit", "reasoning": REASONING}, monkeypatch)
    band = _load_band()
    with pytest.raises(SystemExit) as exc:
        band.main()
    assert "not manager_review" in str(exc.value)


def test_the_band_check_passes_on_manager_review(sandbox, monkeypatch, capsys):
    _run("overcharge", {"decision": "manager_review", "reasoning": REASONING}, monkeypatch)
    _load_band().main()
    assert "routed to manager_review" in capsys.readouterr().out


def test_the_band_check_fails_when_no_overcharge_run_recorded_a_decision(sandbox):
    with pytest.raises(SystemExit) as exc:
        _load_band().main()
    assert "recorded no decision" in str(exc.value)


def _load_band():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "check_analyst_band", os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_analyst_band.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reasoning_that_names_no_sop_rule_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", {"decision": "manager_review",
                            "reasoning": "The rate looks higher than agreed so a manager should look."}, monkeypatch)
    assert "names an SOP rule" in str(exc.value)


def test_reasoning_that_only_mentions_the_sop_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", {"decision": "manager_review",
                            "reasoning": "Per the SOP the billed rate is above the contract, so a manager reviews it."},
             monkeypatch)
    assert "names an SOP rule" in str(exc.value)


def test_reasoning_that_names_the_rule_title_passes(sandbox, monkeypatch):
    _run("overcharge", {"decision": "manager_review",
                        "reasoning": "Under the incorrect-rate rule the billed $290 exceeds the contracted $235."},
         monkeypatch)


def test_agent_that_did_not_complete_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", {"decision": "manager_review", "reasoning": REASONING}, monkeypatch,
             agent_status="Faulted")
    assert "no agent node completed" in str(exc.value)


def test_line_at_contract_rejected_passes(sandbox, monkeypatch):
    _run("reject", {"decision": "reject",
                    "reasoning": "Under SOP §5.4 the billed $185 matches the contracted rate, so there is no variance."},
         monkeypatch)


def test_line_at_contract_sent_to_review_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("reject", {"decision": "manager_review", "reasoning": REASONING}, monkeypatch)
    assert "decision 'reject'" in str(exc.value)


def test_thin_description_goes_to_manager_review(sandbox, monkeypatch):
    sent = _run("thin", {"decision": "manager_review",
                         "reasoning": "SOP §5 needs the line, quantity and rates, which the description lacks."},
                monkeypatch)
    assert "$" not in sent["customerComplaint"]


def test_thin_description_rejected_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit):
        _run("thin", {"decision": "reject", "reasoning": "Per the SOP there is not enough to verify any charge."},
             monkeypatch)
