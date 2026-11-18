"""Checker-level tests for check_billing_invoice_lookup.py.

Only `run_debug` is replaced. The flow on disk is the task's reference flow, so
the source and trace lookups run for real. The fake debug answers each input
the way the live tenant does (8 rows for MCS-2026-04872, 4 for MCS-2026-04903),
in the `Data` shape `uip maestro flow debug --output json` returns.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_invoice_lookup.py"
REFERENCE_FLOW = HERE / "BillingInvoiceLookup.reference.flow"
QUERY_ID = "erpQuery"  # the reference flow's query-entity-records node
LIVE_COUNTS = {"MCS-2026-04872": 8, "MCS-2026-04903": 4}


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_invoice_lookup", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    project = tmp_path / "BillingInvoiceLookup" / "BillingInvoiceLookup"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    shutil.copy(REFERENCE_FLOW, project / "new.flow")
    monkeypatch.chdir(tmp_path)
    return project


def _clean(raw: str) -> str:
    text = raw.strip().upper()
    return text if text.startswith("MCS-") else f"MCS-{text}"


def _payload(raw, matched, count, *, query_status="Completed"):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [
            {"elementId": "start", "status": "Completed"},
            {"elementId": QUERY_ID, "status": query_status},
            {"elementId": "doneSuccess", "status": "Completed"},
        ],
        "variables": {
            "globals": {
                "invoiceNumber": raw,
                "matchedInvoiceNumber": matched,
                "lineItemCount": count,
            }
        },
    }


def _live(raw):
    invoice = _clean(raw)
    return _payload(raw, invoice, LIVE_COUNTS[invoice])


def _run(checker, monkeypatch, answer):
    monkeypatch.setattr(checker, "run_debug", lambda *, inputs, **_: answer(inputs["invoiceNumber"]))
    checker.main()


def test_a_flow_that_cleans_up_and_queries_passes(sandbox, monkeypatch, capsys):
    checker = _load_checker()
    _run(checker, monkeypatch, _live)
    assert "all 3 messy forms" in capsys.readouterr().out


def test_a_hardcoded_count_of_8_fails(sandbox, monkeypatch):
    # The old grader exercised only MCS-2026-04872, so a constant 8 passed.
    checker = _load_checker()
    with pytest.raises(SystemExit) as exc:
        _run(checker, monkeypatch, lambda raw: _payload(raw, _clean(raw), 8))
    assert "lineItemCount" in str(exc.value) and "expected 4" in str(exc.value)


def test_an_input_echo_is_not_a_matched_invoice_number(sandbox, monkeypatch):
    # The raw input is in the payload; the named output must be the cleaned-up number.
    checker = _load_checker()
    with pytest.raises(SystemExit) as exc:
        _run(checker, monkeypatch, lambda raw: _payload(raw, raw, LIVE_COUNTS[_clean(raw)]))
    assert "matchedInvoiceNumber" in str(exc.value)


def test_a_query_that_did_not_complete_fails(sandbox, monkeypatch):
    checker = _load_checker()
    with pytest.raises(SystemExit) as exc:
        _run(
            checker,
            monkeypatch,
            lambda raw: _payload(raw, _clean(raw), LIVE_COUNTS[_clean(raw)], query_status="Faulted"),
        )
    assert "no entity query completed" in str(exc.value)
