"""Checker-level tests for check_billing_invoice_lookup.py.

Only `run_debug` is replaced. The flow on disk is the task's reference flow,
with its variables renamed the way an agent might name them, so the mapping by
meaning and the trace lookups run for real. The fake debug answers each input the way the live tenant does (8 rows for
MCS-2026-04872, 4 for MCS-2026-04903, 5 for MCS-2026-05128, none for 99999),
in the `Data` shape `uip maestro flow debug --output json` returns.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
CHECKER = HERE / "check_billing_invoice_lookup.py"
REFERENCE_FLOW = HERE / "BillingInvoiceLookup.reference.flow"
QUERY_ID = "erpQuery"  # the reference flow's query-entity-records node
LIVE_COUNTS = {"MCS-2026-04872": 8, "MCS-2026-04903": 4, "MCS-2026-05128": 5}
RENAMES = {"invoiceNumber": "rawInvoiceRef", "matchedInvoiceNumber": "invoiceOnRecord",
           "lineItemCount": "lines"}


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_billing_invoice_lookup", CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_flow(project, renames):
    text = REFERENCE_FLOW.read_text()
    for old, new in renames.items():
        text = text.replace(f'"{old}"', f'"{new}"').replace(f".{old}", f".{new}")
    (project / "new.flow").write_text(text)


@pytest.fixture
def project(tmp_path, monkeypatch):
    project = tmp_path / "BillingInvoiceLookup" / "BillingInvoiceLookup"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text(json.dumps({"ProjectType": "Flow"}))
    _write_flow(project, RENAMES)
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
        "variables": {"globals": {"rawInvoiceRef": raw, "invoiceOnRecord": matched, "lines": count}},
    }


def _live(raw):
    invoice = _clean(raw)
    if invoice not in LIVE_COUNTS:
        return _payload(raw, "", 0)
    return _payload(raw, invoice, LIVE_COUNTS[invoice])


def _run(monkeypatch, case, answer):
    checker = _load_checker()
    sent = []

    def fake(*, inputs, **_):
        sent.append(inputs)
        return answer(inputs["rawInvoiceRef"])

    monkeypatch.setattr(checker, "run_debug", fake)
    monkeypatch.setattr("sys.argv", ["check", case])
    checker.main()
    return sent


def test_a_flow_that_cleans_up_and_queries_passes(project, monkeypatch, capsys):
    sent = _run(monkeypatch, "found", _live)
    assert [s["rawInvoiceRef"] for s in sent] == ["2026-04872", "mcs-2026-04903", "  mcs-2026-05128 "]
    assert "all 3 messy forms" in capsys.readouterr().out


def test_a_hardcoded_count_of_8_fails(project, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "found", lambda raw: _payload(raw, _clean(raw), 8))
    assert "line count 4" in str(exc.value)


def test_a_number_left_lowercase_fails(project, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "found", lambda raw: _payload(raw, raw.strip(), LIVE_COUNTS[_clean(raw)]))
    assert "MCS-2026-04872 exactly" in str(exc.value)


def test_a_query_that_did_not_complete_fails(project, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "found",
             lambda raw: _payload(raw, _clean(raw), LIVE_COUNTS[_clean(raw)], query_status="Faulted"))
    assert "no entity read completed" in str(exc.value)


def test_not_found_returns_empty_text_and_zero(project, monkeypatch):
    _run(monkeypatch, "not-found", _live)


def test_not_found_echoing_the_cleaned_number_fails(project, monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "not-found", lambda raw: _payload(raw, _clean(raw), 0))
    assert "expected empty text and 0" in str(exc.value)


def test_not_found_with_the_invoice_output_never_set_fails(project, monkeypatch):
    def unset(raw):
        payload = _payload(raw, "", 0)
        del payload["variables"]["globals"]["invoiceOnRecord"]
        return payload

    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "not-found", unset)
    assert "expected empty text and 0" in str(exc.value)


def test_a_single_text_input_is_used_whatever_its_name(project, monkeypatch):
    _write_flow(project, {**RENAMES, "invoiceNumber": "q"})
    checker = _load_checker()
    sent = []
    monkeypatch.setattr(checker, "run_debug", lambda *, inputs, **_: sent.append(inputs) or _live(inputs["q"]))
    monkeypatch.setattr("sys.argv", ["check", "not-found"])
    checker.main()
    assert sent == [{"q": "mcs-2026-99999"}]
