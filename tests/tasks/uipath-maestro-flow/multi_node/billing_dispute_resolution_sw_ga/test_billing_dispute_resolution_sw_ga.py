#!/usr/bin/env python3
"""Unit tests for the Studio Web GA graders of BillingDisputeResolution.

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
_V1 = os.path.join(os.path.dirname(_HERE), "billing_dispute_resolution")
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
    _load("check_structure_billing_dispute_resolution_sw_ga.py").assert_topology(
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


@pytest.mark.parametrize("reference", REFERENCES)
def test_structure_accepts_both_reference_shapes(reference):
    _topology(_flow(reference))


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


EFFECTS = "check_effects_billing_dispute_resolution_sw_ga.py"
ALL_NODES = [n["id"] for n in _flow()["nodes"]]
REJECT_PATH = ["start", "invoiceExtraction", "dataTransform", "queryEntityRecords1", "queryEntityRecords2",
               "merge1", "discrepancyScript", "autonomousAgent1", "switchValidity", "endReject"]


@pytest.fixture
def effects(monkeypatch):
    module = _load(EFFECTS)
    monkeypatch.setattr(module, "_declared_input_global_keys", lambda payload: set())
    return module


POSTED = {"financialpostingfunction12.output": {
    "result": "Credit memo posted successfully. Invoice: 'MCS-2026-04872'. Status: posted."}}


def test_overcharge_passes_when_posted_and_the_draft_cites_invoice_and_credit(effects):
    effects.check_overcharge(_flow(), _payload(ALL_NODES, {
        **POSTED,
        "creditAmount": 1610,
        "resolutionEmailBody": "We credited $1,610.00 on invoice MCS-2026-04872.",
    }))


def test_overcharge_fails_when_the_posting_reply_is_for_another_invoice(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(_flow(), _payload(ALL_NODES, {
            "financialpostingfunction12.output": {"result": "Credit memo posted. Invoice: 'MCS-2026-00001'."},
            "creditAmount": 1610,
            "resolutionEmailBody": "We credited $1,610.00 on invoice MCS-2026-04872.",
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
            "creditAmount": 1610,
            "resolutionEmailBody": "We reviewed invoice MCS-2026-04872 and issued a credit.",
        }))
    assert "credit amount" in str(exc.value)


def test_no_discrepancy_passes_on_the_rejection_path(effects):
    effects.check_no_discrepancy(_flow(), _payload(REJECT_PATH, {
        "rationale": "Line 4 was billed at the contracted rate.",
        "resolutionEmailBody": "No resolution email was drafted.",
    }))


def test_no_discrepancy_fails_when_it_was_posted(effects):
    with pytest.raises(SystemExit) as exc:
        effects.check_no_discrepancy(_flow(), _payload(ALL_NODES, {"rationale": "credited anyway"}))
    assert "FinancialPostingFunction ran" in str(exc.value)


WINDOW = {"invoice": "MCS-2026-04872", "startedAt": "2026-11-18T10:00:00Z", "endedAt": "2026-11-18T10:05:00Z"}


def _job(created, state="Successful", invoice="MCS-2026-04872"):
    return {"key": "k", "state": state, "creationTime": created,
            "inputArguments": json.dumps({"invoiceNumber": invoice})}


def test_probe_keeps_only_jobs_in_the_window_for_the_invoice():
    probe = _load("probe_posting_jobs_sw_ga.py")
    jobs = [_job("2026-11-18T10:02:00Z"), _job("2026-11-18T09:59:00Z"),
            _job("2026-11-18T10:05:30.5Z"), _job("2026-11-18T10:03:00Z", invoice="MCS-2026-05128")]
    kept = probe.jobs_in_window(jobs, WINDOW)
    assert [j["creationTime"] for j in kept] == ["2026-11-18T10:02:00Z", "2026-11-18T10:05:30.5Z"]


def test_probe_verdicts():
    probe = _load("probe_posting_jobs_sw_ga.py")
    assert probe.verdict("overcharge", [_job("t")]) is None
    assert "no Successful" in probe.verdict("overcharge", [_job("t", state="Faulted")])
    assert probe.verdict("no-discrepancy", []) is None
    assert "must not post" in probe.verdict("no-discrepancy", [_job("t")])
