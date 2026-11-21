"""Checker-level tests for check_billing_discrepancy_detector.py.

Only `run_debug` is replaced. The flow on disk is the task's reference flow
(ERP and CRM Data Service reads), with its variables renamed the way an agent
might name them, so the mapping by meaning and the reading by value run for
real. Payloads are in the `Data` shape
`uip maestro flow debug --output json` returns.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_discrepancy_detector.py"
REFERENCE_FLOW = HERE / "BillingDiscrepancyDetector.reference.flow"
READS = ("erpQuery", "crmQuery")  # the reference's ERP and CRM reads

# The reference's names -> names an agent might pick instead.
RENAMES = {
    "invoiceNumber": "invoiceNo",
    "accountNumber": "customerAccount",
    "disputedLineNumber": "lineNo",
    "disputedUnitPrice": "billedRate",
    "disputedQuantity": "billedQty",
    "totalOvercharge": "overchargeUsd",
    "discrepancyCount": "discrepancies",
    "matchedInvoiceNumber": "recordInvoice",
    "accountTier": "tier",
}


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_discrepancy_detector", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    text = REFERENCE_FLOW.read_text()
    for old, new in RENAMES.items():
        text = text.replace(f'"{old}"', f'"{new}"').replace(f".{old}", f".{new}")
    project = tmp_path / "BillingDiscrepancyDetector" / "BillingDiscrepancyDetector"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    (project / "new.flow").write_text(text)
    monkeypatch.chdir(tmp_path)
    return project


def _payload(inputs, outputs, *, read_status="Completed"):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "status": "Completed"},
            *({"elementId": r, "status": read_status} for r in READS),
            {"elementId": "end", "status": "Completed"},
        ],
        "variables": {"globals": {**inputs, **outputs}},
    }


def _run(case, outputs, monkeypatch, **kw):
    checker = _load_checker()
    seen = {}

    def fake(*, inputs, **_):
        seen.update(inputs)
        return _payload(inputs, outputs, **kw)

    monkeypatch.setattr(checker, "run_debug", fake)
    monkeypatch.setattr("sys.argv", ["check", case])
    checker.main()
    return seen


LIVE = {"overchargeUsd": 1610, "discrepancies": 1, "recordInvoice": "MCS-2026-04872", "tier": "Enterprise"}
NOT_FOUND = {"overchargeUsd": 0, "discrepancies": 0, "recordInvoice": "", "tier": ""}


def test_inputs_are_mapped_by_meaning_onto_agent_chosen_names(sandbox, monkeypatch):
    seen = _run("overcharge", LIVE, monkeypatch)
    assert seen == {"invoiceNo": "MCS-2026-04872", "customerAccount": "ACCT-98201-NE",
                    "lineNo": 5, "billedRate": 300, "billedQty": 14}


def test_the_live_overcharge_passes(sandbox, monkeypatch, capsys):
    _run("overcharge", LIVE, monkeypatch)
    assert "1610, 1, MCS-2026-04872 and Enterprise" in capsys.readouterr().out


@pytest.mark.parametrize("field,wrong", [
    ("overchargeUsd", 4200),            # billed amount, not the overcharge
    ("discrepancies", True),            # the prompt asks for 1 or 0
    ("recordInvoice", "mcs-2026-04872"),  # not as it appears in the records
    ("tier", "enterprise"),
])
def test_a_wrong_or_misformatted_result_fails(sandbox, monkeypatch, field, wrong):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", {**LIVE, field: wrong}, monkeypatch)
    assert "no declared output is" in str(exc.value)


def test_a_read_that_did_not_complete_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", LIVE, monkeypatch, read_status="Faulted")
    assert "did not complete" in str(exc.value)


@pytest.mark.parametrize("case", ["unknown-line", "unknown-customer"])
def test_not_found_returns_zeros_and_empty_text(sandbox, monkeypatch, case):
    _run(case, NOT_FOUND, monkeypatch)


def test_a_found_tier_for_an_unknown_line_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("unknown-line", {**NOT_FOUND, "tier": "Enterprise"}, monkeypatch)
    assert "returned a match" in str(exc.value)


def test_not_found_with_missing_zeros_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("unknown-customer", {**NOT_FOUND, "overchargeUsd": None, "discrepancies": None}, monkeypatch)
    assert "expected 0" in str(exc.value)


def test_not_found_with_the_text_outputs_never_set_fails(sandbox, monkeypatch):
    unset = {k: v for k, v in NOT_FOUND.items() if k not in ("recordInvoice", "tier")}
    with pytest.raises(SystemExit) as exc:
        _run("unknown-line", unset, monkeypatch)
    assert "empty outputs []" in str(exc.value)


def test_not_found_with_one_zero_and_two_empties_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("unknown-line", {**NOT_FOUND, "discrepancies": None}, monkeypatch)
    assert "expected 0" in str(exc.value)


def test_not_found_with_two_zeros_and_one_empty_fails(sandbox, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run("unknown-line", {**NOT_FOUND, "tier": None}, monkeypatch)
    assert "expected 0" in str(exc.value)


def test_a_flow_missing_an_input_reports_the_role_it_could_not_map(sandbox, monkeypatch):
    flow_path = sandbox / "new.flow"
    flow = json.loads(flow_path.read_text())
    flow["variables"]["globals"] = [v for v in flow["variables"]["globals"] if v["id"] != "billedQty"]
    flow_path.write_text(json.dumps(flow))
    with pytest.raises(SystemExit) as exc:
        _run("overcharge", LIVE, monkeypatch)
    assert "could not map billed quantity onto inputs" in str(exc.value)
