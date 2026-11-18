#!/usr/bin/env python3
"""Unit tests for the BillingDisputeResolution structure and effects graders.

The structure check must accept both reference shapes and the routing the
short prompt allows (manager review going straight to posting), and reject a
flow with no rejection path or with the writer before posting. The effects
check reads the debug trace; its two cases are fed payloads in the shape
`uip maestro flow debug --output json` returns.
"""
import copy
import importlib.util
import json
import os

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_V1 = _HERE
REFERENCES = ["BillingDisputeResolution.reference.flow", "BillingDisputeResolution.native.reference.flow"]


def _load(name):
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), os.path.join(_HERE, name))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _flow(reference=REFERENCES[0]):
    with open(os.path.join(_V1, reference)) as handle:
        return json.load(handle)


def _topology(flow):
    _load("check_structure_billing_dispute_resolution.py").assert_topology(
        {n["id"]: n for n in flow["nodes"]}, flow["edges"]
    )


def _without_decision(flow):
    """Manager review routed straight to posting: the decision node is gone."""
    flow = copy.deepcopy(flow)
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] not in {"decisionApproval", "endRejectMgr"}]
    flow["edges"] = [
        {**e, "targetNodeId": "financialpostingfunction12"} if e["targetNodeId"] == "decisionApproval" else e
        for e in flow["edges"]
        if e["sourceNodeId"] != "decisionApproval"
    ]
    return flow


def test_structure_accepts_manager_review_routed_straight_to_posting():
    _topology(_without_decision(_flow()))


def test_structure_rejects_a_flow_with_no_rejection_path():
    flow = _without_decision(_flow())
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] != "endReject"]
    flow["edges"] = [
        {**e, "targetNodeId": "financialpostingfunction12"} if e["targetNodeId"] == "endReject" else e
        for e in flow["edges"]
    ]
    with pytest.raises(SystemExit) as exc:
        _topology(flow)
    assert "rejection path" in str(exc.value)


def test_structure_rejects_the_writer_before_posting():
    flow = copy.deepcopy(_flow())
    flow["edges"] = [
        e for e in flow["edges"]
        if (e["sourceNodeId"], e["targetNodeId"]) not in {
            ("financialpostingfunction12", "autonomousAgent3"), ("autonomousAgent3", "endResolve")}
    ]
    flow["edges"] += [
        {"sourceNodeId": "script1", "targetNodeId": "autonomousAgent3"},
        {"sourceNodeId": "autonomousAgent3", "targetNodeId": "financialpostingfunction12"},
        {"sourceNodeId": "financialpostingfunction12", "targetNodeId": "endResolve"},
    ]
    with pytest.raises(SystemExit) as exc:
        _topology(flow)
    assert "writer" in str(exc.value)


def _payload(executed, outputs):
    return {
        "finalStatus": "Completed",
        "elementExecutions": [{"elementId": i, "status": "Completed"} for i in executed],
        "variables": {"globals": outputs},
    }


EFFECTS = "check_e2e_billing_dispute_resolution.py"
ALL_NODES = [n["id"] for n in _flow()["nodes"]]
REJECT_PATH = ["start", "invoiceExtraction", "dataTransform", "queryEntityRecords1", "queryEntityRecords2",
               "merge1", "discrepancyScript", "autonomousAgent1", "switchValidity", "endReject"]


@pytest.fixture
def effects(monkeypatch):
    module = _load(EFFECTS)
    monkeypatch.setattr(module, "_declared_input_global_keys", lambda payload: set())
    return module


POSTED = {"financialpostingfunction12.output": {
    "result": "Credit memo posted successfully. Invoice: 'MCS-2026-04903'. Status: posted."}}


def test_overcharge_passes_when_posted_and_the_draft_cites_invoice_and_credit(effects):
    effects.check_overcharge(_flow(), _payload(ALL_NODES, {
        **POSTED,
        "creditAmount": 4950,
        "resolutionEmailBody": "We credited $4,950.00 on invoice MCS-2026-04903.",
    }))


def test_overcharge_fails_when_the_posting_reply_is_for_another_invoice(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(_flow(), _payload(ALL_NODES, {
            "financialpostingfunction12.output": {"result": "Credit memo posted. Invoice: 'MCS-2026-00001'."},
            "creditAmount": 4950,
            "resolutionEmailBody": "We credited $4,950.00 on invoice MCS-2026-04903.",
        }))
    assert "reply does not cite" in str(exc.value)


def test_overcharge_fails_when_posting_did_not_run(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(_flow(), _payload(REJECT_PATH, {"creditAmount": 0, "rationale": "x"}))
    assert "FinancialPostingFunction" in str(exc.value)


def test_overcharge_fails_when_the_draft_misses_the_credit_amount(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(_flow(), _payload(ALL_NODES, {
            **POSTED,
            "creditAmount": 4950,
            "resolutionEmailBody": "We reviewed invoice MCS-2026-04903 and issued a credit.",
        }))
    assert "cites both" in str(exc.value)


def test_overcharge_fails_when_the_credit_is_not_the_sops(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(_flow(), _payload(ALL_NODES, {
            **POSTED,
            "creditAmount": 1610,
            "resolutionEmailBody": "We credited $1,610.00 on invoice MCS-2026-04903.",
        }))
    assert "credit of 4950" in str(exc.value)


def test_submission_uses_each_cases_invoice_and_account(effects):
    over, none = effects.submission("overcharge"), effects.submission("no-discrepancy")
    assert (over["invoice"]["invoiceNumber"], over["customer"]["accountNumber"]) == ("MCS-2026-04903", "ACCT-71044-AT")
    assert (none["invoice"]["invoiceNumber"], none["customer"]["accountNumber"]) == ("MCS-2026-04872", "ACCT-98201-NE")
    for case in ("overcharge", "no-discrepancy"):
        assert os.path.isfile(effects.invoice_pdf(case))


def test_no_discrepancy_passes_on_the_rejection_path(effects):
    effects.check_no_discrepancy(_flow(), _payload(REJECT_PATH, {
        "rationale": "Line 4 was billed at the contracted rate.",
        "resolutionEmailBody": "No resolution email was drafted.",
    }))


def test_no_discrepancy_fails_when_it_was_posted(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_no_discrepancy(_flow(), _payload(ALL_NODES, {"rationale": "credited anyway"}))
    assert "FinancialPostingFunction ran" in str(exc.value)



def test_overcharge_reads_a_draft_returned_as_an_object(effects):
    """A flow may return the email as {subject, body} (delegate run, 2026-11-18)."""
    effects.check_overcharge(_flow(), _payload(ALL_NODES, {
        **POSTED,
        "creditAmount": 4950,
        "resolutionEmailBody": {"subject": "Invoice MCS-2026-04903",
                                "body": "We approved a credit of $4,950.00 for invoice MCS-2026-04903."},
    }))


def _with_tenant_agent_writer(flow):
    """The writer as an existing tenant agent, as a Studio Web build did."""
    flow = copy.deepcopy(flow)
    for n in flow["nodes"]:
        if n["id"] == "autonomousAgent3":
            n["type"] = "uipath.core.agent.31cfa36d-dbc7-4be3-bbf7-000000000000"
    return flow


def test_structure_accepts_an_existing_tenant_agent_as_the_writer():
    _topology(_with_tenant_agent_writer(_flow()))


def test_no_discrepancy_catches_a_tenant_agent_writer_that_ran(effects):
    flow = _with_tenant_agent_writer(_flow())
    with pytest.raises(SystemExit) as exc:
        effects.check_no_discrepancy(flow, _payload(REJECT_PATH + ["autonomousAgent3"], {"rationale": "x"}))
    assert "writer agent ran" in str(exc.value)


def test_no_discrepancy_disputes_a_line_billed_at_its_contracted_rate(effects):
    line = effects.submission("no-discrepancy")["dispute"]["disputedLineItems"][0]
    assert (line["lineNumber"], line["quantity"], line["unitPrice"], line["amount"]) == (5, 14, 185, 2590)
