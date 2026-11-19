"""check_invoice_lookup_run.py grades each run's named outputs and its Data
Service step.

`fixtures/Process.bpmn` is the agent's process from Studio Web run
adhoc-2026-11-17_15-00-15 (passed). The runtime payloads are rebuilt in the
shape that run's `debug-instances variables` printed: PascalCase Globals with
GlobalDefinitions naming them, the query's rows under the query element's
`Response`, and the end event's own `Outputs`.
"""

from __future__ import annotations

import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BPMN = HERE / "fixtures" / "Process.bpmn"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


checker = _load("check_invoice_lookup_run", HERE / "check_invoice_lookup_run.py")
from _shared.bpmn_live import DebugEvidence, input_echo_ids, output_leaves  # noqa: E402

PROCESS = ET.parse(BPMN).getroot().find(f"{{{checker.BPMN_NS}}}process")
QUERY_IDS = checker.data_service_ids(PROCESS)


def _debug(query_status="Completed"):
    return {
        "InstanceId": "d808d1d3-a688-4fde-b420-a9a06f8e53a3",
        "FinalStatus": "Completed",
        "ElementExecutions": [
            {"ElementId": "Event_start", "ElementType": "StartEvent", "Status": "Completed"},
            {"ElementId": "normalizeInvoiceNumber", "ElementType": "ScriptTask", "Status": "Completed"},
            {"ElementId": "queryBillingDisputeERP", "ElementType": "SendTask", "Status": query_status},
            {"ElementId": "shapeLookupOutputs", "ElementType": "ScriptTask", "Status": "Completed"},
            {"ElementId": "done", "ElementType": "EndEvent", "Status": "Completed"},
        ],
    }


def _variables(raw: str, invoice: str, count: int, *, outputs=True):
    rows = [{"InvoiceNumber": invoice, "LineNumber": n, "Amount": 1200} for n in range(1, count + 1)]
    end_outputs = {"LineItemCount": count, "MatchedInvoiceNumber": invoice} if outputs else {}
    return {
        "Variables": [
            {
                "ParentElementId": None,
                "Elements": [
                    {"ElementId": "queryBillingDisputeERP", "Outputs": {"Response": rows}},
                    {"ElementId": "done", "Outputs": end_outputs},
                ],
                "Globals": {
                    "InvoiceNumber": raw,
                    "NormalizedInvoiceNumber": invoice,
                    "QueryResponse": rows,
                    "QueryError": None,
                    "MatchedInvoiceNumberValue": invoice if outputs else None,
                    "LineItemCountValue": count if outputs else None,
                    "MatchedInvoiceNumber": invoice if outputs else None,
                    "LineItemCount": count if outputs else None,
                },
                "GlobalDefinitions": {
                    "MatchedInvoiceNumber": {"Name": "matchedInvoiceNumber", "Type": "string"},
                    "LineItemCount": {"Name": "lineItemCount", "Type": "number"},
                    "LineItemCountValue": {"Name": "lineItemCountValue", "Type": "number"},
                },
            }
        ]
    }


@pytest.mark.parametrize(("raw", "invoice", "count", "label"), checker.CASES)
def test_real_shape_passes_every_case(raw, invoice, count, label):
    checker.check_run(PROCESS, QUERY_IDS, _debug(), _variables(raw, invoice, count), invoice, count, label)


def test_the_data_service_step_is_found_by_connector_key():
    assert QUERY_IDS == {"queryBillingDisputeERP"}


def test_outputs_are_read_by_name_not_found_among_every_value():
    """A run that queried the entity but returned neither output: the query's
    rows still carry the invoice number and LineNumber 8."""
    variables = _variables("2026-04872", "MCS-2026-04872", 8, outputs=False)
    leaves = output_leaves(variables, skip=input_echo_ids(PROCESS))
    assert "MCS-2026-04872" in leaves and 8 in leaves
    with pytest.raises(checker.CheckFailure, match="matchedInvoiceNumber"):
        checker.check_run(PROCESS, QUERY_IDS, _debug(), variables, "MCS-2026-04872", 8, "missing prefix")


def test_wrong_count_fails():
    variables = _variables("mcs-2026-05128", "MCS-2026-05128", 8)
    with pytest.raises(checker.CheckFailure, match="lineItemCount: expected 5"):
        checker.check_run(PROCESS, QUERY_IDS, _debug(), variables, "MCS-2026-05128", 5, "wrong casing")


def test_a_run_whose_query_did_not_complete_fails():
    with pytest.raises(checker.CheckFailure, match="no Data Service step"):
        checker.check_run(
            PROCESS, QUERY_IDS, _debug(query_status="Faulted"),
            _variables("2026-04872", "MCS-2026-04872", 8), "MCS-2026-04872", 8, "missing prefix",
        )


def test_end_event_outputs_alone_are_enough():
    variables = _variables("2026-04872", "MCS-2026-04872", 8)
    scope = variables["Variables"][0]
    scope["Globals"] = {"InvoiceNumber": "2026-04872"}
    scope["GlobalDefinitions"] = {}
    checker.check_run(PROCESS, QUERY_IDS, _debug(), variables, "MCS-2026-04872", 8, "missing prefix")


def test_main_runs_every_case_in_a_studio_web_layout(tmp_path, monkeypatch):
    project = tmp_path / "BillingInvoiceLookup" / "BillingInvoiceLookup"
    project.mkdir(parents=True)
    (project / "project.uiproj").write_text('{"Name": "BillingInvoiceLookup", "ProjectType": "ProcessOrchestration"}')
    (project / "Process.bpmn").write_text(BPMN.read_text())
    monkeypatch.chdir(tmp_path)

    sent = []
    cases = iter(checker.CASES)
    current = {}

    def fake_debug(project_dir, inputs, log, **kwargs):
        sent.append(inputs)
        current["case"] = next(cases)
        return _debug(), "inst"

    def fake_evidence(instance_id):
        raw, invoice, count, _ = current["case"]
        return DebugEvidence(_variables(raw, invoice, count), "", [], [])

    monkeypatch.setattr(checker, "import_exact", lambda bpmn, project_dir, solution: project_dir)
    monkeypatch.setattr(checker, "run_debug", fake_debug)
    monkeypatch.setattr(checker, "debug_evidence", fake_evidence)
    checker.main()
    assert sent == [{"invoiceNumber": raw} for raw, *_ in checker.CASES]
