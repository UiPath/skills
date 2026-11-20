#!/usr/bin/env python3
"""Unit tests for the BillingDisputeResolution structure and effects graders.

The structure check (advisory) must accept both reference shapes and the
routing the prompt allows (manager review going straight to posting), and
reject a flow with no rejection path or with the writer before posting.

The effects check builds the dispute submission from the paths the flow reads
plus a synonym-rich fallback, so it is fed the reference flow with its
variables renamed, a flow that reads the submission only inside a script (as
an agent build did), and a flow that
spreads the submission over separate inputs. Payloads are in the shape
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
OUT_RENAMES = {"determination": "outcome", "recommendedAction": "action", "creditAmount": "creditUsd",
               "rationale": "why", "resolutionEmailBody": "draft"}
IN_RENAMES = {"webhookPayload": "claim", "disputedInvoice": "invoiceScan"}


def _renamed(flow, renames):
    text = json.dumps(flow)
    for old, new in renames.items():
        text = text.replace(f'"{old}"', f'"{new}"').replace(f".{old}", f".{new}")
    return json.loads(text)


@pytest.fixture
def effects():
    return _load(EFFECTS)


@pytest.fixture
def flow():
    return _renamed(_flow(), {**OUT_RENAMES, **IN_RENAMES})


POSTED = {"financialpostingfunction12.output": {
    "result": "Credit memo posted successfully. Invoice: 'MCS-2026-04903'. Status: posted."}}
EXPLANATION = "Per SOP §5.4 the billed $290 exceeds the contracted $235; §7 sends $4,950 to manager review."
DRAFT = "Dear Atlas Manufacturing Group,\n\nWe credited USD 4,950.00 on invoice MCS-2026-04903.\n\nBilling"
APPROVED = {"outcome": "Approved", "action": "manager_review", "creditUsd": 4950, "why": EXPLANATION, "draft": DRAFT}
REJECTED = {"outcome": "Rejected", "action": "reject", "creditUsd": 0,
            "why": "Under SOP §5.4 line 5 was billed at the contracted $185, so there is no variance to credit.",
            "draft": "No resolution email drafted"}


def test_submission_is_built_from_the_paths_the_flow_reads(effects, flow):
    inputs, attachments = effects.build_inputs(flow, "overcharge")
    claim = inputs["claim"]
    assert attachments == {"invoiceScan": effects.invoice_pdf("overcharge")}
    assert claim["customer"]["accountNumber"] == "ACCT-71044-AT"
    assert claim["invoice"]["invoiceNumber"].strip().upper() == "MCS-2026-04903"
    assert claim["invoice"]["invoiceNumber"] != "MCS-2026-04903"  # typed messily, as the prompt warns
    line = claim["dispute"]["disputedLineItems"][0]
    assert (line["lineNumber"], line["quantity"], line["unitPrice"], line["amount"]) == (2, 90, 290, 26100)


def test_a_submission_read_only_inside_a_script_is_served_by_the_fallback(effects):
    # An agent build: `const submission = $vars.start.output.disputeSubmission;` then
    # submission.customer.accountNumber / submission.dispute.disputedLineItems in the script.
    script = ("const submission = $vars.start.output.disputeSubmission;\n"
              "const accountNumber = String(submission.customer.accountNumber);")
    flow = {"nodes": [{"id": "prepareLookup", "type": "core.action.script", "inputs": {"script": script}}],
            "variables": {"globals": [
                {"id": "invoicePdf", "direction": "in", "type": "file"},
                {"id": "disputeSubmission", "direction": "in", "type": "object"}]}}
    inputs, _ = effects.build_inputs(flow, "reject")
    sub = inputs["disputeSubmission"]
    for read in (sub["customer"]["accountNumber"], sub["accountNumber"], sub["account"]):
        assert read == "ACCT-98201-NE"
    for lines in (sub["dispute"]["disputedLineItems"], sub["disputedLines"], sub["lineItems"], sub["lines"]):
        assert (lines[0]["lineNumber"], lines[0]["qty"], lines[0]["rate"], lines[0]["total"]) == (5, 14, 185, 2590)
    assert sub["invoice"]["number"] == sub["invoiceNumber"] == sub["invoiceNo"]


@pytest.mark.parametrize("path,value", [
    ("invoice", "MCS-2026-04903"),
    ("customer", "ACCT-71044-AT"),
])
def test_a_bare_string_read_of_invoice_or_customer_gets_the_scalar(effects, path, value):
    flow = {"nodes": [{"id": "s", "type": "core.action.script",
                       "inputs": {"script": f"return $vars.sub.{path};"}}],
            "variables": {"globals": [
                {"id": "pdf", "direction": "in", "type": "file"},
                {"id": "sub", "direction": "in", "type": "object"}]}}
    inputs, _ = effects.build_inputs(flow, "overcharge")
    assert str(inputs["sub"][path]).strip().upper() == value


@pytest.mark.parametrize("path", ["customerId", "customerNumber", "customerNo", "customerCode", "customerRef", "customerIdNumber"])
def test_a_customer_id_read_gets_the_account_number(effects, path):
    flow = {"nodes": [{"id": "s", "type": "core.action.script",
                       "inputs": {"script": f"return $vars.sub.{path};"}}],
            "variables": {"globals": [
                {"id": "pdf", "direction": "in", "type": "file"},
                {"id": "sub", "direction": "in", "type": "object"}]}}
    inputs, _ = effects.build_inputs(flow, "overcharge")
    assert inputs["sub"].get(path) == "ACCT-71044-AT"


@pytest.mark.parametrize("path", ["customerStatement", "customerName", "invoiceDate", "customerNote", "customerRefund", "customerNumberOfDisputes"])
def test_a_longer_field_keeps_its_submission_value(effects, path):
    flow = {"nodes": [{"id": "s", "type": "core.action.script",
                       "inputs": {"script": f"return $vars.sub.{path};"}}],
            "variables": {"globals": [
                {"id": "pdf", "direction": "in", "type": "file"},
                {"id": "sub", "direction": "in", "type": "object"}]}}
    inputs, _ = effects.build_inputs(flow, "overcharge")
    assert "ACCT-71044-AT" not in str(inputs["sub"].get(path))
    assert "MCS-2026-04903" not in str(inputs["sub"].get(path)).upper()


def test_a_submission_spread_over_separate_inputs_is_mapped(effects):
    flow = {"nodes": [], "variables": {"globals": [
        {"id": "pdf", "direction": "in", "type": "file"},
        {"id": "customerAccount", "direction": "in", "type": "string"},
        {"id": "invoiceRef", "direction": "in", "type": "string"},
        {"id": "disputedLines", "direction": "in", "type": "array"}]}}
    inputs, attachments = effects.build_inputs(flow, "overcharge")
    assert inputs["customerAccount"] == "ACCT-71044-AT"
    assert inputs["invoiceRef"].strip().upper() == "MCS-2026-04903"
    assert inputs["disputedLines"][0]["lineNumber"] == 2 and attachments == {"pdf": effects.invoice_pdf("overcharge")}


def test_a_flow_without_a_file_input_names_what_could_not_be_mapped(effects):
    flow = {"nodes": [], "variables": {"globals": [{"id": "submission", "direction": "in", "type": "object"}]}}
    with pytest.raises(SystemExit) as exc:
        effects.build_inputs(flow, "overcharge")
    assert "could not map the invoice PDF (a file input) onto inputs ['submission']" in str(exc.value)


def test_every_case_has_its_invoice_pdf(effects):
    for case in effects.CASES:
        assert os.path.isfile(effects.invoice_pdf(case))


def test_overcharge_passes_when_posted_and_the_results_are_right(effects, flow):
    effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED}))


def test_overcharge_accepts_credit_as_the_recommended_action(effects, flow):
    effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED, "action": "credit"}))


@pytest.mark.parametrize("field,wrong,message", [
    ("outcome", "approved", "decision 'Approved'"),
    ("action", "auto_resolve", "recommended action"),
    ("creditUsd", 1610, "credit amount 4950"),
    ("why", "We looked at it and the rate was too high, so we credited it.", "names an SOP rule"),
    ("draft", "We reviewed invoice MCS-2026-04903 and issued a credit.", "plain-text email"),
    ("draft", {"subject": "MCS-2026-04903", "body": DRAFT}, "plain-text email"),
])
def test_overcharge_fails_on_a_wrong_result(effects, flow, field, wrong, message):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED, field: wrong}))
    assert message in str(exc.value)


def test_overcharge_accepts_an_email_without_a_greeting_and_with_a_long_closing(effects, flow):
    draft = ("Thank you for contacting us about MCS-2026-04903.\nWe approved a credit of 4,950 for the overcharge.\n"
             "Please reply to this email if you have any further questions.")
    effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED, "draft": draft}))


def test_overcharge_accepts_an_email_that_names_the_sop_rule_when_it_is_the_only_letter(effects, flow):
    draft = "Dear customer,\n\nPer SOP §5.4 we credited 4,950 on MCS-2026-04903.\n\nBilling"
    why = "The billed rate exceeds the contract by $55 per hour."
    effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED, "draft": draft, "why": "Per SOP §5.4 the " + why}))


def test_overcharge_explanation_may_cite_the_invoice_and_credit(effects, flow):
    why = "Credit of 4,950 on MCS-2026-04903 approved under SOP §5.4"
    effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED, "why": why}))


def test_overcharge_fails_when_only_the_explanation_cites_the_invoice_and_credit(effects, flow):
    why = "Credit of 4,950 on MCS-2026-04903 approved under SOP §5.4"
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(ALL_NODES, {**POSTED, **APPROVED, "why": why, "draft": "Done."}))
    assert "plain-text email" in str(exc.value)


def test_overcharge_fails_when_the_posting_reply_is_for_the_uncleaned_number(effects, flow):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(ALL_NODES, {
            "financialpostingfunction12.output": {"result": "Credit memo posted. Invoice: ' mcs-2026-04903  '."},
            **APPROVED}))
    assert "reply does not cite" in str(exc.value)


def test_overcharge_fails_when_posting_did_not_run(effects, flow):
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(REJECT_PATH, APPROVED))
    assert "FinancialPostingFunction" in str(exc.value)


def test_overcharge_fails_when_the_ixp_extraction_did_not_complete(effects, flow):
    executed = [n for n in ALL_NODES if n != "invoiceExtraction"]
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(executed, {**POSTED, **APPROVED}))
    assert "IxP extraction did not complete" in str(exc.value)


def test_overcharge_fails_when_the_writer_after_posting_did_not_complete(effects, flow):
    executed = [n for n in ALL_NODES if n != "autonomousAgent3"]
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(executed, {**POSTED, **APPROVED}))
    assert "writer agent after posting did not complete" in str(exc.value)


@pytest.mark.parametrize("skipped,entity", [
    ("queryEntityRecords1", "BillingDisputeCRM"),
    ("queryEntityRecords2", "BillingDisputeERP"),
])
def test_overcharge_fails_when_one_of_the_two_lookups_did_not_complete(effects, flow, skipped, entity):
    executed = [n for n in ALL_NODES if n != skipped]
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(flow, _payload(executed, {**POSTED, **APPROVED}))
    assert f"{entity} lookup did not complete" in str(exc.value)


def test_overcharge_fails_when_both_lookups_read_the_same_entity(effects, flow):
    twin = json.loads(json.dumps(flow).replace("BillingDisputeCRM", "BillingDisputeERP"))
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(twin, _payload(ALL_NODES, {**POSTED, **APPROVED}))
    assert "no read of BillingDisputeCRM" in str(exc.value)


def _with_decoy_api_workflow(flow):
    flow = copy.deepcopy(flow)
    flow["nodes"].append({"id": "decoyApi", "type": "uipath.core.api-workflow.00000000-0000-0000-0000-000000000000"})
    return flow


def test_overcharge_requires_financial_posting_function_not_any_api_workflow(effects, flow):
    executed = [n for n in ALL_NODES if n != "financialpostingfunction12"] + ["decoyApi"]
    with pytest.raises(SystemExit) as exc:
        effects.check_overcharge(_with_decoy_api_workflow(flow), _payload(executed, {**POSTED, **APPROVED}))
    assert "FinancialPostingFunction did not complete" in str(exc.value)


def test_reject_passes_when_another_api_workflow_runs_before_the_analyst(effects, flow):
    flow = _with_decoy_api_workflow(flow)
    effects.check_reject(flow, _payload(["decoyApi"] + REJECT_PATH, REJECTED))


def test_reject_fails_when_the_flow_has_no_posting_node(effects, flow):
    flow = copy.deepcopy(flow)
    flow["nodes"] = [n for n in flow["nodes"] if n["id"] != "financialpostingfunction12"]
    flow["definitions"] = [d for d in flow.get("definitions") or [] if "FinancialPostingFunction" not in json.dumps(d)]
    with pytest.raises(SystemExit) as exc:
        effects.check_reject(flow, _payload(REJECT_PATH, REJECTED))
    assert "FinancialPostingFunction" in str(exc.value)


def test_reject_passes_on_the_rejection_path(effects, flow):
    effects.check_reject(flow, _payload(REJECT_PATH, REJECTED))


def test_reject_fails_when_it_was_posted(effects, flow):
    with pytest.raises(SystemExit) as exc:
        effects.check_reject(flow, _payload(ALL_NODES, REJECTED))
    assert "FinancialPostingFunction ran" in str(exc.value)


def test_reject_fails_without_the_no_email_text(effects, flow):
    with pytest.raises(SystemExit) as exc:
        effects.check_reject(flow, _payload(REJECT_PATH, {**REJECTED, "draft": ""}))
    assert "No resolution email drafted" in str(exc.value)


@pytest.mark.parametrize("skipped,message", [
    (["queryEntityRecords2"], "BillingDisputeERP lookup did not complete"),
    (["autonomousAgent1"], "analyst agent did not complete"),
    (["invoiceExtraction", "dataTransform", "queryEntityRecords1", "queryEntityRecords2", "merge1",
      "discrepancyScript", "autonomousAgent1"], "BillingDisputeERP lookup did not complete"),
])
def test_reject_fails_when_the_rejection_skipped_the_lookup_or_the_analyst(effects, flow, skipped, message):
    with pytest.raises(SystemExit) as exc:
        effects.check_reject(flow, _payload([n for n in REJECT_PATH if n not in skipped], REJECTED))
    assert message in str(exc.value)


@pytest.mark.parametrize("why", [
    "Per the SOP there is no variance on line 5, so we reject the dispute and credit nothing.",
    "The billed rate matches the contract, so the SOP says this dispute is rejected.",
])
def test_reject_fails_when_the_explanation_only_mentions_the_sop(effects, flow, why):
    with pytest.raises(SystemExit) as exc:
        effects.check_reject(flow, _payload(REJECT_PATH, {**REJECTED, "why": why}))
    assert "names an SOP rule" in str(exc.value)


@pytest.mark.parametrize("why", [
    "Under SOP 5.4 line 5 was billed at the contracted $185, so there is no variance to credit.",
    "Per the Incorrect rate rule line 5 matches its contracted $185, so there is nothing to credit.",
    "Section 7 sends a dispute without a variance to reject, and line 5 matches its contract.",
])
def test_reject_accepts_a_rule_named_by_number_or_title(effects, flow, why):
    effects.check_reject(flow, _payload(REJECT_PATH, {**REJECTED, "why": why}))


def test_reject_disputes_a_line_billed_at_its_contracted_rate(effects):
    line = effects.line_item("reject")
    assert (line["lineNumber"], line["quantity"], line["unitPrice"], line["amount"]) == (5, 14, 185, 2590)


def _with_tenant_agent_writer(flow):
    """The writer as an existing tenant agent, as a Studio Web build did."""
    flow = copy.deepcopy(flow)
    for n in flow["nodes"]:
        if n["id"] == "autonomousAgent3":
            n["type"] = "uipath.core.agent.31cfa36d-dbc7-4be3-bbf7-000000000000"
    return flow


def test_structure_accepts_an_existing_tenant_agent_as_the_writer():
    _topology(_with_tenant_agent_writer(_flow()))


def test_reject_catches_a_tenant_agent_writer_that_ran(effects, flow):
    with pytest.raises(SystemExit) as exc:
        effects.check_reject(_with_tenant_agent_writer(flow), _payload(REJECT_PATH + ["autonomousAgent3"], REJECTED))
    assert "writer agent ran" in str(exc.value)


@pytest.mark.parametrize("case, retries", [("overcharge", 1), ("reject", None)])
def test_only_the_posting_case_debugs_once(effects, flow, monkeypatch, case, retries):
    seen = {}
    monkeypatch.setattr(effects, "_load_flow", lambda glob: flow)
    monkeypatch.setattr(effects, "run_debug", lambda **kw: seen.update(kw) or _payload(REJECT_PATH, REJECTED))
    monkeypatch.setattr(effects, "check_overcharge", lambda f, p: None)
    monkeypatch.setattr("sys.argv", ["check", case])
    effects.main()
    assert seen.get("retries") == retries
